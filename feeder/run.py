import time
import yaml
import redis
import signal
import sys
import gevent

from CamFeeder import CamFeeder

CAMS_FILE = '../cams.yml'
REDIS_PREFIX = 'wilsa'
REDIS_HOST = 'localhost'
REDIS_PORT = 6379
REDIS_DB = 0

cam_feeders = {}


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
        cf = CamFeeder(rdb, REDIS_PREFIX, cam_name, cam['url'])
        cam_feeders[cam_name] = cf
        cf.start()

    # Create the watchdog
    gevent.spawn(watchdog, rdb)

    # Wait for all the greenlets
    greenlets = [cam._g for cam in cam_feeders.values()]
    gevent.joinall(greenlets)


if __name__ == '__main__':
    run()
