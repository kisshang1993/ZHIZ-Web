###########################
#
# Name: HLD PIC View
# Author: HLD
# Date: 2019-07-16
#
###########################

from flask import Blueprint
from .exts import db
from app import mail
from app import login_manager
from app.models import User, Article, Tag, Comment, Favorite, Notice, InvitationCode
from .utils import send_mail
from .utils import atomic
from flask import request
from flask import Response
from flask import render_template
from flask import make_response
from flask import jsonify
from flask import abort
from flask import redirect
from flask import url_for
from flask import g
from .basic import notice_control
from jinja2.exceptions import TemplateNotFound
from werkzeug.security import generate_password_hash,check_password_hash
from flask import current_app as app
import tempfile
from flask_httpauth import HTTPTokenAuth
from functools import wraps
from flask_cors import CORS
from bs4 import BeautifulSoup
from lxml import html
import datetime
import random
import string
import base64
import shutil
import json
import os
import uuid
import re

admin = Blueprint('admin',__name__)
auth = HTTPTokenAuth(scheme='token')
CORS(admin, supports_credentials=True)


@auth.verify_token
def verify_admin(token):
    """ 管理员验证token """
    token = request.headers.get('token', None)
    user = User.verify_auth_token(token)
    if not user or not user.is_admin():
        return False
    g.user = user
    return True

@auth.error_handler
def auth_failed():
    """ 验证失败 """
    return jsonify(code=403), 403


@admin.route('/login/', methods=['POST'])
def admin_login():
    """ 管理员登录 """
    
    context = {'code': 400}
    
    username = request.form.get('login_username')
    passwd = request.form.get('login_passwd')

    user = User.query.filter(User.username == username).first()
    if user and user.verify_password(passwd) and user.level >= app.config['ACCESS_BACKEND_LEVEL']:
        context['code'] = 200
        context['token'] = user.generate_auth_token(expiration=36000)

    else:
        context['msg'] = '账号或密码错误'

    return jsonify(context)


@admin.route('/user-list/', methods=['GET'])
@auth.login_required
def user_list():
    """ 获取用户列表 """

    context = {'code': 400}
    try:
        page = request.args.get('page', 1)
        page_size = request.args.get('page_size', 15)
        users_query = User.query
        users_paginate = users_query.paginate(int(page), int(page_size), False)
        data  = {
            'users': [],
            'total': users_query.count()
        }
        for u in users_paginate.items:
            data['users'].append(u.to_dict())
        
        context['data'] = data
        context['code'] = 200


    except Exception as e:
        print(e)
        pass

    return jsonify(context)


@admin.route('/user-detail/', methods=['GET', 'POST'])
@auth.login_required
def user_detail():
    """获取用户详情"""

    context = {'code': 400}

    if request.method == 'GET':
        id = request.args.get('id')
        user = User.query.get(id)
        if user:
            context['data'] = user.to_dict()
            context['code'] = 200

        else:
            context['msg'] = '用户不存在'


    elif request.method == 'POST':
        pass
    
    return jsonify(context)


@admin.route('/articles-list/', methods=['GET'])
@auth.login_required
def articles_list():
    """ 获取文章列表 """

    context = {'code': 400}
    try:
        page = request.args.get('page', 1)
        page_size = request.args.get('page_size', 15)
        status = request.args.get('status')
        queryset = Article.query
        if status: queryset = queryset.filter(Article.status==status)
        paginate = queryset.order_by(Article.id.desc()).paginate(int(page), int(page_size), False)
        data  = {
            'list': [],
            'total': queryset.count()
        }
        for item in paginate.items:
            data['list'].append(item.to_dict())
        
        context['data'] = data
        context['code'] = 200


    except Exception as e:
        print(e)
        pass

    return jsonify(context)


