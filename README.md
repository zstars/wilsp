
# Deployment

As of now the project has only been tested with Python 3.
Probably, Python 2.7 will NOT work without changes.

It is recommended to have different virtualenvs for Feeder and
Server, because, for now, Feeder relies on gevent and Server
relies on eventlet, and apparently, at least under some version
combinations, don't seem to work together nice enough with socketio.

## Feeder

The Feeder relies on gevent. (Enventually it should be ported
to eventlet). 

## Server

The Server relies on gunicorn and eventlet. The chances of it working
properly will be higher if gevent is *not* installed in the virtualenv.
 
