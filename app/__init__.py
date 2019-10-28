###########################
#
# Name: HLD PICLine
# Author: HLD
# Date: 2019-07-03
#
###########################

from flask import Flask
from flask import render_template
from flask import jsonify
from flask import request
from flask_migrate import Migrate
from flask_compress import Compress
from flask_mail import Mail
from flask_login import LoginManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from config import Config
from app.exts import db
from app.exts import red
from app.models import User
import platform
import logging
import os

#create app
app = Flask(__name__)
app.config.from_object(Config) #settings
#SQL
if platform.system() == 'Windows':
    '''DEVELOPMENT'''
    app.config['SQLALCHEMY_DATABASE_URI'] = app.config['SQLALCHEMY_DATABASE_URI_DEVELOPMENT']

if platform.system() == 'Linux':
    '''PRODUCTION'''
    app.config['SQLALCHEMY_DATABASE_URI'] = app.config['SQLALCHEMY_DATABASE_URI_PRODUCTION']

#Compress
Compress(app)
#DB
db.init_app(app)
migrate = Migrate(app, db)
 
#Login
login_manager = LoginManager()
login_manager.login_view = 'basic.index'
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    user = User.query.get(user_id)
    if user and red.get(user.id) is None:
        user.add_score(10)
        red.set(user.id, 'logged', ex=60*60*24, nx=True)
    
    return user

# logs
handler = logging.FileHandler(app.config['LOGS_PATH'], encoding='UTF-8')
logging_format = logging.Formatter(app.config['LOGS_FORMATTER'])
handler.setFormatter(logging_format)
app.logger.addHandler(handler)
app.logger.setLevel(logging.INFO)

#mail
mail = Mail(app)
mail.init_app(app)

#limter
limiter = Limiter(app, key_func=get_remote_address)

#blueprint
#Basic
from app.basic import basic
app.register_blueprint(basic, url_prefix='/')

#Admin
from app.admin import admin
app.register_blueprint(admin, url_prefix='/admin')


"""HTTP 统一异常处理"""

@app.errorhandler(404)
def page_not_found(e):
    """404"""

    return render_template('404.html'), 404

@app.errorhandler(429)
def ratelimit_handler(e):
    return jsonify({'code': 429})
    

@app.errorhandler(500)
def internal_server_error(e):
    """500"""
    
    return jsonify({'code': 500})