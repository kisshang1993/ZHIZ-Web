###########################
#
# Name: HLD PIC View
# Author: HLD
# Date: 2019-07-03
#
###########################

from flask import Blueprint
from flask import current_app as app
from .exts import db
from .exts import red
from app import limiter
from app import login_manager
from .utils import send_mail
from .utils import atomic
from flask import request
from flask import render_template
from flask import jsonify
from flask import current_app
from flask import abort
from flask import redirect
from flask import url_for
from flask_login import login_user, logout_user, login_required, \
    current_user
from jinja2.exceptions import TemplateNotFound
from werkzeug.security import generate_password_hash,check_password_hash
from app.models import User, Article, Tag, Comment, Favorite, Notice, InvitationCode
import random
import base64
import json
import os
import uuid

basic = Blueprint('basic',__name__)

@basic.route('/query/', methods=['GET'])
@basic.route('/', methods=['GET'])
def index():
    """ 主页 """

    return render_template('index.html', articles=get_article(), sidebar_data=sidebar_data())


@basic.route('/article-load-more/', methods=['GET'])
def load_more():
    """ 加载更多文章 """
    
    return render_template('article__templete.html', articles=get_article(), sidebar_data=sidebar_data())


def get_article():
    """ 过滤文章 """
    
    #分页
    page = request.args.get('page') or 1
    keywords = request.args.get('keywords')
    tag = request.args.get('tag')
    
    #标签过滤
    if tag:
        has_tag_articles = Tag.query.filter(Tag.name==tag).first()
        if has_tag_articles:
            origin_articles = Article.query.with_parent(has_tag_articles)
        else:
            origin_articles = Article.query.filter(Article.id==0)

    #关键字查询
    elif keywords:
        origin_articles = Article.query.filter(Article.title.like('%'+keywords+'%'))

    else:
        origin_articles = Article.query

    articles = origin_articles.filter(Article.status=='normal').order_by(Article.id.desc()).paginate(int(page), app.config['PAGINATION_ARTICLE'], False)

    if keywords: articles.keywords = keywords
    if tag: articles.tag = tag

    return articles

@basic.route('/user/profile/', methods=['GET'])
@login_required
def user_info():
    """ 用户详情 """

    return render_template('user_info.html')
                        

@basic.route('/article/<int:id>/', methods=['GET'])
def article_detail(id):
    """ 文章详情 """

    article_this = Article.query.get_or_404(id)
    if article_this.status == 'deleted':
        return abort(404)

    article_this.visited = article_this.visited + 1
    prev_id = id-1
    article_prev = Article.query.get(prev_id)
    while (article_prev and article_prev.status == 'deleted'):
        prev_id = prev_id - 1
        article_prev = Article.query.get(prev_id)

    next_id = id + 1
    article_next = Article.query.get(next_id)
    while (article_next and article_next.status == 'deleted'):
        next_id = next_id + 1
        article_next = Article.query.get(next_id)

    article = {
        'this': article_this,
        'prev': article_prev,
        'next': article_next
    }

    comments = Comment.query.filter_by(article_id=id, status='allowed')
    comment = {
        'all': comments.all(),
        'count': comments.count()
    }
    db.session.commit()
    return render_template('article-detail.html', article=article, comment=comment, sidebar_data=sidebar_data())

         
def sidebar_data():
    """ 侧边栏数据 """

    hot_articles = Article.query.filter(Article.status=='normal').order_by(Article.visited.desc()).limit(8)
    hot_tags = Tag.query.limit(20)
    hot_comments = Comment.query.filter(Comment.status=='allowed').order_by(Comment.date.desc()).limit(6)
    sidebar_data = {
        'articles': hot_articles,
        'tags': hot_tags,
        'comments': hot_comments
    }
    if current_user.get_id():
        sidebar_data['notice'] = Notice.query.filter(Notice.receive_id==current_user.id,Notice.status=='unread').count()


    return sidebar_data


@basic.route('/comment/submit/', methods=['POST'])
@limiter.limit('5/minute')
def comment_submit():
    """ 提交评论 """

    context = {'code': 400}

    article_id = request.form.get('article_id')
    guest_name = request.form.get('guest_name')
    guest_email = request.form.get('guest_email')
    comment_content = request.form.get('comment_content')
    reply_id = request.form.get('reply_id')
    
    if current_user.is_anonymous:
        if len(guest_name) < 2 or len(guest_name) > 8:
            context['msg'] = '请输入2~8个字之间的昵称'
            return jsonify(context)

    try:
        comment = Comment()
        comment.article_id = article_id
        comment.guest_name = guest_name
        comment.guest_email = guest_email
        comment.content = comment_content
        comment.reply_id = reply_id
        
        if current_user.get_id():
            comment.sender = current_user
        
        db.session.add(comment)
        db.session.commit()
        context['code'] = 200

    except Exception as e:
        print(e)
        context['msg'] = '某个值超出了限制'

    return jsonify(context)


