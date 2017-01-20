import os
import signal
import sys

import redis
import yaml
import gevent

# Pre-set the working directory.
from feeder.h264 import H264Feeder
from feeder.image_refresher import ImageRefreshCamFeeder
from feeder.mjpeg import MJPEGCamFeeder
from feeder.mpeg import MPEGFeeder

abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(dname)


CAMS_FILE = '../cams.yml'
CONFIG_FILE = 'config/config.yml'
REDIS_PREFIX = 'wilsa'
REDIS_HOST = 'localhost'
REDIS_PORT = 6379
REDIS_DB = 0

cam_feeders = {}
greenthreads = []


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

    # Load the basic configuration
    config = yaml.load(open(CONFIG_FILE, 'r'))

    # Connect to the redis instance
    rdb = redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, decode_responses=True)

    # Create every cam feeder
    for cam_name, cam in cams.items():
        print('Adding cam {0} to the dict'.format(cam_name))
        if 'rotation' in cam:
            rotation = float(cam['rotation'])
        else:
            rotation = 0.0

        url = cam.get('img_url')
        mjpeg_url = cam.get('mjpeg_url')
        mpeg = cam.get('mpeg')
        h264 = cam.get('h264')

        if mjpeg_url is not None:
            cf = MJPEGCamFeeder(rdb, REDIS_PREFIX, cam_name, mjpeg_url, 30, rotation)
        elif url is not None:
            cf = ImageRefreshCamFeeder(rdb, REDIS_PREFIX, cam_name, url, 30, rotation)

        if mjpeg_url is None and url is None:
            raise Exception("img_url or mjpeg_url not specified for camera {}".format(cam_name))

        if mpeg is not None and mpeg is True:
            mpeg_cf = MPEGFeeder(rdb, cam_name, mjpeg_url, config.get('FFMPEG_BIN'))
            cam_feeders[cam_name + '/mpeg'] = mpeg_cf
            mpeg_cf.start()

        if h264 is not None and h264 is True:
            h264_cf = H264Feeder(rdb, cam_name, mjpeg_url, config.get('FFMPEG_BIN'))
            cam_feeders[cam_name + '/h264'] = h264_cf
            h264_cf.start()

        cam_feeders[cam_name] = cf
        cf.start()

    # Create the watchdog
    g = gevent.spawn(watchdog, rdb)
    greenthreads.append(g)

    # Wait for all the greenlets
    cam_feeder_greenthreads_list = [cam._g for cam in cam_feeders.values()]

    for cam_feeder_greenthreads in cam_feeder_greenthreads_list:
        greenthreads.extend(cam_feeder_greenthreads)


if __name__ == '__main__':
    run()

    # Wait for greenlets
    for g in greenthreads:
        g.join()
