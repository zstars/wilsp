import io
import os
from unittest.mock import patch

import eventlet
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

        # We mock erequests.async.get calls.
        self.get_patcher = patch('erequests.async.get')
        self.get_mock = self.get_patcher.start()
        self.addCleanup(self.get_patcher.stop)

        fixed_response = requests.Response()
        fixed_response.status_code = 200
        fixed_response.raw = io.BytesIO(b"1234567890"*12)
        self.get_mock.return_value.send.return_value = fixed_response

    def tearDown(self):
        pass

    def test_grab_frame(self):
        frame = self.cf._grab_frame()
        self.assertIsNotNone(frame)
        self.assertGreater(len(frame), 3)
        self.assertTrue(frame.startswith(b'1234567890'))


class TestBasicException(FeederTestBase):

    def setUp(self):
        self.rdb = mock_strict_redis_client()
        self.img = open('data/img.jpg', 'rb').read()
        self.cf = ImageRefreshCamFeeder(self.rdb, 'wilsat', 'archimedes', 'http://fake.com/image.jpg', 10, 0)

        # We mock erequests.async.get calls.
        self.get_patcher = patch('erequests.async.get')
        self.get_mock = self.get_patcher.start()
        self.addCleanup(self.get_patcher.stop)

        fixed_response = requests.Response()
        fixed_response.status_code = 404
        fixed_response.raw = io.BytesIO(b"1234567890"*12)
        self.get_mock.return_value.send.return_value = fixed_response

    def tearDown(self):
        pass

    def test_frame_grabbing_exception(self):
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

    @patch('erequests.async.get')
    def test_invalid_fps_init_raises(self, get_patch):
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

        # We mock erequests.async.get calls.
        self.get_patcher = patch('erequests.async.get')
        self.get_mock = self.get_patcher.start()
        self.addCleanup(self.get_patcher.stop)

        fixed_response = requests.Response()
        fixed_response.status_code = 200
        fixed_response.raw = io.BytesIO(b"1234567890"*12)
        self.get_mock.return_value.send.return_value = fixed_response

        # Start running the greenthreads.
        self.cf.start()
        self._g = self.cf._g

    def test_active_flow(self):
        """
        Ensures that it seems to request frames and that it puts them on redis as expected.
        :return:
        """

        # Should activate
        self.rdb.setex('wilsat:cams:archimedes:active', 10, 1)
        eventlet.sleep(0.1)

        # Get current number of frames
        frames_first = self.cf._frames_this_cycle

        # Let it run
        eventlet.sleep(0.1)

        # Ensure that the number of frames has incrased
        frames_second = self.cf._frames_this_cycle
        self.assertGreater(frames_second, frames_first)

        # Ensure that mock has been called several times.
        self.assertGreater(self.get_mock.return_value.send.call_count, 5)

        # Ensure that the frames are being placed into redis.
        self.assertEquals(self.rdb.get('wilsat:cams:archimedes:lastframe'), b'1234567890'*12)

    def tearDown(self):
        for g in self._g:
            eventlet.kill(g)