@admin.route('/tags-list/', methods=['GET', 'POST'])
@auth.login_required
def tags_list():
    """ 获取标签列表 """

    context = {'code': 400}
    if request.method == 'GET':
        try:
            tags = Tag.query.all()
            data = []
            for item in tags:
                data.append(item.to_dict())
            
            context['data'] = data
            context['code'] = 200

        except Exception as e:
            print(e)
            pass

    elif request.method == 'POST':
        tag_name = request.json.get('tag_name')
        if tag_name == '': return
        
        has_tag = Tag.query.filter(Tag.name==tag_name).first()
        if has_tag:
            context['msg'] = '标签已存在'

        else:
            tag = Tag(name=tag_name)
            db.session.add(tag)
            db.session.flush()
            db.session.commit()

            context['code'] = 200
            context['data'] = {
                'id': tag.id,
                'name': tag_name
            }


    return jsonify(context)


def allowed_file(filename):
    """检查文件名"""
    
    return '.' in filename and filename.rsplit('.', 1)[1] in ['jpg', 'jpeg', 'bmp', 'png', 'gif']

def random_file_name(filename):
    """随机文件名"""

    return '%s.%s' % (uuid.uuid4().hex, filename.split('.')[1])

@admin.route('/upload/', methods=['POST'])
@auth.login_required
def upload_file():
    """上传"""

    context = {'code': 400}
    file = request.files['file'] or request.files['upload']
    if file and allowed_file(file.filename):
        filename = random_file_name(file.filename)
        #temp_save_path = os.path.join(tempfile.gettempdir(), filename)
        save_path = os.path.join(app.root_path, 'static/upload/article', filename)
        file.save(save_path)
        context['code'] = 200
        context['data'] = os.path.join('/static/upload/article', filename)
    
    else:
        context['msg'] = '文件不合法'

    return jsonify(context)


def gen_rnd_filename():
    """生成随机文件名"""

    filename_prefix = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
    return '%s%s' % (filename_prefix, str(random.randrange(1000, 10000)))


@admin.route('/ckupload/', methods=['POST'])
@auth.login_required
def ckupload():
    """CKEditor文件上传"""

    error = ''
    url = ''
    callback = request.form.get("CKEditorFuncNum")
    if request.method == 'POST' and 'upload' in request.files:
        fileobj = request.files['upload']
        fname, fext = os.path.splitext(fileobj.filename)
        rnd_name = '%s%s' % (gen_rnd_filename(), fext)
        filepath = os.path.join(app.static_folder, 'upload/article', rnd_name)
        """检查路径是否存在，不存在则创建"""
        dirname = os.path.dirname(filepath)
        if not os.path.exists(dirname):
            try:
                os.makedirs(dirname)
            except:
                error = '文件上传失败'
        elif not os.access(dirname, os.W_OK):
            error = '文件不可读'
        if not error:
            fileobj.save(filepath)
            url = url_for('static', filename='%s/%s' % ('upload/article', rnd_name))
    else:
        error = 'post error'

    res = '{"fileName":"%s","uploaded":1,"url":"%s"}'% (rnd_name, url)
    response = make_response(res)
    response.headers["Content-Type"] = "text/html"

    return response




