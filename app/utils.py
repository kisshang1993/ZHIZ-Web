###########################
#
# Name: HLD PIC Utils
# Author: HLD
# Date: 2019-07-29
#
###########################
from flask import current_app
from app import app
from app import mail
from .exts import db
from flask_mail import Message
from threading import Thread
from functools import wraps
from contextlib import ContextDecorator
from PIL import Image, ImageDraw, ImageFont, ImageSequence
import os

def send_async_email(msg):
    """异步发送邮件"""

    with app.app_context():
        mail.send(msg)

def send_mail(body):
    """发送邮件"""

    msg = Message()
    msg.subject = body.get('subject')
    msg.recipients = body.get('recipients')
    msg.body = body.get('body')
    msg.html = body.get('html')

    thr = Thread(target=send_async_email, args=[msg])
    thr.start()

    print('邮件发送 -> ', msg.recipients)
    return True







def atomic(db):
    '''
    '''
    if callable(db):
        return Atomic(db)(db)
    else:
        return Atomic(db)


class Atomic(ContextDecorator):

    def __init__(self, db):
        self.db = db

    def __enter__(self):
        pass

    def __exit__(self, exc_typ, exc_val, tb):
        if exc_typ:
            self.db.session.rollback()
        else:
            self.db.session.commit()


def watermark(image_path):
    """添加水印"""

    mark = Image.open('hld.png').convert('RGBA')
    font_mark = ImageFont.truetype('msyh.ttf', 24)

    #mark = mark.resize()
    path, img_name = os.path.split(image_path)
    name, ext = os.path.splitext(img_name)

    im = Image.open(image_path)
    im_out = Image.open('out.gif')
    print(im.info)
    print(im_out.info)
    return
    if ext == '.gif':
        fps_dir = img_name+'_fps'
        if not os.path.exists(fps_dir):
            os.mkdir(fps_dir)

        sequence = []
        index = 1
        for f in ImageSequence.Iterator(im):
            f.save(os.path.join(fps_dir, str(index) + '.png'))
            watered = add_watermark_to_image(f, mark)
            watered.save(os.path.join(fps_dir, str(index) + '_watered.png'))
            sequence.append(watered)
            index = index + 1
    
        sequence[0].save('out.gif', save_all=True, append_images=sequence[1:])

    else:
        layer = Image.new('RGBA', im.size, (0,0,0,0))
        layer.paste(mark, (im.size[0]-mark.size[0]-10, im.size[1]-mark.size[1]-10))
        out=Image.composite(layer,im,layer)
        out.save('w.%s' % ext)


def add_watermark_to_image(image, watermark):

    rgba_image = image.convert('RGBA')
    rgba_watermark = watermark.convert('RGBA')

    image_x, image_y = rgba_image.size
    watermark_x, watermark_y = rgba_watermark.size

    # 缩放图片
    scale = 10
    watermark_scale = max(image_x / (scale * watermark_x), image_y / (scale * watermark_y))
    new_size = (int(watermark_x * watermark_scale), int(watermark_y * watermark_scale))
    rgba_watermark = rgba_watermark.resize(new_size, resample=Image.ANTIALIAS)
    # 透明度
    rgba_watermark_mask = rgba_watermark.convert("L").point(lambda x: min(x, 180))
    rgba_watermark.putalpha(rgba_watermark_mask)

    watermark_x, watermark_y = rgba_watermark.size
    # 水印位置
    rgba_image.paste(rgba_watermark, (image_x - watermark_x, image_y - watermark_y), rgba_watermark_mask)

    return rgba_image



