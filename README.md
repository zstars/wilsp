
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

### Configuration scheme

The main Feeder configuration file is the config.py script. The file is meant to be version-controlled.
Secret values should be referenced from that file as environment variables.

The cameras definition file (cams.yml) is a different, YML file. Its path is referenced through config.py through
the ```CAMS_YML``` setting.

### Scaling

To scale beyond a certain number of users you might need to increase your OS or Redis limits.

The OS open file and maximum number of connections limit may need to be increased. To check the current limits:
```limit -a```.

Redis by default supports a relatively low number of users (around 4000). To increase it, you need to run the server as such:
```
./redis-server --maxclients 100000
```

### REDIS statistics

cycle_elapsed: How long (in seconds) the current cycle of the stream has been active from the server-side
cycle_frames: How many frames have been rendered in that particular cycle

(FPS for the current cycle is thus cycle_frames / cycle_elapsed)



## Server

The Server relies on gunicorn and eventlet. The chances of it working
properly will be higher if gevent is *not* installed in the virtualenv.
 