@admin.route('/article-control/', methods=['GET', 'POST'])
@auth.login_required
def article_control():
    """文章处理"""

    context = {'code': 400}
    if request.method == 'GET':
        '''获取文章详情'''
        id = request.args.get('id')
        article = Article.query.get(id)
        if article:
            context['data'] = article.detail()
            context['code'] = 200

        else:
            context['msg'] = '无效的文章ID'


    elif request.method == 'POST':
        '''提交文章'''

        id = request.json.get('id')
        try:
            if id == 0: 
                #创建新文章
                article = Article()
            else:
                article = Article.query.get(id)
            
            if article:
                autofill = request.json.get('autofill')
                content = request.json.get('content')
                subtitle = request.json.get('subtitle')
                article.title = request.json.get('title')
                article.content = content
                article.hide = request.json.get('hide')
                article.hide_level = request.json.get('hide_level')
                article.level = request.json.get('level')
                article.author = g.user
                #预览图
                get_perview = request.json.get('perview')
                perview_list = [ p['path'] for p in get_perview if p['path'] ]
                # perview_save = []
                # for p in perview_list:
                #     #写入缓存文件
                #     if p.find(tempfile.gettempdir()) == 0:
                #         if os.path.exists(p):
                #             fpath, fname = os.path.split(p) 
                #             save_path = os.path.join(app.root_path, 'static/upload/article')
                #             shutil.move(p, save_path)
                #             perview_save.append('/static/upload/article/%s' % (fname))
                #         else:
                #             print(p, 'NOT EXIST')
                #     else:
                #         perview_save.append(p)

                # article.perview = ','.join(perview_save)
                
                #自动填充副标题
                if autofill and not subtitle:
                    cut_header = content[:150]
                    img_tag = cut_header.find('<img')
                    if img_tag > -1:
                        cut_header = cut_header[:img_tag]
                    pattern = re.compile(r'<[^>]+>', re.S)
                    clean_result = pattern.sub('', cut_header)
                    article.subtitle = clean_result

                else:    
                    article.subtitle = subtitle

                #自动填充略缩图
                if autofill and len(perview_list) < 3:
                    needs_count = 3 - len(perview_list)
                    pos = 0
                    while (needs_count > 0):
                        needs_count -= 1
                        img_s = content.find('src="', pos)
                        if img_s > -1:
                            img_s += 5
                            img_e = content.find('"', img_s)
                            if img_e > -1:
                                pos = img_e + 1
                                img_url = content[img_s:img_e]
                                perview_list.append(img_url)

                article.perview = ','.join(perview_list)


                #标签
                get_tags = request.json.get('tags')
                article.tags = []
                for t in get_tags:
                    tag = Tag.query.get(t['id'])
                    if tag:
                        article.tags.append(tag)
                
                if id == 0: db.session.add(article)
                db.session.commit()
                context['code'] = 200

            else:
                context['msg'] = '文章不存在'

        except Exception as e:
            context['msg'] = e


    return jsonify(context)
        




@admin.route('/article-update/', methods=['POST'])
@auth.login_required
def article_update():
    """文章状态更新"""

    context = {'code': 400}
    id = request.json.get('id')
    article = Article.query.get(id)
    if article:
        article.status = request.json.get('status')
        db.session.commit()
        context['code'] = 200

    else:
        context['msg'] = '文章不存在'

    return jsonify(context)


@admin.route('/comments-list/', methods=['GET', 'POST'])
@auth.login_required
def comments_list():
    """ 获取评论列表 """

    context = {'code': 400}

    if request.method == 'GET':
        """获取列表"""
        try:
            page = request.args.get('page', 1)
            page_size = request.args.get('page_size', 15)
            status = request.args.get('status')
            queryset = Comment.query
            if status: queryset = queryset.filter(Comment.status==status)
            paginate = queryset.order_by(Comment.date.desc()).paginate(int(page), int(page_size), False)
            data  = {
                'list': [],
                'total': queryset.count()
            }
            for item in paginate.items:
                data['list'].append(item.to_dict())
            
            context['data'] = data
            context['code'] = 200

        except Exception as e:
            print(e)
            pass
    
    elif request.method == 'POST':
        """更新状态"""
        id = request.json.get('id')
        status = request.json.get('status')
        comment = Comment.query.get(id)
        if comment:
            comment.status = status
            db.session.commit()

            if status == 'allowed' and comment.reply_id:
                '''通知'''
                r = Comment.query.get(comment.reply_id)
                if r:
                    if r.sender:
                        s = send_notice({
                            'guest_name': comment.get_sender_name(),
                            'sender_id': comment.get_sender_id(),
                            'receive_id': r.sender.id,
                            'article_id': comment.article_id,
                            'msg': '<span class="notice-name">%s</span>回复了你：<span class="notice-msg">%s</span>' % (comment.get_sender_name(), comment.content),
                            'link': '/article/%s/#comment_%s' % (comment.article_id, comment.id)
                        })
                        print('发送消息状态：', s)
                    
                    elif r.guest_email:
                        body = {
                            'subject': '有评论回复了你',
                            'recipients': [r.guest_email],
                            'html': render_template('mails/has_reply.html',
                                reply_sender = comment.get_sender_name(),
                                reply_content = comment.content,
                                link = '%s/article/%s/#comment_%s' % (app.config['HOST'], comment.article_id, comment.id)
                            )
                        }
                        send_mail(body)



            context['code'] = 200

        else:
            context['msg'] = '文章不存在'


    return jsonify(context)


