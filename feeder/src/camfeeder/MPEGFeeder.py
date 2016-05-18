import gevent


class MPEGFeeder(object):
    """
    The MPEG feeder will control a ffmpeg instance and rely on the 'forward' server to publish
    the stream in REDIS.
    """

    def __init__(self, mjpeg_source):
        self._g = []

    def _run(self):
        pass

    def start(self):
        g = gevent.Greenlet(self._run)
        g.start()
        self._g.append(g)