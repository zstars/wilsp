#!/usr/bin/env python

import os
from os import environ
import sys

from app import create_app

FAKEWEBCAM_DIR = os.path.dirname(__file__)
if FAKEWEBCAM_DIR == '':
    FAKEWEBCAM_DIR = os.path.abspath('.')

sys.path.insert(0, FAKEWEBCAM_DIR)
os.chdir(FAKEWEBCAM_DIR)

sys.stdout = open('stdout.txt', 'w', 100)
sys.stderr = open('stderr.txt', 'w', 100)


application = create_app('production')

import logging
file_handler = logging.FileHandler(filename='errors.log')
file_handler.setLevel(logging.INFO)
application.logger.addHandler(file_handler)



class CherrokeeFix(object):

    def __init__(self, app, script_name):
        self.app = app
        self.script_name = script_name

    def __call__(self, environ, start_response):
        path = environ.get('SCRIPT_NAME', '') + environ.get('PATH_INFO', '')
        environ['SCRIPT_NAME'] = self.script_name
        environ['PATH_INFO'] = path[len(self.script_name):]
        # assert path[:len(self.script_name)] == self.script_name
        return self.app(environ, start_response)


application.wsgi_app = CherrokeeFix(application.wsgi_app, '/fakewebcam')
