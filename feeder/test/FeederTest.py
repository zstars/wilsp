import unittest
import redis

from run import REDIS_HOST, REDIS_PORT, REDIS_DB


class FeederTest(unittest.TestCase):
    """
    Common test base class for Feeder tests, which can start servers.
    Based on: https://gist.github.com/twolfson/13f5f5784f67fd49b245
    """

    @classmethod
    def setUpClass(cls):
        """
        Runs the setUp of classes that inherit from this one.
        :return:
        """
        if cls is not FeederTest and cls.setUp is not FeederTest.setUp:
            orig_setUp = cls.setUp

            def setUpOverride(self, *args, **kwargs):
                FeederTest.setUp(self)
                return orig_setUp(self, *args, **kwargs)

            cls.setUp = setUpOverride

    def setUp(self):
        """
        :return:
        Do custom setUp.
        """

        # Connect to the redis instance.
        self.rdb = redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB)

    def tearDown(self):
        """
        # TODO: Not sure if that one is called.
        :return:
        """
        pass