def send_notice(body):
    """发送消息"""

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




@admin.route('/comment-reply/', methods=['GET'])
@auth.login_required
def comment_reply():
    """查看回复引用"""

    context = {'code': 400}

    reply_id = request.args.get('id')
    reply_list = []
    while reply_id:
        r = Comment.query.get(reply_id)
        if r:
            reply_list.append({
                'id': r.id,
                'sender_id': r.get_sender_id(),
                'name': r.get_sender_name(),
                'level': r.get_sender_level(),
                'text': r.content,
                'date': r.date.strftime("%Y-%m-%d %H:%M:%S")
            })
            reply_id = r.reply_id
        else:
            reply_id = None

    context['code'] = 200
    context['data'] = list(reversed(reply_list))



    return jsonify(context)


@admin.route('/invitation-code/', methods=['GET', 'POST'])
@auth.login_required
def invitation_code():
    """ 获取所有邀请码 """

    context = {'code': 400}
    if request.method == 'GET':
        try:
            page = request.args.get('page', 1)
            page_size = request.args.get('page_size', 15)
            queryset = InvitationCode.query
            paginate = queryset.order_by(InvitationCode.id.desc()).paginate(int(page), int(page_size), False)
            data  = {
                'list': [],
                'total': queryset.count()
            }
            for u in paginate.items:
                data['list'].append(u.to_dict())
            
            context['data'] = data
            context['code'] = 200


        except Exception as e:
            print(e)
            pass
    
    elif request.method == 'POST':
        count = request.json.get('count')
        level = request.json.get('level')

        src = string.ascii_uppercase + string.digits
        list_passwds = []
        
        for i in range(int(count)):
            list_passwd_all = random.sample(src, 12) #从字母和数字中随机取5位
            list_passwd_all.extend(random.sample(string.digits, 1))  #让密码中一定包含数字
            list_passwd_all.extend(random.sample(string.ascii_uppercase, 1)) #让密码中一定包含大写字母
            random.shuffle(list_passwd_all) #打乱列表顺序
            str_passwd = ''.join(list_passwd_all) #将列表转化为字符串
            if str_passwd not in list_passwds: #判断是否生成重复密码
                list_passwds.append(str_passwd)
        with atomic(db):
            for p in list_passwds:
                ic = InvitationCode(
                    code=p,
                    level=int(level)
                )
                db.session.add(ic)
            db.session.commit()
            context['data'] = list_passwds
            context['code'] = 200 
        
    return jsonify(context)

@admin.route('/backup/getpath/', methods=['GET', 'POST'])
@auth.login_required
def backup():
    """备份机制"""
    context = {'code': 400}
    articles = Article.query.all()
    res = ''
    for a in articles:
        if a.content:
            soup = BeautifulSoup(a.content, 'lxml')
            imgs = soup.find_all('img')
            if imgs:
                res = res + '#%s\n' % a.id
                for img in imgs:
                    link = img['src']
                    if link.find('/') == 0:
                        link = app.config['HOST'] + link
                    res = res + '%s\n' % link

    context['code'] = 200
    context['data'] = res
    return jsonify(context)


@admin.route('/generate_sitemap/', methods=['POST'])
@auth.login_required
def generate_sitemap():
    """生成站点地图"""
    context = {'code': 400}
    articles = Article.query.filter(Article.id>1, Article.status=='normal')
    times = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S+00:00")
    file = open('sitemap.xml', 'w', encoding='utf-8')
    file.writelines('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n')
    file.writelines("  <url>\n    <loc>%s/</loc>\n    <lastmod>%s</lastmod>\n    <changefreq>daily</changefreq>\n    <priority>1</priority>\n  </url>\n" % (app.config['HOST'], times))
    for a in articles:
        urls = '%s/article/%s/' % (app.config['HOST'], a.id)
        ment = "  <url>\n    <loc>%s</loc>\n    <lastmod>%s</lastmod>\n    <changefreq>weekly</changefreq>\n    <priority>0.8</priority>\n  </url>\n" % (urls, times)
        file.writelines(ment)

    file.writelines("</urlset>")
    file.close()

    context['code'] = 200
    return jsonify(context)

