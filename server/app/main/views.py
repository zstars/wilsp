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
    alive = rdb.get("wilsa:feeder:alive")
    if alive is None:
        return "Feeder is down. Cam id: " + cam_id

    cam_key = "wilsa:cams:" + cam_id + ":lastframe"
    frame = rdb.get(cam_key)
    if frame is None:
        return "No frame available for: " + cam_key
    else:
        return Response(frame, status=200, mimetype="image/jpeg")


