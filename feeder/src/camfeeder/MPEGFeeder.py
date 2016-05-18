import subprocess

import gevent
import config


class MPEGFeeder(object):
    """
    The MPEG feeder will control a ffmpeg instance and rely on the 'forward' server to publish
    the stream in REDIS.
    """

    def __init__(self, cam_name, mjpeg_source):
        self._g = []
        self._cam_name = cam_name
        self._mjpeg_source = mjpeg_source
        self._forward_url = config.FORWARD_SERVER_URL + "/inputs/" + cam_name + "/"

    def _run(self):
        # Run ffmpeg to forward from the camera to the forwarder.

        # For debugging only.
        # sself._forward_url = "output_test.mpeg"
        self._mjpeg_source = "output_test.mpeg"

        ffmpeg_command = ['/opt/local/bin/ffmpeg', '-r', '30', '-i', self._mjpeg_source, '-f', 'mpeg1video', '-b', '800k', '-r', '15', self._forward_url]

        print("Running FFMPEG command: {}".format(ffmpeg_command))

        p = subprocess.Popen(ffmpeg_command, stdin=subprocess.PIPE, stdout=subprocess.PIPE)

        while True:
            retval = p.poll()
            if retval is None:
                break
            out, _ = p.communicate(None, 1)

        print("MPEG greenlet is OUT")

    def start(self):
        g = gevent.Greenlet(self._run)
        g.start()
        self._g.append(g)
