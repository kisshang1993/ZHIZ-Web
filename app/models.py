###########################
#
# Name: HLD PIC Models
# Author: HLD
# Date: 2019-07-10
#
###########################

from flask import current_app as app
from .exts import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash,check_password_hash
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer, SignatureExpired, BadSignature
import datetime

class User(UserMixin, db.Model):
    """用户表"""
        
    id = db.Column(db.Integer, primary_key=True, index=True)
    uid = db.Column(db.String(10), unique=True, index=True) #UID
    username = db.Column(db.String(20),  unique=True, index=True) #账户名
    email = db.Column(db.String(50),  unique=True) #电子邮箱
    password = db.Column(db.String(256)) #密码sha256加密
    nickname = db.Column(db.String(30), unique=True) #昵称
    avatar = db.Column(db.String(50)) #头像
    level = db.Column(db.Integer, default=1) #等级
    score = db.Column(db.Integer, default=0) #积分
    status = db.Column(db.String(10), default='normal') #状态
    date = db.Column(db.DateTime, default=datetime.datetime.now()) #注册日期

    #添加积分
    def add_score(self, score):
        self.score = self.score + score
        db.session.commit()

	#验证密码hash
    def verify_password(self, password):
        return check_password_hash(self.password, password)

    #验证管理员
    def is_admin(self):
        return (self.level >= app.config['ACCESS_BACKEND_LEVEL'])

    # 获取token，有效时间10min
    def generate_auth_token(self, expiration = 3600):
        s = Serializer(app.config['SECRET_KEY'], expires_in = expiration)
        return s.dumps({ 'id': self.id }).decode(encoding='utf-8')

    # 解析token，确认登录的用户身份
    @staticmethod
    def verify_auth_token(token):
        if token == None:
            return None
        s = Serializer(app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except SignatureExpired:
            return None # valid token, but expired
        except BadSignature:
            return None # invalid token
        user = User.query.get(data['id'])
        return user
    
    # 转字典
    def to_dict(self):
        return {
            'id': self.id,
            'uid': self.uid,
            'username': self.username,
            'email': self.email,
            'nickname': self.nickname,
            'avatar': self.avatar,
            'level': self.level,
            'score': self.score,
            'status': self.status,
            'date': self.date.strftime("%Y-%m-%d %H:%M:%S")
        }


#文章标签关系映射中间表
article_tag = db.Table('article_tag',
                       db.Column('article_id', db.Integer, db.ForeignKey('article.id'), primary_key=True),
                       db.Column('tag_id', db.Integer, db.ForeignKey('tag.id'), primary_key=True)
                       )

class Article(db.Model):
    """文章"""
    
    id = db.Column(db.Integer, primary_key=True, index=True)
    title = db.Column(db.String(50), index=True) #标题
    subtitle = db.Column(db.String(150)) #简略
    content = db.Column(db.Text()) #正文
    hide = db.Column(db.Text(), default='') #隐藏域
    hide_level = db.Column(db.Integer, default=0) #隐藏域需要权限
    level = db.Column(db.Integer, default=0) #文章需要权限
    perview = db.Column(db.String(450)) #预览图
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    author = db.relationship('User', backref='articles') #作者
    date = db.Column(db.DateTime, default=datetime.datetime.now()) #日期
    tags = db.relationship('Tag', secondary=article_tag, backref='articles')
    status = db.Column(db.String(20), default='normal') #状态
    like = db.Column(db.Integer, default=0) #点赞数
    visited = db.Column(db.Integer, default=0) #阅读量

    # 转字典
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'author': self.author.nickname,
            'author_id': self.author.id,
            'date': self.date.strftime("%Y-%m-%d %H:%M:%S"),
            'like': self.like,
            'tags': len(self.tags),
            'status': self.status,
            'visited': self.visited,
            'has_hide': self.hide != '',
            'hide_level': self.hide_level
        }

    # 详情
    def detail(self):
        perview = []
        split_perview = self.perview.split(',')
        for sp in split_perview:
             perview.append({'path': sp})

        tags = []
        for t in self.tags:
            tags.append({
                'id': t.id,
                'name': t.name
            })

        return {
            'id': self.id,
            'title': self.title,
            'subtitle': self.subtitle,
            'content': self.content,
            'hide': self.hide,
            'hide_level': self.hide_level,
            'level': self.level,
            'perview': perview,
            'tags': tags
        }



