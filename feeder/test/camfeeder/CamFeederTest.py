import os
import hashlib

from mockredis import mock_strict_redis_client
from FeederTestBase import FeederTestBase
from camfeeder.CamFeeder import CamFeeder

# Fix the working path
abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(os.path.join(dname, '..'))


class TestBasic(FeederTestBase):

    def setUp(self):
        rdb = mock_strict_redis_client()
        self.img = open('data/img.jpg', 'rb').read()
        self.cf = CamFeeder(rdb, 'wilsat', 'archimedes', '', 10, 0)

    def tearDown(self):
        pass

    def test_pass(self):
        pass

    def test_rotates(self):
        r = self.cf._rotated(self.img, 80.5)
        r_md5 = hashlib.md5(r).hexdigest()
        self.assertIsNotNone(r)
        self.assertEquals('d27e3eea81060a69e9d62d2343fe5bcb', r_md5)