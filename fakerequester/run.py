import gevent
from gevent import monkey
monkey.patch_all()

import requests
import time
from socketIO_client import SocketIO, LoggingNamespace

from config import config as config_dict
config = config_dict['development']

import logging

logging.getLogger('socketIO-client').setLevel(logging.DEBUG)
logging.basicConfig()



threadlets = []

URL = "http://localhost:5000/exps/imgrefresh/cam0_0"


def main():
    for i in range(config.NUMBER):
        # Start worker threadlets

        if config.TYPE == "img":
            threadlets.append(gevent.spawn(run_img_g))
        elif config.TYPE == "sio":
            threadlets.append(gevent.spawn(run_sio_g))

    gevent.joinall(threadlets)


def run_sio_g():

    with SocketIO('localhost', 8000, LoggingNamespace) as socketIO:
        socketIO.emit('aaa')
        socketIO.wait(seconds=1)


def run_img_g():
    started_time = time.time()
    count_frames = 0

    while True:

        update_start_time = time.time()

        r = requests.get(URL)
        count_frames += 1

        elapsed = time.time() - update_start_time
        intended_period = 1 / config.TFPS  # That's the approximate time a frame should take.

        time_left = intended_period - elapsed
        # print("Time left: {}".format(time_left))
        if time_left < 0:
            # We are simply not managing to keep up with the intended frame rate, but for this
            # cam feeder, that is not a (big) problem.
            gevent.sleep(0)
        else:
            gevent.sleep(time_left)

        if count_frames % 100 == 0:
            print("FPS: {}".format(count_frames / (time.time() - started_time)))

main()
