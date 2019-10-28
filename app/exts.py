from config import Config

#Flask Sqlalchemy
from flask_sqlalchemy import SQLAlchemy
db = SQLAlchemy()

#Redis
import redis
red = redis.Redis(
    host=Config.REDIS_HOST, 
    port=Config.REDIS_PORT,
    password=Config.REDIS_PASSWD
    )
