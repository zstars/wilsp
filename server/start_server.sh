#!/bin/bash

. /home/lrg/.virtualenvs/wilsa/bin/activate
cd /home/lrg/labsland/wilsaproxy/server/src
nohup gunicorn --bind 0.0.0.0:8500 -w 1 -k gevent --pid wilsa.server.pid wsgi_app:application > nohup.gunicorn.out &
