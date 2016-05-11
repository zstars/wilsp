import os
import hashlib
from unittest.mock import patch, MagicMock, PropertyMock

import gevent
import grequests
import io
import redis
import time

import requests
from PIL import Image
from mockredis import mock_strict_redis_client
from test.FeederTestBase import FeederTestBase
from camfeeder.CamFeeder import CamFeeder

# Fix the working path
from camfeeder.ImageRefreshCamFeeder import FrameGrabbingException
from camfeeder.MJPEGCamFeeder import MJPEGCamFeeder

abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(os.path.join(dname, '..'))


class ResponseMock(MagicMock):

    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)
        self.status_code = 200


class TestBasic(FeederTestBase):

    def setUp(self):
        self.rdb = mock_strict_redis_client()
        self.cf = MJPEGCamFeeder(self.rdb, 'wilsat', 'archimedes', 'http://fake.com/image.mjpg', 10, 0)

        # We mock grequests.get calls.
        self.get_patcher = patch('grequests.get')
        self.get_mock = self.get_patcher.start()
        self.addCleanup(self.get_patcher.stop)

        fixed_response = requests.Response()
        fixed_response.status_code = 200
        fixed_response.headers['content-type'] = 'multipart/x-mixed-replace;boundary=--video boundary--'
        fixed_response.raw = io.FileIO('data/example.mjpeg', 'rb')
        type(self.get_mock.return_value.send.return_value).response = PropertyMock(return_value=fixed_response)

        # Advanced DARK MAGICKS. Would be nice to find a less contrived way to do this.
        # response_intra_mock = MagicMock()
        # type(response_intra_mock).status_code = PropertyMock(return_value=200)
        # type(self.get_mock.return_value.send.return_value).response = PropertyMock(return_value=response_intra_mock)

    def test_mocking_scheme(self):

        idx = 0
        for idx, line in enumerate(grequests.get().send().response.iter_lines()):
            self.assertIsNotNone(line)

        self.assertGreater(idx, 0)

    def test_start_streaming_request(self):
        self.cf._start_streaming_request()
        self.assertIsNotNone(self.cf._request_response_boundary)
        self.assertEquals('--video boundary--', self.cf._request_response_boundary)

    def test_parse_headers(self):
        self.cf._start_streaming_request()
        headers = self.cf._parse_headers()
        self.assertEquals(3, len(headers))
        print(headers)

    def test_parse_next_image(self):
        self.cf._start_streaming_request()

        # Parse first image from the stream
        img_bytes, date = self.cf._parse_next_image()

        self.assertIsNotNone(img_bytes)
        self.assertGreater(len(img_bytes), 100)

        # Try to check whether it's a valid JPEG.
        sio_in = io.BytesIO(img_bytes)
        img = Image.open(sio_in)
        self.assertIsNotNone(img)

        # Parse the second one
        img_bytes, date = self.cf._parse_next_image()

        self.assertIsNotNone(img_bytes)
        self.assertGreater(len(img_bytes), 100)

        # Try to check whether it's a valid JPEG.
        sio_in = io.BytesIO(img_bytes)
        img = Image.open(sio_in)
        self.assertIsNotNone(img)


        open('remove.jpg', 'wb').write(img_bytes)

    def tearDown(self):
        pass

    def test_pass(self):
        pass

    def test_start_streaming(self):
        self.cf._start_streaming_request()


class TestRun(FeederTestBase):
    """
    Tests by letting the gevent greenlets run.
    """

    def setUp(self):
        self.rdb = mock_strict_redis_client()
        self.cf = MJPEGCamFeeder(self.rdb, 'wilsat', 'archimedes', 'http://fake.com/image.mjpg', 10000, 0)

        # Start running the greenlet.
        self.cf.start()
        self._g = self.cf._g

    def test_pass(self):
        pass

    def tearDown(self):
        gevent.kill(self._g)