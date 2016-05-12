import io
import os
from unittest.mock import patch

import gevent
import requests
from mockredis import mock_strict_redis_client

from test.FeederTestBase import FeederTestBase
# Fix the working path
from camfeeder.ImageRefreshCamFeeder import ImageRefreshCamFeeder, FrameGrabbingException

abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(os.path.join(dname, '..'))


class TestBasic(FeederTestBase):

    def setUp(self):
        self.rdb = mock_strict_redis_client()
        self.img = open('data/img.jpg', 'rb').read()
        self.cf = ImageRefreshCamFeeder(self.rdb, 'wilsat', 'archimedes', 'http://fake.com/image.jpg', 10, 0)

    def tearDown(self):
        pass

    @patch('grequests.get')
    @patch('grequests.map')
    def test_grab_frame(self, map_patch, get_patch):

        # Mock grequests get
        response = requests.Response()
        response.status_code = 200
        get_patch.return_value = response

        # Mock grequests map
        response = requests.Response()
        response.status_code = 200
        response.raw = io.BytesIO(b"1234567890"*12)
        map_patch.return_value = [response]

        frame = self.cf._grab_frame()
        self.assertIsNotNone(frame)
        self.assertGreater(len(frame), 3)
        self.assertTrue(frame.startswith(b'1234567890'))

    @patch('grequests.get')
    @patch('grequests.map')
    def test_frame_grabbing_exception(self, map_patch, get_patch):

        # Mock grequests get
        response = requests.Response()
        response.status_code = 500
        get_patch.return_value = response

        # Mock grequests map
        response = requests.Response()
        response.status_code = 500
        response.raw = io.BytesIO(b"1234567890"*12)
        map_patch.return_value = [response]

        try:
            frame = self.cf._grab_frame()
            self.assertIsNotNone(frame)
            self.assertGreater(len(frame), 3)
            self.assertTrue(frame.startswith(b'1234567890'))
        except FrameGrabbingException as fge:
            pass
        else:
            self.fail('Expected a FrameGrabbingException')

class TestBasicRegressions(FeederTestBase):

    def setUp(self):
        self.rdb = mock_strict_redis_client()
        self.img = open('data/img.jpg', 'rb').read()
        self.cf = ImageRefreshCamFeeder(self.rdb, 'wilsat', 'archimedes', 'http://fake.com/image.jpg', 10,
                                        0)

    def tearDown(self):
        pass

    @patch('grequests.get')
    @patch('grequests.map')
    def test_invalid_fps_init_raises(self, map_patch, get_patch):
        """ Ensures that trying to initialize with an invalid FPS raises an exception. """
        try:
            self.cf = ImageRefreshCamFeeder(self.rdb, 'wilsat', 'archimedes', 'http://fake.com/image.jpg', 0,
                                            0)
        except:
            pass
        else:
            self.fail("Exception was expected")


class TestRun(FeederTestBase):
    """
    Tests by letting the gevent greenlets run.
    """

    def setUp(self):
        self.rdb = mock_strict_redis_client()
        self.img = open('data/img.jpg', 'rb').read()
        self.cf = ImageRefreshCamFeeder(self.rdb, 'wilsat', 'archimedes', 'http://fake.com/image.jpg', 10000, 0)

        # Start running the greenlet.
        self.cf.start()
        self._g = self.cf._g

    @patch('grequests.get')
    @patch('grequests.map')
    def test_active_flow(self, map_patch, get_patch):
        """
        Ensures that it seems to request frames and that it puts them on redis as expected.
        :return:
        """

        # Mock grequests get
        response = requests.Response()
        response.status_code = 200
        get_patch.return_value = response

        # Mock grequests map
        response = requests.Response()
        response.status_code = 200
        response.raw = io.BytesIO(b"1234567890"*12)
        map_patch.return_value = [response]

        # Should activate
        self.rdb.setex('wilsat:cams:archimedes:active', 10, 1)
        gevent.sleep(0.1)

        # Get current number of frames
        frames_first = self.cf._frames_this_cycle

        # Let it run
        gevent.sleep(0.1)

        # Ensure that the number of frames has incrased
        frames_second = self.cf._frames_this_cycle
        self.assertGreater(frames_second, frames_first)

        # Ensure that mock has been called several times.
        self.assertGreater(map_patch.call_count, 5)

        # Ensure that the frames are being placed into redis.
        self.assertEquals(self.rdb.get('wilsat:cams:archimedes:lastframe'), b'1234567890'*12)

    def tearDown(self):
        gevent.kill(self._g)