import unittest

import gevent
from tests.base import FeederTestBase

from old import run
from old.run import REDIS_PREFIX


class TestWatchdog(FeederTestBase):

    def setUp(self):
        run.run()  # This starts running the greenlets but does not block.

    def tearDown(self):
        pass

    def test_pass(self):
        pass

    def test_watchdog_set(self):
        """
        Test that after working for some time, the watchdog is set.
        :return:
        """
        gevent.sleep(2)

        alive = self.rdb.get('{0}:feeder:alive'.format(REDIS_PREFIX))
        self.assertIsNotNone(alive)

    def test_watchdog_disappears_after_awhile(self):
        """
        Ensures that the watchdog disappears if we kill and wait.
        :return:
        """
        for g in run.greenlets:  # type: gevent.Greenlet
            g.kill()

        gevent.sleep(6)

        alive = self.rdb.get('{0}:feeder:alive'.format(REDIS_PREFIX))
        self.assertIsNone(alive)


class TestFrames(FeederTestBase):

    def setUp(self):
        run.run()  # This starts running the greenlets but does not block.

    def tearDown(self):
        pass

    def test_pass(self):
        pass

    def test_frames_exist(self):
        """
        Test that after working for some time, the watchdog is set.
        :return:
        """
        gevent.sleep(2)

        a1 = self.rdb.get('{0}:cams:archimedes1:lastframe'.format(REDIS_PREFIX))
        self.assertIsNotNone(a1)

        self.assertGreater(len(a1), 1000)

    def test_frames_disappear(self):
        """
        Test that after working for some time, the frames disappear.
        :return:
        """
        gevent.sleep(2)

        for g in run.greenthreads:  # type: gevent.Greenlet
            g.kill()

        gevent.sleep(11)

        a1 = self.rdb.get('{0}:cams:archimedes1:lastframe'.format(REDIS_PREFIX))
        self.assertIsNone(a1)

if __name__ == "__main__":
    unittest.main()
