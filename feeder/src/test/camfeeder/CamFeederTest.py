import os
import hashlib

import eventlet
import redis
import time
from mockredis import mock_strict_redis_client
from camfeeder.CamFeeder import CamFeeder

from unittest.mock import patch

# Fix the working path
from test.FeederTestBase import FeederTestBase

abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(os.path.join(dname, '..'))


class TestBasic(FeederTestBase):

    def setUp(self):
        self.rdb = mock_strict_redis_client()
        self.img = open('data/img.jpg', 'rb').read()
        self.cf = CamFeeder(self.rdb, 'wilsat', 'archimedes', '', 10, 0)

    def tearDown(self):
        pass

    def test_pass(self):
        pass

    def test_rotates(self):
        """
        Ensure standard rotation works.
        :return:
        """
        r = self.cf._rotated(self.img, 80)
        r_md5 = hashlib.md5(r).hexdigest()
        self.assertIsNotNone(r)
        # TODO: Add image comparison that does not break.
        # self.assertEquals('ff7fcdfb99a4391b2b1df3898045604b', r_md5)

    def test_rotates_nothing_when_0(self):
        """
        Ensure if rotation is 0 the image does not change.
        :return:
        """
        r_md5_before = hashlib.md5(self.img).hexdigest()
        r = self.cf._rotated(self.img, 0)
        self.assertIsNotNone(r)
        r_md5_after = hashlib.md5(r).hexdigest()
        self.assertEquals(r_md5_before, r_md5_after)

    def test_put_frame(self):
        self.cf._frames_this_cycle = 0
        self.assertEquals(0, self.cf._frames_this_cycle)
        frame = b'abcd'
        self.cf._put_frame(frame)
        self.assertEquals(frame, self.rdb.get('wilsat:cams:archimedes:lastframe'))
        self.assertEquals(1, self.cf._frames_this_cycle)

    def test_check_active(self):
        # Set active flag:
        self.rdb.setex('wilsat:cams:archimedes:active', 10, 1)
        self.cf._check_active()
        self.assertTrue(self.cf._active)  # We are marked as active

        self.rdb.delete('wilsat:cams:archimedes:active')
        self.cf._check_active()
        self.assertFalse(self.cf._active)  # We are marked as inactive

    def test_get_fps(self):
        """
        Checks the FPS calculations.
        :return:
        """
        self.cf._frames_this_cycle = 200
        curtime = time.time()
        self.cf._active_since = curtime - 10
        fps = self.cf.get_current_fps()

        max_expected_fps = 200 / 10
        min_expected_fps = 200 / 12  # Two seconds elapsed at most while calculating.
        self.assertTrue(min_expected_fps <= fps <= max_expected_fps)

    def test_get_fps_when_0(self):
        """
        Check that it returns 0 and does not explode if elapsed is 0.
        :return:
        """
        self.cf._active_since = time.time()
        fps = self.cf.get_current_fps()
        self.assertEquals(0, fps)


class ConcreteCamFeeder(CamFeeder):
    """
    Concrete CamFeeder for testing.
    """

    def __init__(self, rdb: redis.StrictRedis, redis_prefix: str, cam_name: str, url: str, max_fps: int,
                 rotation: float = None):
        super().__init__(rdb, redis_prefix, cam_name, url, max_fps, rotation)
        self._times_active = 0
        self._times_inactive = 0

    def _run_until_inactive(self):
        self._times_active += 1
        while self._active:
            self._check_active()
            self._frames_this_cycle += 1
            eventlet.sleep(0.01)

    def _wait_until_active(self):
        self._times_inactive += 1
        super()._wait_until_active()


class TestRun(FeederTestBase):

    def setUp(self):
        self.rdb = mock_strict_redis_client()
        self.img = open('data/img.jpg', 'rb').read()
        self.cf = ConcreteCamFeeder(self.rdb, 'wilsat', 'archimedes', '', 10, 0)

        # Start running the greenlet.
        self.cf.start()
        self._g = self.cf._g

    def test_active_flow(self):
        """
        Ensures that it switches between the active and inactive states predictably,
        and that the _wait_until_active and _run_until_inactive execute as they should.
        :return:
        """

        # Give it some execution time.
        eventlet.sleep(0.1)

        # Should start inactive.
        self.assertEquals(0, self.cf._times_active)
        self.assertEquals(1, self.cf._times_inactive)

        # Should activate
        self.rdb.setex('wilsat:cams:archimedes:active', 10, 1)
        eventlet.sleep(0.1)
        self.assertEquals(1, self.cf._times_active)
        self.assertEquals(1, self.cf._times_inactive)

        # Should deactivate again
        self.rdb.delete('wilsat:cams:archimedes:active')
        eventlet.sleep(0.1)
        self.assertEquals(1, self.cf._times_active)
        self.assertEquals(2, self.cf._times_inactive)

        # Should activate
        self.rdb.setex('wilsat:cams:archimedes:active', 10, 1)
        eventlet.sleep(0.1)

    @patch.object(ConcreteCamFeeder, 'STATS_PUSH_WAIT', 0.1)
    def test_stats_pusher(self):

        CamFeeder.STATS_PUSH_WAIT = 0.01

        # Should activate
        self.rdb.setex('wilsat:cams:archimedes:active', 10, 1)
        eventlet.sleep(0.3)

        cycle_frames = self.rdb.get('wilsat:cams:archimedes:stats:cycle_frames')
        cycle_elapsed = self.rdb.get('wilsat:cams:archimedes:stats:cycle_elapsed')

        self.assertIsNotNone(cycle_frames)
        self.assertIsNotNone(cycle_elapsed)

        cycle_frames = int(cycle_frames)
        cycle_elapsed = float(cycle_elapsed)

        self.assertGreater(cycle_frames, 10)
        self.assertGreater(cycle_elapsed, 0.1)

    def tearDown(self):
        for g in self._g:
            eventlet.kill(g)