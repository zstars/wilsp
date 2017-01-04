#!/bin/bash

. /home/lrg/.virtualenvs/wilsa/bin/activate
cd /home/lrg/wilsaproxy/server/src
nohup gunicorn --bind 127.0.0.1:8500 -w 4 --pid wilsa.server.pid wsgi_app:application > nohup.gunicorn.out &
