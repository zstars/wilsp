from flask import render_template, request

from app import rdb
from . import main


@main.route('/')
def index():
    return render_template('base.html')


@main.route('/inputs/<cam>', methods=['POST', 'GET'])
def inputs(cam):
    """
    Forwards the raw data to the appropriate redis channel.
    GET method is accepted but it is only for testing purposes.
    :param cam:
    :return:
    """
    data = request.data

    # Publish the data in redis as an event.
    rdb.publish('{}/mpeg', data)

    return ""