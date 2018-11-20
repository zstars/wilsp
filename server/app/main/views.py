import gevent
from gevent import monkey
monkey.patch_all()

import io
import time

from PIL import Image
from flask import render_template, current_app, make_response, Response, request, stream_with_context

from app import rdb
from . import main


@main.route('/')
def index():
    return render_template('base.html')


@main.route('/exps/imgrefresh/<cam>')
def exp_imgrefresh(cam):
    """
    Seems to be working fine. Tests not yet available, though.
    :param cam:
    :return:
    """
    tfps = request.values.get('tfps', 30)
    qr = request.values.get('qr', 0)
    return render_template('exps/camera_image_refresh.html', cam=cam, tfps=tfps, qr=qr)


@main.route('/exps/mjpegnative/<cam>')
def exp_mjpegnative(cam):
    """
    Working fine. Though native MJPEG has no significant advantages over any other method.
    :param cam:
    :return:
    """
    tfps = request.values.get('tfps', 5)
    tfps = int(tfps)
    return render_template('exps/camera_mjpeg_native.html', cam=cam, tfps=tfps)


@main.route('/exps/mjpegjs/<cam>')
def exp_mjpegjs(cam):
    """
    Working fine. Relies on socket IO.
    :param cam:
    :return:
    """
    tfps = request.values.get('tfps', 5)
    path = current_app.config.get('SOCKETIO_PATH', '')
    return render_template('exps/camera_mjpeg_js.html', cam=cam, socketio_path=path, tfps=tfps)


@main.route('/exps/mpegjs/<cam>')
def exp_mpegjs(cam):
    path = current_app.config.get('SOCKETIO_PATH', '')
    return render_template('exps/camera_mpeg_js.html', cam=cam, socketio_path=path)


@main.route('/exps/h264js/<cam>')
def exp_h264js(cam):
    path = current_app.config.get('SOCKETIO_PATH', '')
    qr = request.values.get('qr', 0)
    return render_template('exps/camera_h264_js.html', cam=cam, socketio_path=path, qr=qr)


count = 0


def generator_mjpeg(cam_id, not_available, redis_prefix, rotate, tfps):
    try:
        rotate = float(rotate)
    except ValueError:
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + not_available + b'\r\n')
        yield make_response("Wrong value: Rotate must be a float", 400)
        return  # Return in a generator must be empty.

    cam_key = redis_prefix + ":cams:" + cam_id

    target_fps = tfps

    last_frame_start_time = 0

    while True:

        global count
        print("[DBG]: Serving MJPEG frame: %d" % count)
        count += 1

        # FPS rate limiting
        target_frame_time = 1.0 / target_fps
        current_time = time.time()
        time_since_last_frame_start = current_time - last_frame_start_time

        time_to_wait = target_frame_time - time_since_last_frame_start
        if time_to_wait > 0:
            print("Sleeping for: %f" % time_to_wait)
            gevent.sleep(time_to_wait)
            last_frame_start_time = current_time + time_to_wait
        else:
            print("Sleeping for 0")
            # We cannot keep up. Maybe we should lower the target FPS.
            last_frame_start_time = current_time

        frame = rdb.get(cam_key + ":lastframe")

        # Mark the cam as active. This signals the feeder so that it starts working on this. It could potentially
        # be made more efficient by working in a background
        # thread, but that would be overkill for now.
        rdb.setex(cam_key + ":active", 30, 1)

        if frame is None:
            # We check whether the feeder itself is alive to be able to give a proper error,
            # even if, for now, we don't.
            alive = rdb.get(redis_prefix + ":feeder:alive")
            if alive is None:
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + not_available + b'\r\n')

            # If there is no error, we just retry: the webcam image should be available soon.
            if current_app.config.get('WAIT_FOR_WEBCAM', False):
                gevent.sleep(current_app.config.get('WAIT_FOR_WEBCAM_TIME', 0.1))
                continue

            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + not_available + b'\r\n')
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

            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')


@main.route('/cams/<cam_id>/mpeg')
def test_mpeg(cam_id):
    return render_template('wsmpeg/mpeg.html')


@main.route('/cams/<cam_id>/mjpeg')
def cam_mjpeg(cam_id):
    """
    Returns a stream for the specified camera.
    :param cam_id:
    :return:
    """
    tfps = request.values.get("tfps", 5)
    tfps = int(tfps)
    rotate = request.values.get("rotate", 0)
    REDIS_PREFIX = current_app.config['REDIS_PREFIX']
    # TODO: Not pretty.
    not_available = open("app/static/no_image_available.png", "rb").read()
    return Response(stream_with_context(generator_mjpeg(cam_id, not_available, REDIS_PREFIX, rotate, tfps)),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


def test_gen(data):
    n = 0
    while True:
        n += 1
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + data + b'\r\n')


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

    crop_top = request.values.get("crop_top")
    crop_bottom = request.values.get("crop_bottom")
    crop_right = request.values.get("crop_right")
    crop_left = request.values.get("crop_left")

    cam_key = REDIS_PREFIX + ":cams:" + cam_id

    # We will retry under some circumstances.
    while True:

        frame = rdb.get(cam_key + ":lastframe")

        # Mark the cam as active. This signals the feeder so that it starts working on this. It could potentially
        # be made more efficient by working in a background
        # thread, but that would be overkill for now.
        rdb.setex(cam_key + ":active", 30, 1)

        if frame is None:
            # We check whether the feeder itself is alive to be able to give a proper error,
            # even if, for now, we don't.
            alive = rdb.get(REDIS_PREFIX + ":feeder:alive")
            if alive is None:
                return current_app.send_static_file('no_image_available.png'), 400

            # Check whether the webcam is explicitly reporting an error. If it does, we just return not-available.
            err = rdb.get(cam_key + ":error")
            if err is not None:
                return current_app.send_static_file('no_image_available.png'), 400

            # If there is no error, we just retry: the webcam image should be available soon.
            if current_app.config.get('WAIT_FOR_WEBCAM', False):
                gevent.sleep(current_app.config.get('WAIT_FOR_WEBCAM_TIME', 0.1))
                continue
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

            return Response(frame, status=200, mimetype="image/jpeg")
