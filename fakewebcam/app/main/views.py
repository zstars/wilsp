
import io
import time


from flask import render_template, current_app, make_response, Response, request, stream_with_context

from app.main import main


@main.route('/')
def index():
    return "Fake Webcam 1.0"

