
import gevent
from gevent import monkey
monkey.patch_all()

import os
import subprocess

import psutil

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
    global benchmark_runner_greenlet, benchmark_measurements_greenlet
    benchmark_runner_greenlet = gevent.spawn(benchmark_run_g)
    benchmark_measurements_greenlet = gevent.spawn(measurements_g)


def benchmark_run_g():
    """
    Runs a single benchmark cycle.
    :return:
    """
    sp = subprocess.run("python run.py", shell=True)
    return sp


def measurements_g():
    """
    Measures the CPU and RAM usage.
    :return:
    """
    proc = psutil.Process()
    mem = psutil.virtual_memory()

    while True:
        print("Av: {}. Oc: {}. TPhys: {}".format(mem.available/(1024.0**2), mem.used/(1024.0**2), mem.total/(1024.0**2)))
        gevent.sleep(1)


benchmark()

# Run for a fixed time
benchmark_runner_greenlet.join(80)

