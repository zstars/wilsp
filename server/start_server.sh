#!/bin/bash

. /home/lrg/.virtualenvs/wilsa/bin/activate
cd /home/lrg/labsland/wilsaproxy/server/src
nohup gunicorn --bind 127.0.0.1:8500 -w 1 -k geventwebsocket.gunicorn.workers.GeventwebSocketWorker --pid wilsa.server.pid wsgi_app:application > nohup.gunicorn.out &
