from datetime import datetime
from flask import render_template, session, redirect, url_for, current_app
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
    pass


