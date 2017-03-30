import gevent
import redis
import time

import zlib
from gevent import monkey

monkey.patch_all()

import os
import subprocess

import psutil
import seqfile

abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(dname)

print(os.getcwd())

benchmark_runner_greenlet = None
benchmark_measurements_greenlet = None

rdb = None

NUM_CLIENTS = 5
NUM_MEASUREMENTS = 15


def run(clients, measurements):
    global benchmark_runner_greenlet, benchmark_measurements_greenlet

    benchmark_runner_greenlet = gevent.spawn(benchmark_run_g)

    benchmark_measurements_greenlet = gevent.spawn(measurements_g, clients, measurements)


def benchmark_run_g():
    """
    Runs a single benchmark cycle.
    :return:
    """

    def spawn_subproc():
        result = subprocess.check_call("gunicorn -w 4 -k gevent -b localhost:5000 --pythonpath ../$(pwd) wsgi_app:application", shell=True)
        print("RESULT: {}".format(result))

    gl = gevent.spawn(spawn_subproc)

    gl.join()

    return gl


def measurements_g(clients, measurements):
    """
    Measures the CPU, RAM and network usage.
    :return:
    """
    proc = psutil.Process()
    mem = psutil.virtual_memory()

    # Prepare for recording results
    results_file = seqfile.findNextFile(".", "server_benchmark_results_", ".txt", maxattempts=100)
    results = open(results_file, "w")
    results.write("cpu,mem_used,bw,fps,lat\n")

    # 5 seconds plus half a second for each feeder.
    gevent.sleep(6)

    # Note: The first iteration results should be discarded. They are faster.

    iterations = 0

    times_measured = 0
    times_failed = 0

    while times_measured < measurements:

        try:
            cpu = psutil.cpu_percent(interval=None, percpu=False)
            bw = psutil.net_io_counters().bytes_sent
            mem_used = mem.used / (1024.0 ** 2)

            report = "{},{},{}\n".format(cpu, mem_used, bw)
            print(report)

            # Ignore the first two iterations. They have unusually short times.
            if iterations > 1:
                results.write(report)

            results.flush()
            iterations += 1
            times_measured += 1
        except:
            print("Error while benchmarking.")
            times_failed += 1
            if times_failed > 10:
                print("Aborting.")
                break

        gevent.sleep(1)

    results.close()

if __name__ == "__main__":
    run(NUM_CLIENTS, NUM_MEASUREMENTS)

    # Run until we stop measuring
    benchmark_measurements_greenlet.join()

    # Kill the gunicorn
    gevent.kill(benchmark_runner_greenlet)
