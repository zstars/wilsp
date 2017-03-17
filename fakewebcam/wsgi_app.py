#!/usr/bin/env python

import os
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