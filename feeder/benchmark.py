from greenlet import GreenletExit
from optparse import OptionParser

import gevent
import redis
import time

import zlib
from gevent import monkey

monkey.patch_all()

import os
from gevent import subprocess
import io

import psutil
import zbarlight
from PIL import Image
import seqfile

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

CLIENTS_PER_PROCESS = 5  # Max number of clients per process

# Parse QR
PARSE_QR = False

# Connect to the redis instance
rdb = redis.StrictRedis(host=config.REDIS_HOST, port=config.REDIS_PORT, db=config.REDIS_DB, decode_responses=False)

# Register Lua scripts
code = open('lua/calculated_fps.lua', 'r').read()
lua_calculated_fps = rdb.register_script(code)
code = open('lua/ffmpeg_fps.lua', 'r').read()
lua_ffmpeg_fps = rdb.register_script(code)


def run(clients, format, measurements):

    # Generate the clients organization [proc1_clients, ..., procn_clients]
    # 5 clients per processor.
    N = []
    full_procs = clients // CLIENTS_PER_PROCESS
    rem_procs = clients % CLIENTS_PER_PROCESS
    for i in range(full_procs):
        N.append(CLIENTS_PER_PROCESS)

    if rem_procs > 0:
        N.append(rem_procs)

    print("Array of clients per process: {}".format(N))

    global benchmark_runner_greenlet, benchmark_measurements_greenlet
    benchmark_runner_greenlet = gevent.spawn(benchmark_run_g, N)
    benchmark_measurements_greenlet = gevent.spawn(measurements_g, N, measurements, format)

    if format == "img":
            benchmark_keep_active_greenlet = gevent.spawn(keep_active_g, N, format)

    # Run until the specified number of measurements are taken.
    benchmark_measurements_greenlet.join()
    gevent.kill(benchmark_runner_greenlet, exception=GreenletExit)
    gevent.kill(benchmark_keep_active_greenlet)

    print("Run finished")

    benchmark_runner_greenlet.join()
    benchmark_keep_active_greenlet.join()

    print("Out")


def benchmark_run_g(feeders):
    """
    Runs the feeder subprocesses for benchmarking.
    Feeders is an array with the form [4, 4, 4]. Each element is a subprocess, and indicates the number of cameras.
    :return:
    """

    try:

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
                sb.write("        h264: False\n")
            f.write(sb.getvalue())
            f.close()

        def spawn_subproc(p):
            print("Spawning: {}".format(p))
            subprocess.run("export CAMS_YML=/tmp/cams_bench_{}.yml && python run.py".format(p), shell=True)

        greenlets = []
        for p in range(n_procs):
            gl = gevent.spawn(spawn_subproc, p)
            greenlets.append(gl)

        gevent.joinall(greenlets)

    except GreenletExit:
        print("Subprocesses out")
        for g in greenlets:
            g.kill()

    return


def measurements_g(feeders, measurements, format):
    """
    Measures the CPU, RAM and network usage. Stops when the specified number of measurements are taken.
    @param feeders: Array of clients per process. E.g., [2, 2, 1]
    @param measurements: Measurements to take
    @param format: img or h264
    :return:
    """
    proc = psutil.Process()
    mem = psutil.virtual_memory()

    # Prepare for recording results
    results_file = seqfile.findNextFile(".", "benchmark_results_", ".txt", maxattempts=100)
    results = open(results_file, "w")
    results.write("cpu,mem_used,bw,fps,lat\n")

    # 5 seconds plus half a second for each feeder.
    gevent.sleep(5+sum(feeders)*0.5)

    # Note: The first iteration results should be discarded. They are faster.

    iterations = 0

    measurements_done = 0
    measurements_failed = 0

    while measurements_done < measurements:

        try:
            lat = None
            if format == "img":
                if PARSE_QR:
                    lat = calculate_latency(feeders)

            cpu = psutil.cpu_percent(interval=None, percpu=False)
            bw = psutil.net_io_counters().bytes_sent
            mem_used = mem.used / (1024.0 ** 2)

            if format == "img":
                fps = lua_calculated_fps()
            else: # h264
                fps = lua_ffmpeg_fps()
            fps = float(fps)

            report = "{},{},{},{},{}\n".format(cpu, mem_used, bw, fps, lat)
            print(report)

            # Ignore the first 4 iterations. They have unusually short times.
            if iterations > 4:
                results.write(report)

            results.flush()
            iterations += 1
            measurements_done += 1
        except:
            print("Error taking measurement")
            measurements_failed += 1
            if measurements_failed > 10:
                print("Abort.")
                break

        gevent.sleep(1)


def calculate_latency(feeders):
    count = 0
    tot_elapsed = 0
    frame = None
    image = None
    for p, n in enumerate(feeders):
        for i in range(n):

            cam_key = "{}:cams:cam{}_{}:lastframe".format(config.REDIS_PREFIX, p, i)

            try:

                frame = rdb.get(cam_key)
                if frame is None:
                    print("Could not find such a frame: {}".format(cam_key))

                current_time = int(time.time() * 1000)

                # Note: Opening and parsing the QR takes around 27 ms.
                image = Image.open(io.BytesIO(frame))
                image.load()
                codes = zbarlight.scan_codes('qrcode', image)

                if len(codes) != 1:
                    print("No code in image")
                    continue

                code = codes[0]
                timestamp, crc = code.split(b'|')
                crc_expected = hex(zlib.crc32(timestamp)).encode('utf-8')
                if crc != crc_expected:
                    print("Code was parsed wrong")
                    print("CRC: {}; expected: {}".format(crc, crc_expected))
                    continue

                then_time = int(timestamp)
                elapsed = current_time - then_time
                count += 1
                tot_elapsed += elapsed

            except:
                if frame is None:
                    frame = []
                print("[Exception trying to get latency. FL: {}, {}]".format(len(frame), image))

            #print("FRAME LEN: {}".format(len(frame)))
    if count > 0:
        print("Elapsed average: {}".format(tot_elapsed / count))
    else:
        print("Average not available")

    return tot_elapsed / count


def keep_active_g(feeders, format):
    """
    Keeps the active flag set in Redis.
    :return:
    """

    if format == "img":
        while True:
            for p, n in enumerate(feeders):
                for i in range(n):
                    cam_key = "{}:cams:cam{}_{}".format(config.REDIS_PREFIX, p, i)
                    rdb.setex(cam_key + ":active", 30, 1)

            gevent.sleep(3)

if __name__ == "__main__":

    parser = OptionParser()
    parser.add_option("-c", "--clients", type="int", dest="clients", default=10, help="Number of clients to simulate")
    parser.add_option("-f", "--format", type="string", dest="format", default="img", help="img or h264 mode")
    parser.add_option("-n", "--measurements", type="int", dest="measurements", default=15, help="Number of measurements to take")

    (options, args) = parser.parse_args()

    if options.format not in ("img", "format"):
        parser.print_usage()
        exit(1)

    if options.clients <= 0:
        parser.print_usage()
        exit(1)

    run(options.clients, options.format, options.measurements)
