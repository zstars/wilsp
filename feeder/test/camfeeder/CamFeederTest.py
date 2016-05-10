import os
import hashlib

import gevent
import redis
from mockredis import mock_strict_redis_client
from FeederTestBase import FeederTestBase
from camfeeder.CamFeeder import CamFeeder

# Fix the working path
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
        r = self.cf._rotated(self.img, 80.5)
        r_md5 = hashlib.md5(r).hexdigest()
        self.assertIsNotNone(r)
        self.assertEquals('d27e3eea81060a69e9d62d2343fe5bcb', r_md5)

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
            gevent.sleep(0.01)

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
        gevent.sleep(0.1)

        # Should start inactive.
        self.assertEquals(0, self.cf._times_active)
        self.assertEquals(1, self.cf._times_inactive)

        # Should activate
        self.rdb.setex('wilsat:cams:archimedes:active', 10, 1)
        gevent.sleep(0.1)
        self.assertEquals(1, self.cf._times_active)
        self.assertEquals(1, self.cf._times_inactive)

        # Should deactivate again
        self.rdb.delete('wilsat:cams:archimedes:active')
        gevent.sleep(0.1)
        self.assertEquals(1, self.cf._times_active)
        self.assertEquals(2, self.cf._times_inactive)

    def tearDown(self):
        gevent.kill(self._g)