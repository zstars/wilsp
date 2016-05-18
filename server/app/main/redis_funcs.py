from flask import current_app

from app import rdb


def mark_active(cam_name, stream_format):
    """
    Marks the specified camera id as active for the specified format, so that if there is a feeder
    for it, it can start pushing getting and pushing data.
    :param cam_name:
    :param stream_format:
    :return:
    """
    REDIS_PREFIX = current_app.config['REDIS_PREFIX']
    cam_key = REDIS_PREFIX + ":cams:" + cam_name + ":active:" + stream_format
    rdb.setex(cam_key, 30, 1)


def is_active(cam_name, stream_format):
    """
    Checks whether the specified camera id is active for the specified format.
    :param cam_name:
    :param stream_format:
    :return:
    """
    REDIS_PREFIX = current_app['REDIS_PREFIX']
    cam_key = REDIS_PREFIX + ":cams:" + cam_name + ":active:" + stream_format
    result = rdb.get(cam_key)
    return result is not None
