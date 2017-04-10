#!/usr/bin/env python

import os
import sys

from app import create_app

WILSASERVER_DIR = os.path.dirname(__file__)
if WILSASERVER_DIR == '':
    WILSASERVER_DIR = os.path.abspath('.')

sys.path.insert(0, WILSASERVER_DIR)
os.chdir(WILSASERVER_DIR)

sys.stdout = open('stdout.txt', 'w', 100)
sys.stderr = open('stderr.txt', 'w', 100)


application = create_app(os.environ.get("FLASK_CONFIG", 'production'))

import logging
file_handler = logging.FileHandler(filename='errors.log')
file_handler.setLevel(logging.INFO)
application.logger.addHandler(file_handler)