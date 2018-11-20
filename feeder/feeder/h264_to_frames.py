"""
This feeder module will extract a stream in the h264 format using ffmpeg and feed it into individual redis-frames.

TO-DO: Verify that we can recover from errors.
"""


import traceback

import gevent
import re
from gevent import subprocess
import redis

from feeder.base import CamFeeder


class H264ToFramesFeeder(CamFeeder):
    """
    The H264 feeder will control a ffmpeg instance, transcode it into individual frames, direct them through a stdout
    pipe, and push them into redis as individual frames.
    Requires an h264 source webcam.
    """

    def __init__(self, rdb: redis.StrictRedis, redis_prefix: str, cam_name: str, h264_source: str, ffmpeg_bin: str):
        super(H264ToFramesFeeder, self).__init__(rdb, redis_prefix, cam_name, None, None, 0)

        self._g = []
        self._cam_name = cam_name
        self._h264_source = h264_source
        self._rdb = rdb
        self._redis_prefix = redis_prefix

        self._ffmpeg_bin = ffmpeg_bin

    def _run_until_inactive(self):
        """
        TO-DO: This is unused. It's abstract in the base classs but doesn't really make full sense with this
        kind of ffmpeg source.
        :return:
        """
        raise NotImplementedError()

    def _run(self):

        # Eventlet cannot greenify subprocess, so we will call ffmpeg from a different thread.
        def run_ffmpeg():

            # Note: Those are for testing.
            # ffmpeg_input_parameters = ['-r', '10', '-f', 'mjpeg', '-i', 'https://cams.weblab.deusto.es/cams/cams/arduino1c1/mjpeg']

            # Those are for real:
            ffmpeg_input_parameters = ['-i', self._h264_source]
            ffmpeg_output_parameters = ['-f', 'mjpeg']

            ffmpeg_command = [self._ffmpeg_bin, *ffmpeg_input_parameters, *ffmpeg_output_parameters, "pipe:1"]

            print("Running FFMPEG command: {}".format(ffmpeg_command))

            p = subprocess.Popen(ffmpeg_command, stdin=subprocess.PIPE, stderr=subprocess.PIPE, stdout=subprocess.PIPE)

            def myreadlines(f, newline):
                """
                Custom readlines to use a specific terminator: ffmpeg uses ^M (\r) to separate the line with the stats.
                :param f:
                :param newline:
                :return:
                """
                buf = bytes()
                while True:
                    while newline in buf:
                        pos = buf.index(newline)
                        yield buf[:pos]
                        buf = buf[pos + len(newline):]
                    chunk = f.read(50)  # 50 bytes buffer: Appropriate for the amount of data we tend to receive.
                    if not chunk or len(chunk) <= 0:
                        yield buf
                        break
                    buf += chunk

            def handle_stderr(err):
                """
                Handles the stderr stream, which in the case of ffmpeg does not only contain errors, but stats.
                We will periodically push the fps to redis. (Trying to update only every so often to decrease the potential
                impact on performance).
                :param err:
                :param queue:
                :return:
                """
                base_key = "{}:cams:{}:stats:".format(self._redis_prefix, self._cam_name)
                fps_key = base_key+"fps"

                fps_list = []
                for line in myreadlines(err, b'\r'):
                    try:
                        # Try to extract FPS
                        results = re.findall(r"fps=\s([0-9]+)\s", line.decode('utf-8'))
                        if len(results) > 0:
                            fps = int(results[0])
                            fps_list.append(fps)

                            if len(fps_list) >= 5:
                                avg = sum(fps_list) / len(fps_list)
                                fps_list = []
                                self._rdb.setex(fps_key, 30, avg)
                                # print("FPS: {}".format(avg))
                        else:
                            pass
                            # print("FPS not found in: {}".format(line))
                    except:
                        traceback.print_exc()
                err.close()

            stderr_handler = gevent.spawn(handle_stderr, p.stderr)
            self._g.append(stderr_handler)

            packet = bytes()
            starting = True
            it = 0  # Indicates the bytes we have examined.
            while True:
                try:

                    # Read quite a few bytes.
                    packet += bytes(p.stdout.read(2048))
                    n = len(packet)

                    if starting:
                        # If we are just starting a JPEG, we should find 0xFF 0xD8 0xFF in the beginning.
                        if n < 3:
                            continue

                        # Check whether we are indeed starting a JPG.
                        if packet[0] == 0xFF and packet[1] == 0xD8 and packet[2] == 0xFF:
                            # yes
                            starting = False
                        else:
                            # Unexpected. Does not seem to be a JPG.
                            return 2

                    # Parse the incoming bytes to keep seeking for FF D9 (end of JPEG).
                    while it < n - 1:  # n - 1 so that we ensure the header will be visible at once.
                        # Full JPG found.
                        if packet[it] == 0xFF and packet[it+1] == 0xD9:
                            # We have a JPG frame now.
                            frame = packet[:it+2]

                            self._put_frame(frame)

                            # For debugging purposes.
                            # f = open("out.jpg", "wb")
                            # f.write(frame)
                            # f.close()

                            # Clear the frame from the packet buffer so that we can go on with the next frame.
                            packet = packet[it+2:]
                            it = 0
                            starting = True
                            break
                        else:
                            it += 1

                except ValueError as ex:
                    return 1

        run_ffmpeg()

        print("H.264 to Frames greenlet is OUT")

    def start(self):
        g = gevent.spawn(self._run)
        self._g.append(g)

