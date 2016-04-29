

import os
import signal
import sys

import gevent
import redis
import yaml

from CamFeeder import CamFeeder


# Pre-set the working directory.
abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(dname)


CAMS_FILE = '../../cams.yml'
REDIS_PREFIX = 'wilsa'
REDIS_HOST = 'localhost'
REDIS_PORT = 6379
REDIS_DB = 0

cam_feeders = {}
greenlets = []


def signal_handler(signal, frame):
    print('Now exiting...')
    sys.exit(0)


def watchdog(rdb):
    """
    :param rdb: Redis connection
    :type rdb: redis.StrictRedis
    :return:
    """
    while True:
        rdb.setex(REDIS_PREFIX + ":feeder:alive", 5, True)
        gevent.sleep(2)


def run():
    global greenlets

    # Register exit handler
    signal.signal(signal.SIGINT, signal_handler)
    print('Press Ctrl+C to exit.')

    # Load the cameras configuration
    data = yaml.load(open(CAMS_FILE, 'r'))
    cams = data['cams']  # type: dict

    # Connect to the redis instance
    rdb = redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB)

    # Create every cam feeder
    for cam_name, cam in cams.items():
        print('Adding cam {0} to the dict'.format(cam_name))
        rotation = float(cam['rotation'])
        cf = CamFeeder(rdb, REDIS_PREFIX, cam_name, cam['url'], rotation)
        cam_feeders[cam_name] = cf
        cf.start()

    # Create the watchdog
    g = gevent.spawn(watchdog, rdb)
    greenlets.append(g)

    # Wait for all the greenlets
    greenlets.extend([cam._g for cam in cam_feeders.values()])


if __name__ == '__main__':
    run()

    # Wait for greenlets
    gevent.joinall(greenlets)
