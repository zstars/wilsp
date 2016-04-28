import shutil
import gevent
import grequests
import requests
import redis
import time


class CamFeeder(object):

    SLEEP_TIME = 0.1
    ACTIVE_CHECK_PERIOD = 10 # Check if webcam is active every 10 seconds.
    SLEEP_TIME_INACTIVE = 0.1 # Wait for x seconds after checking and being found inactive.

    def __init__(self, rdb, redis_prefix, cam_name, url):
        self._g = None
        self._rdb = rdb # type: redis.StrictRedis
        self._redis_prefix = redis_prefix
        self._url = url
        self._cam_name = cam_name

        self._last_active_check = None  # Timestamp of the last active check
        self._active = None # Whether the camera is active or not (being used, according to redis)

    def run(self):
        print("Running CamFeeder on URL {0}".format(self._url))
        while True:

            cur_time = time.time()
            if self._active is None or cur_time - self._last_active_check > 10:
                # Time to check that if the camera is active
                self._last_active_check = cur_time
                active = self._rdb.get("{}:cams:{}:active".format(self._redis_prefix, self._cam_name))
                self._active = active is not None

            if self._active:
                # Request the image and get the data
                rs = [grequests.get(self._url, stream=True)]
                r = grequests.map(rs)[0]
                data = r.content

                # Put the data into redis
                # Set a relatively early expire to ensure that wrong images do not stay for long
                self._rdb.setex("{}:cams:{}:lastframe".format(self._redis_prefix, self._cam_name), 10, data)

            if self._active:
                gevent.sleep(CamFeeder.SLEEP_TIME)
            else:
                gevent.sleep(CamFeeder.SLEEP_TIME_INACTIVE)

    def start(self):
        self._g = gevent.Greenlet(self.run)
        self._g.start()