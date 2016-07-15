import io
import os
from unittest.mock import patch

import eventlet
import requests
from mockredis import mock_strict_redis_client

from test.FeederTestBase import FeederTestBase
from camfeeder.MPEGFeeder import MPEGFeeder

# Fix the working path
abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(os.path.join(dname, '..'))


class TestMPEGCamFeeder(FeederTestBase):

    def setUp(self):
        self.rdb = mock_strict_redis_client()
        self.img = open('data/img.jpg', 'rb').read()
        self.cf = MPEGFeeder(self.rdb, 'archimedes', 'http://fake.com/video.mjpeg')

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

    def test_pass(self):
        pass