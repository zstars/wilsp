import io
from datetime import datetime
from PIL import Image
from flask import render_template, session, redirect, url_for, current_app, make_response, Response, request
from . import main
from app import rdb


@main.route('/')
def index():
    return render_template('base.html')


@main.route('/cams/<cam_id>')
def cam(cam_id):
    """
    Returns the image for the specified camera.
    :param cam_id:
    :return:
    """
    REDIS_PREFIX = current_app.config['REDIS_PREFIX']
    rotate = request.values.get("rotate", 0)

    try:
        rotate = float(rotate)
    except ValueError:
        return make_response("Wrong value: Rotate must be a float", 400)

    cam_key = REDIS_PREFIX + ":cams:" + cam_id

    frame = rdb.get(cam_key + ":lastframe")

    if frame is None:
        # We check whether the feeder itself is alive to be able to give a proper error,
        # even if, for now, we don't.
        alive = rdb.get(REDIS_PREFIX + ":feeder:alive")
        if alive is None:
            return current_app.send_static_file('no_image_available.png')

        return current_app.send_static_file('no_image_available.png')
    else:
        # It will also be possible to rotate the image via the actual definition of the camera, which will be
        # more efficient because it means that the rotated image will be cached in redis.
        if rotate > 0:
            sio_in = io.BytesIO(frame)
            img = Image.open(sio_in)  # type: Image
            img = img.rotate(rotate, expand=True)
            sio_out = io.BytesIO()
            img.save(sio_out, 'jpeg')
            frame = sio_out.getvalue()
            img.close()

        # Mark the cam as active. This signals the feeder so that it starts working on this. It could potentially
        # be made more efficient by working in a background
        # thread, but that would be overkill for now.
        rdb.setex(cam_key + ":active", 30, 1)

        return Response(frame, status=200, mimetype="image/jpeg")


