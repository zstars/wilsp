import gevent
import redis
from gevent import monkey

monkey.patch_all()

import os
import subprocess
import io

import psutil

from feeder import config

abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(dname)

print(os.getcwd())

#
# This script is a work in progress.
#

benchmark_runner_greenlet = None
benchmark_measurements_greenlet = None

lua_fps = None  # type: StrictRedis.Script
rdb = None

# FFMPEG mode implies not running the activate on redis; and collecting the fps from redis.
FFMPEG_MODE = True

# Connect to the redis instance
rdb = redis.StrictRedis(host=config.REDIS_HOST, port=config.REDIS_PORT, db=config.REDIS_DB, decode_responses=True)

# Register Lua scripts
code = open('lua/calculated_fps.lua', 'r').read()
lua_calculated_fps = rdb.register_script(code)
code = open('lua/ffmpeg_fps.lua', 'r').read()
lua_ffmpeg_fps = rdb.register_script(code)


def benchmark():
    N = [10, 10, 10]
    global benchmark_runner_greenlet, benchmark_measurements_greenlet
    benchmark_runner_greenlet = gevent.spawn(benchmark_run_g, N)
    benchmark_measurements_greenlet = gevent.spawn(measurements_g)
    benchmark_keep_active_greenlet = gevent.spawn(keep_active_g, N)


def benchmark_run_g(feeders):
    """
    Runs a single benchmark cycle.
    Feeders is an array with the form [4, 4, 4]. Each element is a subprocess, and indicates the number of cameras.
    :return:
    """

    n_procs = len(feeders)

    # Generate configs
    for p, n in enumerate(feeders):
        f = open("/tmp/cams_bench_{}.yml".format(p), "w")
        sb = io.StringIO()
        sb.write("cams:\n")
        for i in range(n):
            sb.write("    cam{}_{}:\n".format(p, i))
            sb.write("        img_urls: http://localhost:8050/fakewebcam/image.jpg\n")
            sb.write("        mjpeg_url: http://localhost:8050/fakewebcam/image.mjpeg\n")
            sb.write("        rotate: 0\n")
            sb.write("        mpeg: False\n")
            sb.write("        h264: True\n")
        f.write(sb.getvalue())
        f.close()

    def spawn_subproc():
        subprocess.run("export CAMS_YML=/tmp/cams_bench_{}.yml && python run.py".format(p), shell=True)

    greenlets = []
    for p in range(n_procs):
        gl = gevent.spawn(spawn_subproc)
        greenlets.append(gl)

    gevent.joinall(greenlets)
    return


def measurements_g():
    """
    Measures the CPU and RAM usage.
    :return:
    """
    proc = psutil.Process()
    mem = psutil.virtual_memory()

    gevent.sleep(4)

    while True:
        print("Av: {}. Oc: {}. TPhys: {}".format(mem.available / (1024.0 ** 2), mem.used / (1024.0 ** 2),
                                                 mem.total / (1024.0 ** 2)))
        print("CPU: {}".format(psutil.cpu_percent(interval=None, percpu=False)))
        print("Fds and open files: {} {}".format(proc.num_fds(), proc.open_files()))


        if not FFMPEG_MODE:
            print("Average FPS: {}".format(lua_calculated_fps()))
        else:
            print("Average (ffmpeg) FPS: {}".format(lua_ffmpeg_fps()))

        gevent.sleep(1)


def keep_active_g(feeders):
    """
    Keeps the active flag set in Redis.
    :return:
    """

    if not FFMPEG_MODE:

        while True:
            for p, n in enumerate(feeders):
                for i in range(n):
                    cam_key = "{}:cams:cam{}_{}".format(config.REDIS_PREFIX, p, i)
                    rdb.setex(cam_key + ":active", 30, 1)

            gevent.sleep(3)


benchmark()

# Run for a fixed time
benchmark_runner_greenlet.join(120)
