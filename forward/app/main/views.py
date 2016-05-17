from flask import render_template

from . import main


@main.route('/')
def index():
    return render_template('base.html')


@main.route('/inputs/<cam>', methods=['POST'])
def inputs(cam):
    return "ok"