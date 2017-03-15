import unittest
import redis
from unipath import Path
import sys


sys.path.insert(0, Path(__file__).parent.parent.absolute())
from feeder import config


class FeederTestBase(unittest.TestCase):
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
        if cls is not FeederTestBase and cls.setUp is not FeederTestBase.setUp:
            orig_setUp = cls.setUp

            def setUpOverride(self, *args, **kwargs):
                FeederTestBase.setUp(self)
                return orig_setUp(self, *args, **kwargs)

            cls.setUp = setUpOverride

    def setUp(self):
        """
        :return:
        Do custom setUp.
        """

        # Connect to the redis instance.
        self.rdb = redis.StrictRedis(host=config.REDIS_HOST, port=config.REDIS_PORT, db=config.REDIS_DB)

    def tearDown(self):
        """
        # TODO: Not sure if that one is called.
        :return:
        """
        pass
