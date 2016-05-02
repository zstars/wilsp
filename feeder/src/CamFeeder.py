import gevent
import grequests
import redis
import time
import io
from PIL import Image


class CamFeeder(object):

    TARGET_FPS = 15
    ACTIVE_CHECK_PERIOD = 0.1 # Check if webcam is active every 10 seconds.
    SLEEP_TIME_INACTIVE = 0.1 # Wait for x seconds after checking and being found inactive.
    DEBUG = False

    def __init__(self, rdb, redis_prefix, cam_name, url, rotation = None):
        self._g = None
        self._rdb = rdb # type: redis.StrictRedis
        self._redis_prefix = redis_prefix
        self._url = url
        self._cam_name = cam_name
        self._rotation = rotation if rotation is not None else 0

        self._last_active_check = None  # Timestamp of the last active check
        self._last_frame_time = time.time()
        self._active = None  # Whether the camera is active or not (being used, according to redis)

        self._active_since = None  # Timestamp when we last became active
        self._frames_count = 0  # Frames count in the last active period.

    def run(self):
        print("Running CamFeeder on URL {0}".format(self._url))

        cur_time = time.time()
        while True:

            if self._active is None or cur_time - self._last_active_check > CamFeeder.ACTIVE_CHECK_PERIOD:
                # Time to check that if the camera is active
                self._last_active_check = cur_time
                if not self._active:
                    active = self._rdb.get("{}:cams:{}:active".format(self._redis_prefix, self._cam_name))
                    self._active = active is not None
                    if self._active:

                        if CamFeeder.DEBUG:
                            # We just became active.
                            print("NOW ACTIVE")
                            self._active_since = time.time()
                            self._frames_count = 0
                else:
                    active = self._rdb.get("{}:cams:{}:active".format(self._redis_prefix, self._cam_name))
                    self._active = active is not None

                if CamFeeder.DEBUG:
                    if self._active and self._frames_count > 0 and self._active_since > 0:
                        print("CURRENT ACTIVE PERIOD FPS: {}".format(self._frames_count / (time.time() - self._active_since)))

            if self._active:
                # Request the image and get the data
                rs = [grequests.get(self._url, stream=True)]
                r = grequests.map(rs)[0]
                data = r.content

                # Rotate the image if necessary
                if self._rotation > 0:
                    sio_in = io.BytesIO(data)
                    img = Image.open(sio_in)  # type: Image
                    img = img.rotate(self._rotation, expand=True)
                    sio_out = io.BytesIO()
                    img.save(sio_out, 'jpeg')
                    data = sio_out.getvalue()
                    img.close()

                # Put the data into redis
                # Set a relatively early expire to ensure that wrong images do not stay for long
                self._rdb.setex("{}:cams:{}:lastframe".format(self._redis_prefix, self._cam_name), 10, data)

                self._frames_count += 1

            cur_time = time.time()

            if self._active:
                # Calculate the time to sleep and save the cur_time so we can calculate the next one.
                elapsed_since_last_render = cur_time - self._last_frame_time
                time_to_sleep = 1.0 / CamFeeder.TARGET_FPS - elapsed_since_last_render
                self._last_frame_time = cur_time

                # If we still have time before we should render the next frame we sleep.
                # Otherwise we are running late and we do not wait.
                if time_to_sleep > 0:
                    gevent.sleep(time_to_sleep)
            else:
                gevent.sleep(CamFeeder.SLEEP_TIME_INACTIVE)

    def start(self):
        self._g = gevent.Greenlet(self.run)
        self._g.start()