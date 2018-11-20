"""
This feeder module will extract a stream in the h264 format using ffmpeg and feed it into individual redis-frames.
"""


import traceback

import gevent
import re
from gevent import subprocess
import redis


class H264ToFramesFeeder(object):
    """
    The H264 feeder will control a ffmpeg instance, transcode it into individual frames, direct them through a stdout
    pipe, and push them into redis as individual frames.
    Requires an h264 source webcam.
    """

    def __init__(self, rdb: redis.StrictRedis, redis_prefix: str, cam_name: str, h264_source: str, ffmpeg_bin: str):
        self._g = []
        self._cam_name = cam_name
        self._h264_source = h264_source
        self._rdb = rdb
        self._redis_prefix = redis_prefix

        self._ffmpeg_bin = ffmpeg_bin

    def _run(self):

        # Eventlet cannot greenify subprocess, so we will call ffmpeg from a different thread.
        def run_ffmpeg():

            # Note: For now this is just for testing.
            ffmpeg_input_parameters = ['-r', '1', '-f', 'mjpeg', '-i', 'https://cams.weblab.deusto.es/cams/cams/arduino1c1/mjpeg']
            ffmpeg_output_parameters = ['-r', '1', '-f', 'mjpeg']

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

            while True:
                try:

                    # Read the a first packet.
                    packet = p.stdout.read(2048)
                    n = len(packet)

                    print("Retrieved {} bytes".format(n))


                    # Previously, this was just a channel, so we didn't need to split the frames. Now we do, however.
                    # packet = p.stdout.read(2048)
                    # n = len(packet)
                    #
                    # if n > 0:
                    #     # It is noteworthy that, as of now, the packets are a stream. An alternative would be to split the frames
                    #     # here. This is more efficient from a networking perspective, but it probably transfers some work
                    #     # to the Redis listeners.
                    #     self._rdb.publish(redis_channel, packet)
                    #
                    # elif n != 2048:
                    #     return 2
                except ValueError as ex:
                    return 1

        run_ffmpeg()

        print("H.264 to Frames greenlet is OUT")

    def start(self):
        g = gevent.spawn(self._run)
        self._g.append(g)

