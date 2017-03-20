import glob
import io
import os
import time
import re
from bisect import bisect_right

import gevent
from PIL import Image
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

    current_time = int(time.time() * 1000)
    global cycle_start_time
    elapsed_time = current_time - cycle_start_time
    if elapsed_time > 10000:
        cycle_start_time = int(time.time() * 1000)
        current_time = int(time.time() * 1000)
        elapsed_time = 0

    earliest_ts = bisect_right(timestamps, elapsed_time) - 1
    if earliest_ts < 0:
        earliest_ts = 0

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


def generator_mjpeg(tfps):
    target_fps = tfps

    last_frame_start_time = 0

    while True:

        global mjpeg_count
        print("[DBG]: Serving MJPEG frame: %d" % mjpeg_count)
        mjpeg_count += 1

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
            current_time = int(time.time() * 1000)
            elapsed_time = 0

        earliest_ts = bisect_right(timestamps, elapsed_time) - 1
        if earliest_ts < 0:
            earliest_ts = 0

        frame = images[earliest_ts][1]

        yield ('--frame\r\n'
               'Content-Type: image/jpeg\r\nContent-Length: {}\r\nX-Timestamp: {}\r\n\r\n'.format(len(frame), time.time()).encode() + frame + b'\r\n')
