import glob
import hashlib
import io
import os
import time
import re
from bisect import bisect_right
import zlib

import gevent
from PIL import Image
import qrcode
from flask import render_template, current_app, make_response, Response, request, stream_with_context
from flask import send_file

from app.main import main

images = []
images_indexed = {}
timestamps = []
cycle_start_time = (time.time() * 1000)

mjpeg_count = 0


@main.record
def setup(state):
    # Load images from directory
    dir = state.app.config['CLIP_DIR']
    file_paths = [p for p in glob.glob(os.path.join(dir, 'ar_*.jpg'))]
    for f in file_paths:
        ts = re.findall(r".*/ar_([0-9]+)\.jpg", f)
        ts = ts[0]
        with open(f, "rb") as of:
            content = of.read()
        images.append((int(ts), content))
        images.sort(key=lambda k: k[0])
        images_indexed[int(ts)] = content
        global timestamps
        timestamps = [img[0] for img in images]


@main.route('/fakewebcam/version')
def leveldeep():
    return "Leveldeep"


@main.route('/version')
def version():
    return "Version: Fake Webcam 1.0"


@main.route('/image.jpg')
def image():
    # Decide which image to serve.

    force_qr = request.values.get("qr", "0") == "1"

    current_time = int(time.time() * 1000)
    global cycle_start_time
    elapsed_time = current_time - cycle_start_time

    if elapsed_time > 10000:
        cycle_start_time = int(time.time() * 1000)
        elapsed_time = 0

    earliest_ts = bisect_right(timestamps, elapsed_time) - 1
    if earliest_ts < 0:
        earliest_ts = 0

    if force_qr or (current_app.config["EMBED_QR"] and int(current_time / (1000/current_app.config["EMBED_QR_FREQ"])) % current_app.config['EMBED_QR_FREQ'] == 0):
        qr = create_qr()
        img = Image.open(io.BytesIO(images[earliest_ts][1]))
        img.paste(qr)
        img_io = io.BytesIO()
        img.save(img_io, 'JPEG', quality=70)
        img_io.seek(0)
        return send_file(img_io, mimetype="image/jpg")
    else:
        return send_file(io.BytesIO(images[earliest_ts][1]), mimetype="image/jpg")


@main.route('/image.mjpeg')
def mjpeg():
    tfps = request.values.get("tfps", current_app.config["MJPEG_FPS"])
    tfps = int(tfps)
    return Response(stream_with_context(generator_mjpeg(tfps)),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


@main.route('/')
def index():
    return "Fake Webcam 1.0"


def create_qr():
    """
    Creates a QR image with the current timestamp.
    :return:
    """
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=5
    )
    data = str(int(time.time() * 1000))
    crc = hex(zlib.crc32(data.encode('utf-8')))

    qrdata = "{}|{}".format(data, crc)
    qr.add_data(qrdata)
    qr.make(fit=True)

    img = qr.make_image()
    return img


def generator_mjpeg(tfps):
    target_fps = tfps

    last_frame_start_time = 0

    frame_num = 0

    while True:

        global mjpeg_count
        print("[DBG]: Serving MJPEG frame: %d" % mjpeg_count)
        mjpeg_count += 1
        frame_num += 1

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

        # Get the frame that we should render

        # Decide which image to serve.

        current_time = int(time.time() * 1000)
        global cycle_start_time
        elapsed_time = current_time - cycle_start_time
        if elapsed_time > 10000:
            cycle_start_time = int(time.time() * 1000)
            elapsed_time = 0

        earliest_ts = bisect_right(timestamps, elapsed_time) - 1
        if earliest_ts < 0:
            earliest_ts = 0

        frame = images[earliest_ts][1]

        if current_app.config["EMBED_QR"]:

            if frame_num % current_app.config["EMBED_QR_FREQ"] == 0:

                qr = create_qr()
                img = Image.open(io.BytesIO(frame))

                img.paste(qr)

                img_io = io.BytesIO()
                img.save(img_io, 'JPEG', quality=70)
                img_io.seek(0)

                frame = img_io.getvalue()

        yield ('--frame\r\n'
               'Content-Type: image/jpeg\r\nContent-Length: {}\r\nX-Timestamp: {}\r\n\r\n'.format(len(frame), time.time()).encode() + frame + b'\r\n')
