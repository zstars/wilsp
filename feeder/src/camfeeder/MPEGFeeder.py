import subprocess

import gevent
import config


class MPEGFeeder(object):
    """
    The MPEG feeder will control a ffmpeg instance, direct it through stdout pipe, and push it to redis.
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
        self._forward_url = "pipe:1"
        self._mjpeg_source = "http://cams.weblab.deusto.es/webcam/fishtank1/video.mjpeg"

        ffmpeg_command = ['/opt/local/bin/ffmpeg', '-r', '30', '-i', self._mjpeg_source, '-f', 'mpeg1video', '-b', '800k', '-r', '30', self._forward_url]

        print("Running FFMPEG command: {}".format(ffmpeg_command))

        p = subprocess.Popen(ffmpeg_command, stdin=subprocess.PIPE, stdout=subprocess.PIPE)

        f = open("test_fs.mjpeg", "wb")
        while True:
            packet = p.stdout.readline()
            f.write(packet)

        print("MPEG greenlet is OUT")

    def start(self):
        g = gevent.Greenlet(self._run)
        g.start()
        self._g.append(g)
