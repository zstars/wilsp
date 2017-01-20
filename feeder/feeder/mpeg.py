import subprocess
import gevent


class MPEGFeeder(object):
    """
    The MPEG feeder will control a ffmpeg instance, direct it through stdout pipe, and push it to redis.
    the stream in REDIS.
    """

    def __init__(self, rdb, cam_name, mjpeg_source, ffmpeg_bin):
        self._g = []
        self._cam_name = cam_name
        self._mjpeg_source = mjpeg_source
        self._rdb = rdb
        self._ffmpeg_bin = ffmpeg_bin

    def _run(self):
        # Redis channel
        redis_channel = '{}/mpeg'.format(self._cam_name)

        # For debugging only.
        # self._mjpeg_source = "http://cams.weblab.deusto.es/webcam/fishtank1/video.mjpeg"

        ffmpeg_command = [self._ffmpeg_bin, '-r', '30', '-f', 'mjpeg', '-i', self._mjpeg_source, '-f', 'mpeg1video', '-b', '800k', '-r', '30', "pipe:1"]

        print("Running FFMPEG command: {}".format(ffmpeg_command))

        # Eventlet cannot "greenify" subprocess, so we will run it in a different thread through an eventlet threadpool.

        def run_ffmpeg():
            p = subprocess.Popen(ffmpeg_command, stdin=subprocess.PIPE, stdout=subprocess.PIPE)

            while True:
                # TODO: Consider whether we should read in some other way.

                try:
                    packet = p.stdout.read(2048)
                    n = len(packet)
                    if len(packet) > 0:
                        self._rdb.publish(redis_channel, packet)
                    elif n != 2048:
                        return 2
                except ValueError as ex:
                    return 1

        run_ffmpeg()

        print("MPEG greenlet is OUT")

    def start(self):
        g = gevent.spawn(self._run)
        self._g.append(g)
