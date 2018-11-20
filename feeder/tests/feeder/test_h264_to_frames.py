import os
import unittest
from unittest.mock import patch, PropertyMock

from mockredis import mock_strict_redis_client

from feeder.h264_to_frames import H264ToFramesFeeder
from tests.base import FeederTestBase

# Fix the working path
abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(os.path.join(dname, '..'))


class TestH264ToFramesCamFeeder(FeederTestBase):

    def setUp(self):
        self.rdb = mock_strict_redis_client()
        self.img = open('data/img.jpg', 'rb').read()
        self.cf = H264ToFramesFeeder(self.rdb, 'wilsat', 'archimedes', 'http://fake.com/video.h264', 'ffmpeg')

        # We mock the subprocess.Popen call to provide our own test stream
        self.popen_patcher = patch('feeder.h264_to_frames.subprocess.Popen')
        self.popen_mock = self.popen_patcher.start()
        self.addCleanup(self.popen_patcher.stop)

        self.test_file = open("data/stream.h264", "rb")
        type(self.popen_mock.return_value).stdout = PropertyMock(return_value=self.test_file)

    def tearDown(self):
        self.test_file.close()

    def test_pass(self):
        pass

    def test_frames_on_redis(self):
        """
        Tests whether frames are being placed into redis.
        :return:
        """

        # TODO: Test to be implemented.

        # # Let it run for a while.
        # self.cf.start()
        #
        # # Wait for the greenthread to finish.
        # for g in self.cf._g:
        #     g.join()
        #
        # frame = self.rdb.get('wilsat:cams:archimedes:lastframe')
        #
        # print("Frame is: {}".format(frame))
        #
        # assert(False)

    # def test_messages_on_redis(self):
    #     """
    #     Tests whether messages are being published into redis.
    #     :return:
    #     """
    #
    #     # Let it run for a while.
    #     self.cf.start()
    #
    #     # Wait for the greenthread to finish.
    #     for g in self.cf._g:
    #         g.join()
    #
    #     expected_channel_name = "archimedes/h264"
    #     messages = self.rdb.pubsub[expected_channel_name]
    #
    #     self.assertIsNotNone(messages)
    #     self.assertGreater(len(messages), 0)
    #     self.assertGreater(len(messages[0]), 10)


if __name__ == '__main__':
    unittest.main()
