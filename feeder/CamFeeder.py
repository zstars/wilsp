import shutil
import gevent
import grequests
import requests
import redis


class CamFeeder(object):

    SLEEP_TIME = 2

    def __init__(self, rdb, redis_prefix, cam_name, url):
        self._g = None
        self._rdb = rdb # type: redis.StrictRedis
        self._redis_prefix = redis_prefix
        self._url = url
        self._cam_name = cam_name

    def run(self):
        print("Running CamFeeder on URL {0}".format(self._url))
        while True:
            # Request the image and get the data
            rs = [grequests.get(self._url, stream=True)]
            r = grequests.map(rs)[0]
            data = r.content

            # Put the data into redis
            # Set a relatively early expire to ensure that wrong images do not stay for long
            self._rdb.setex("{}:cams:{}:lastframe".format(self._redis_prefix, self._cam_name), 10, data)

            gevent.sleep(CamFeeder.SLEEP_TIME)

    def start(self):
        self._g = gevent.Greenlet(self.run)
        self._g.start()