@basic.route('/user/login/', methods=['POST'])
def user_login():
    """ 用户登录 """
    
    context = {'code': 400}
    
    username = request.form.get('login_username')
    passwd = request.form.get('login_passwd')

    user = User.query.filter(User.username == username).first()
    if user and user.verify_password(passwd):
        login_user(user, remember=True)
        context['code'] = 200

    else:
        context['msg'] = '账号或密码错误'

    return jsonify(context)


@basic.route('/user/logout/', methods=['POST'])
@login_required
def user_logout():
    """ 用户注销 """

    context = {'code': 500}
    try:
        logout_user()
        context['code'] = 200

    except Exception as e:
        print(e)

    return jsonify(context)

@basic.route('/user/set-nickname/', methods=['POST'])
@login_required
def user_set_nickname():
    """ 设置昵称 """

    context = {'code': 400}
    try:
        nickname = request.form.get('nickname')
        if nickname == None or len(nickname) < 2 or len(nickname) > 8:
            context['msg'] = '昵称为2~8位'
            return jsonify(context)

        user = User.query.filter(User.nickname==nickname).first()
        if user:
            context['msg'] = '昵称已被使用'
        
        else:
            current_user.nickname = nickname
            db.session.add(current_user)
            db.session.commit()
            context['code'] = 200

    except Exception as e:
        print(e)
        context['code'] = 500

    return jsonify(context)


@basic.route('/user/set-avatar/', methods=['POST'])
@login_required
def user_set_avatar():
    """ 设置头像 """

    context = {'code': 400}
    # if len(request.files) > 0:
    #     upload_avatar = request.files['avatar']
    #     print(upload_avatar.content_length)
    #     upload_avatar.save('avatar.jpg')

    avatar_base64 = request.form.get('avatar_base64')
    #avatar_uuid = uuid.uuid3(uuid.NAMESPACE_URL, current_user.uid).hex
    avatar_uuid = uuid.uuid4().hex
    root_dir = os.path.dirname(app.instance_path)
    save_path = os.path.join(root_dir, 'app/static/upload/avatar', avatar_uuid+'.jpg')
    try:
        with open(save_path, 'wb') as fw:
            fw.write(base64.b64decode(avatar_base64[23:]))

        current_user.avatar = avatar_uuid
        db.session.commit()

        context['code'] = 200

    except Exception as e:
        print(e)
        context['msg'] = '传输的base64格式有误'

    return jsonify(context)



@basic.route('/user/register/', methods=['POST'])
def user_register():
    """ 用户注册 """

    context = {'code': 400}
    try:
        invitation_code = request.form.get('register_Invitation_code')
        email = request.form.get('register_email')
        username = request.form.get('register_username')
        passwd = request.form.get('register_passwd')

        if invitation_code == '' or email == '' or\
         username == '' or passwd == '':
            context['msg'] = '请填写所有字段'
            return jsonify(context)
        
        #检查邀请码
        ic = InvitationCode.query.filter(InvitationCode.code==invitation_code).first()
        if ic and ic.status is '':
            with atomic(db):
                ic.status = 'used'
                user = User()
                user.uid = str(10015130 + User.query.count())
                user.username = username
                user.email = email
                user.password = generate_password_hash(passwd)
                user.level = ic.level

                db.session.add(user)
                db.session.commit()
                login_user(user)
                context['code'] = 200
        
        else:
            context['msg'] = '邀请码无效'
    
    except Exception as e:
        print(e)
        context['msg'] = '提交的某个字段已经被占用'

    return jsonify(context)


@basic.route('/user/check/', methods=['GET'])
def check_value():
    """ 检查值 """
    
    context = {'code': 400}

    check_username = request.args.get('username')
    check_email = request.args.get('email')

    if check_username:
        user = User.query.filter(User.username==check_username).first()
        if not user: context['code'] = 200

    if check_email:
        email = User.query.filter(User.email==check_email).first()
        if not email: context['code'] = 200
    
    return jsonify(context)
    

    
@basic.route('/statistics/', methods=['POST'])
@limiter.limit('20/minute')
def statistics():
    """ 统计信息 """

    context = {'code': 400}
    article_id = request.form.get('article_id')
    comment_id = request.form.get('comment_id')
    statistics_type = request.form.get('type')
    if statistics_type == 'like':
        if article_id and article_id != 'undefined':
            #文章点赞
            try:
                article = Article.query.get(article_id)
                article.like = article.like + 1
                db.session.commit()
                context['code'] = 200

            except Exception as e:
                print(e)
                context['msg'] = '文章不存在'

        elif comment_id and comment_id != 'undefined':
            #评论点赞
            try:
                comment = Comment.query.get(comment_id)
                comment.like = comment.like + 1
                db.session.commit()
                context['code'] = 200

            except Exception as e:
                print(e)
                context['msg'] = '评论不存在'




    return jsonify(context)