class Tag(db.Model):
    """标签"""

    id = db.Column(db.Integer, primary_key=True, index=True)
    article_id = db.Column(db.Integer, db.ForeignKey('article.id'))
    name = db.Column(db.String(20), index=True) #标签名

    # 转字典
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name
        }


class Comment(db.Model):
    """评论"""

    id = db.Column(db.Integer, primary_key=True, index=True)
    article_id = db.Column(db.Integer) #文章ID
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    sender = db.relationship('User', backref='comments') #登录用户
    guest_name = db.Column(db.String(20), default='') #临时用户姓名
    guest_email = db.Column(db.String(50), default='') #临时用户邮箱
    content = db.Column(db.Text()) #正文
    reply_id = db.Column(db.Integer) #引用的回复
    like = db.Column(db.Integer, default=0) #点赞数
    date = db.Column(db.DateTime, default=datetime.datetime.now()) #日期
    status = db.Column(db.String(10), default='inspect') #状态

    #是否匿名者
    def is_anonymous(self):
        return not self.sender

    #获取发送者ID
    def get_sender_id(self):
        if self.is_anonymous():
            return None
        else:
            return self.sender.id

    #获取发送者名称
    def get_sender_name(self):
        if self.is_anonymous():
            return self.guest_name
        else:
            return self.sender.nickname or self.sender.username


    #获取发送者邮箱
    def get_sender_email(self):
        if self.is_anonymous():
            return self.guest_email
        else:
            return self.sender.email
   
    #获取发送者等级
    def get_sender_level(self):
        if self.is_anonymous():
            return 0
        else:
            return self.sender.level
        

    # 转字典
    def to_dict(self):
        return {
            'id': self.id,
            'article_id': self.article_id,
            'sender_id': self.get_sender_id(),
            'sender_name': self.get_sender_name(),
            'sender_level': self.get_sender_level(),
            'sender_email': self.get_sender_email(),
            'content': self.content,
            'reply_id': self.reply_id,
            'like': self.like,
            'date': self.date.strftime("%Y-%m-%d %H:%M:%S"),
            'status': self.status
        }



class Favorite(db.Model):
    """收藏"""

    id = db.Column(db.Integer, primary_key=True, index=True)
    own_id = db.Column(db.Integer) #收藏者
    article_id = db.Column(db.Integer) #文章ID
    date = db.Column(db.DateTime, default=datetime.datetime.now()) #日期


class Notice(db.Model):
    """通知"""

    id = db.Column(db.Integer, primary_key=True, index=True)
    sender_id = db.Column(db.Integer) #发送者
    guest_name = db.Column(db.String(20), default='') #临时用户姓名
    receive_id = db.Column(db.Integer) #接受者
    article_id = db.Column(db.Integer) #文章ID
    msg = db.Column(db.String(140)) #通知主体
    link = db.Column(db.String(140)) #跳转页面
    status = db.Column(db.String(10), default='unread') #状态
    date = db.Column(db.DateTime, default=datetime.datetime.now()) #日期


class InvitationCode(db.Model):
    """邀请码"""

    id = db.Column(db.Integer, primary_key=True, index=True)
    code = db.Column(db.String(20), default='') #邀请码
    level = db.Column(db.Integer, default=1) #邀请码权限
    status = status = db.Column(db.String(10), default='') #状态

    # 转字典
    def to_dict(self):
        return {
            'code': self.code,
            'level': self.level,
            'status': self.status
        }
