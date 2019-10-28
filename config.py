 ###########################
#
# Name: HLD PICLine Config
# Author: HLD
# Date: 2019-07-03
#
###########################


class Config(object):
    """ HLDTools Config """

    HOST = 'https://zhiz.xyz'
    SECRET_KEY = '&o8#fgk!b3ymBhbyXFtr6MtPN@Cg$Pkh'
    SQLALCHEMY_DATABASE_URI_DEVELOPMENT = 'db.sqlite3'
    SQLALCHEMY_DATABASE_URI_PRODUCTION = 'mysql://root:root@localhost:3306/hldpic'
    SQLALCHEMY_POOL_RECYCLE = 3
    # SQLALCHEMY_ECHO = True
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    #Redis
    REDIS_HOST = 'localhost'
    REDIS_PORT = 6379
    REDIS_PASSWD = 'redis$hld'
    #logs
    LOGS_PATH = 'logs/flask.log'
    LOGS_FORMATTER = '[%(asctime)s - %(levelname)s - %(filename)s:%(funcName)s %(lineno)s] => %(message)s'
    #后台权限
    ACCESS_BACKEND_LEVEL = 99
    #分页
    PAGINATION_ARTICLE = 6
    PAGINATION_NOTICE = 10
    PAGINATION_FAVORITE = 10
    #上传
    UPLOAD_ROOT_FOLDER = '/static/upload/'
    
    #邮件
    MAIL_DEFAULT_SENDER = ''
    MAIL_SERVER = ''
    MAIL_PORT = 465
    MAIL_USE_SSL = True
    MAIL_USERNAME = ''
    MAIL_PASSWORD = ''
    MAIL_SUPPRESS_SEND = False