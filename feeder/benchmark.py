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


def benchmark():
    N = 350
    global benchmark_runner_greenlet, benchmark_measurements_greenlet
    benchmark_runner_greenlet = gevent.spawn(benchmark_run_g, N)
    benchmark_measurements_greenlet = gevent.spawn(measurements_g)
    benchmark_keep_active_greenlet = gevent.spawn(keep_active_g, N)


def benchmark_run_g(n):
    """
    Runs a single benchmark cycle.
    :return:
    """

    # Generate config
    f = open("/tmp/cams_bench.yml", "w")
    sb = io.StringIO()
    sb.write("cams:\n")
    for i in range(n):
        sb.write("    cam{}:\n".format(i))
        sb.write("        img_url: http://cams.weblab.deusto.es/webcam/proxied.py/arquimedes1_rotate\n")
        sb.write("        mjpeg_urls: http://cams.weblab.deusto.es/webcam/fishtank1/video.mjpeg\n")
        sb.write("        rotate: 0\n")
        sb.write("        mpeg: False\n")
        sb.write("        h264: False\n")
    f.write(sb.getvalue())
    f.close()

    sp = subprocess.run("export CAMS_YML=/tmp/cams_bench.yml && python run.py", shell=True)
    return sp


def measurements_g():
    """
    Measures the CPU and RAM usage.
    :return:
    """
    proc = psutil.Process()
    mem = psutil.virtual_memory()

    while True:
        print("Av: {}. Oc: {}. TPhys: {}".format(mem.available / (1024.0 ** 2), mem.used / (1024.0 ** 2),
                                                 mem.total / (1024.0 ** 2)))
        print("{}".format(psutil.cpu_percent(interval=None, percpu=False)))

        print("Fds and open files: {} {}".format(proc.num_fds(), proc.open_files()))

        print("")
        gevent.sleep(1)


def keep_active_g(n):
    """
    Keeps the active flag set in Redis.
    :return:
    """
    # Connect to the redis instance
    rdb = redis.StrictRedis(host=config.REDIS_HOST, port=config.REDIS_PORT, db=config.REDIS_DB, decode_responses=True)

    while True:
        for i in range(n):
            cam_key = "{}:cams:cam{}".format(config.REDIS_PREFIX, i)
            rdb.setex(cam_key + ":active", 30, 1)

        gevent.sleep(3)


benchmark()

# Run for a fixed time
benchmark_runner_greenlet.join(80)
