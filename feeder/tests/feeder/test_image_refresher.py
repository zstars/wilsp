import io
import os
import unittest
from unittest.mock import patch

import gevent
import requests
from mockredis import mock_strict_redis_client

from tests.base import FeederTestBase
from feeder.image_refresher import ImageRefreshCamFeeder, FrameGrabbingException

# Fix path
abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(os.path.join(dname, '..'))


class TestBasic(FeederTestBase):

    def setUp(self):
        """
        Test that we can grab a single frame and that apprently it returns what we expect.
        :return:
        """

        self.rdb = mock_strict_redis_client()
        self._img_file = open('data/img.jpg', 'rb')
        self.img = self._img_file.read()
        self.cf = ImageRefreshCamFeeder(self.rdb, 'wilsat', 'archimedes', 'http://fake.com/image.jpg', 10, 0)

        # We mock requests.get calls.
        self.get_patcher = patch('requests.get')
        self.get_mock = self.get_patcher.start()
        self.addCleanup(self.get_patcher.stop)

        # Ensure that the request returns
        fixed_response = requests.Response()
        fixed_response.status_code = 200
        fixed_response.raw = io.BytesIO(b"1234567890"*12)
        self.get_mock.return_value = fixed_response

    def tearDown(self):
        self._img_file.close()

    def test_grab_frame(self):
        frame = self.cf._grab_frame()
        self.assertIsNotNone(frame)
        self.assertGreater(len(frame), 3)
        self.assertTrue(frame.startswith(b'1234567890'))


class TestBasicException(FeederTestBase):
    """
    Test that if the webcam returns an exception an exception is indeed thrown by the grabber.
    """

    def setUp(self):
        self.rdb = mock_strict_redis_client()
        self.img = open('data/img.jpg', 'rb').read()
        self.cf = ImageRefreshCamFeeder(self.rdb, 'wilsat', 'archimedes', 'http://fake.com/image.jpg', 10, 0)

        # We mock erequests.async.get calls.
        self.get_patcher = patch('requests.get')
        self.get_mock = self.get_patcher.start()
        self.addCleanup(self.get_patcher.stop)

        fixed_response = requests.Response()
        fixed_response.status_code = 404
        fixed_response.raw = io.BytesIO(b"1234567890"*12)
        self.get_mock.return_value = fixed_response

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
    """
    Regression test: Ensure that trying to initialize the grabber with an invalid FPS will raise an exception.
    """

    def setUp(self):
        self.rdb = mock_strict_redis_client()
        self.img = open('data/img.jpg', 'rb').read()
        self.cf = ImageRefreshCamFeeder(self.rdb, 'wilsat', 'archimedes', 'http://fake.com/image.jpg', 10,
                                        0)

    def tearDown(self):
        pass

    @patch('requests.get')
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
    Complex tests: Lets the frames run.
    """

    def setUp(self):
        self.rdb = mock_strict_redis_client()
        self.img = open('data/img.jpg', 'rb').read()
        self.cf = ImageRefreshCamFeeder(self.rdb, 'wilsat', 'archimedes', 'http://fake.com/image.jpg', 10000, 0)

        # We mock erequests.async.get calls.
        self.get_patcher = patch('requests.get')
        self.get_mock = self.get_patcher.start()
        self.addCleanup(self.get_patcher.stop)

        fixed_response = requests.Response()
        fixed_response.status_code = 200
        fixed_response.raw = io.BytesIO(b"1234567890"*12)
        self.get_mock.return_value = fixed_response

        # Start running the greenthreads.
        self.cf.start()
        self._g = self.cf._g

    def test_greenlets_running(self):
        """
        Ensure that the two greenlets in the internal _g dictionary seem to be alive.
        :return:
        """
        g = self.cf._g

        self.assertEquals(2, len(g))

        for gl in g:
            started_and_not_failed = bool(gl)
            self.assertTrue(started_and_not_failed)

    def test_active_flow(self):
        """
        Ensures that it seems to request frames and that it puts them on redis as expected.
        :return:
        """

        # Should activate
        self.rdb.setex('wilsat:cams:archimedes:active', 10, 1)
        gevent.sleep(0.1)

        # Get current number of frames
        frames_first = self.cf._frames_this_cycle

        # Let it run
        gevent.sleep(0.1)

        # Ensure that the number of frames has increased
        frames_second = self.cf._frames_this_cycle
        self.assertGreater(frames_second, frames_first, "Number of rendered frames should increase steadily")

        # Ensure that mock (requests.get) has been called several times.
        self.assertGreater(self.get_mock.call_count, 5)

        # Ensure that the frames are being placed into redis.
        self.assertEquals(self.rdb.get('wilsat:cams:archimedes:lastframe'), b'1234567890'*12)

    def tearDown(self):
        for g in self._g:
            gevent.kill(g)

if __name__ == '__main__':
    unittest.main()