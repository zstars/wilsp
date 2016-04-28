from datetime import datetime
from flask import render_template, session, redirect, url_for, current_app, make_response, Response
from . import main
from app import rdb


@main.route('/')
def index():
    return render_template('base.html')


@main.route('/cam/<cam_id>')
def cam(cam_id):
    """
    Returns the image for the specified camera.
    :param cam_id:
    :return:
    """
    REDIS_PREFIX = current_app.config['REDIS_PREFIX']

    alive = rdb.get(REDIS_PREFIX + ":feeder:alive")
    if alive is None:
        return current_app.send_static_file('no_image_available.png')

    cam_key = REDIS_PREFIX + ":cams:" + cam_id + ":lastframe"
    frame = rdb.get(cam_key)
    if frame is None:
        return current_app.send_static_file('no_image_available.png')
    else:
        return Response(frame, status=200, mimetype="image/jpeg")