@basic.route('/favorite/', methods=['GET', 'POST'])
def favorite_control():
    """ 收藏管理 """

    if current_user.is_anonymous:
        return jsonify({'code': 401})

    if request.method == 'GET':
        page = request.args.get('page') or 1
        pagination = Favorite.query.filter(Favorite.own_id==current_user.id).order_by(Favorite.date.desc()).paginate(int(page), app.config['PAGINATION_FAVORITE'], False)
        for p in pagination.items:
            p.title = Article.query.get(p.article_id).title
    
        return render_template('user_info_favorite_list__templete.html', pagination=pagination)

    elif request.method == 'POST':
        context = {'code': 400}
        command = request.form.get('command')
        article_id = request.form.get('article_id')
        favorite = Favorite.query.filter(Favorite.own_id==current_user.id,Favorite.article_id==article_id).first()
        if command == 'add':
            if not favorite:
                db.session.add(Favorite(
                    own_id=current_user.id,
                    article_id=article_id
                ))
                db.session.commit()
                context['code'] = 200

            else:
                context['msg'] = '文章已经收藏'
        
        if command == 'remove':
            if favorite:
                db.session.delete(favorite)
                db.session.commit()
                context['code'] = 200

            else:
                context['msg'] = '文章不存在'

        return jsonify(context)
            
            

@basic.route('/notice/', methods=['GET', 'POST'])
@login_required
def notice_control(body=None):
    """ 消息中心 """

    if request.method == 'GET' and body == None:
        page = request.args.get('page') or 1
        pagination = Notice.query.filter(Notice.receive_id==current_user.id).order_by(Notice.date.desc()).paginate(int(page), app.config['PAGINATION_NOTICE'], False)

        return render_template('user_info_notice_list__templete.html', pagination=pagination)
    
    elif request.method == 'POST' and body == None:
        unread_id = request.form.get('id')
        if unread_id:
            unread_notice = Notice.query.get(unread_id)
            if unread_notice:
                unread_notice.status = 'read'
                db.session.add(unread_notice)

        else:
            Notice.query.filter(Notice.receive_id==current_user.id,Notice.status=='unread').update({'status': 'read'})
        
        db.session.commit()
        
        return jsonify({'code': 200})

    elif body:
        try:
            notice = Notice()
            notice.sender_id = body.get('sender_id')
            notice.guest_name = body.get('guest_name')
            notice.receive_id = body.get('receive_id')
            notice.article_id = body.get('article_id')
            notice.msg = body.get('msg')
            notice.link = body.get('link')
            db.session.add(notice)
            db.session.commit()
            return True

        except Exception as e:
            print(e)
            return False
        

@basic.route('/user/forget-pwd/', methods=['GET', 'POST'])
@basic.route('/user/forget-pwd/<token_base64>/', methods=['GET', 'POST'])
def forget_pwd(token_base64=None):
    """忘记密码"""

    if request.method == 'GET':
        type = 'send'
        if token_base64:
            try:
                token = str(base64.b64decode(token_base64), 'utf-8')
                user = User.verify_auth_token(token)
                if user:
                    type = 'reset'
                else:
                    type = 'expired'

            except base64.binascii.Error:
                type = 'invalid'

        return render_template('forget-pwd.html', type=type)
    
    elif request.method == 'POST':
        context = {'code': 400}
        #验证通过重置密码
        if token_base64:
            try:
                pwd = request.form.get('pwd')
                token = str(base64.b64decode(token_base64), 'utf-8')
                user = User.verify_auth_token(token)
                if user and pwd:
                    user.password = generate_password_hash(pwd)
                    db.session.commit()
                    context['code'] = 200

                else:
                    context['msg'] = '链接已过期，请重新发送验证邮件'

            except base64.binascii.Error:
                context['msg'] = '身份验证失败，请勿修改TOKEN'
        
        return jsonify(context)


@basic.route('/user/verify-email/', methods=['POST'])
@limiter.limit('2/minute')
def send_reset_mail():
    """发送重置密码邮件"""

    context = {'code': 400}
    email = request.form.get('email')
    user = User.query.filter(User.email==email).first()
    if user:
        token = user.generate_auth_token(3600)
        token_base64 = base64.b64encode(token.encode('utf-8'))
        dom = render_template('mails/forget_password.html',
                username = user.username,
                link = '%s/user/forget-pwd/%s/' % (app.config['HOST'], str(token_base64, 'utf-8'))
            )
        body = {
            'subject': '重置密码',
            'recipients': [email],
            'html': dom
        }
        send_mail(body)

    context['code'] = 200
    return jsonify(context)


