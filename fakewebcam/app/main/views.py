import glob
import io
import os
import time
import re
from bisect import bisect_right

from flask import render_template, current_app, make_response, Response, request, stream_with_context
from flask import send_file

from app.main import main

images = []
images_indexed = {}
timestamps = []
cycle_start_time = (time.time() * 1000)

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

@main.route('/')
def index():
    return "Fake Webcam 1.0"

