from greenlet import GreenletExit

import gevent
from gevent import monkey
monkey.patch_all()

from optparse import OptionParser
import os
import subprocess
import psutil
import seqfile
import itertools

INIT_ITERATIONS = 4

abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(dname)

print(os.getcwd())

benchmark_runner_greenlet = None
benchmark_measurements_greenlet = None

rdb = None

def run(clients, format, measurements, results):

    # Runs the actual flask server to be benchmarked, with gunicorn.
    benchmark_runner_greenlet = gevent.spawn(benchmark_run_g)

    # Runs the greenlet that takes measurements.
    benchmark_measurements_greenlet = gevent.spawn(measurements_g, clients, measurements, format, results)

    # Run until the measurements greenlet returns, indicating that we have taken enough measurements.
    benchmark_measurements_greenlet.join()
    gevent.kill(benchmark_runner_greenlet, exception=GreenletExit)
    benchmark_runner_greenlet.join()


def benchmark_run_g():
    """
    Runs gunicorn for a single benchmark cycle.
    :return:
    """
    procs = []
    gl = None
    try:
        def spawn_subproc():
            proc = subprocess.Popen("gunicorn -w 4 -k gevent -b localhost:5000 --pythonpath ../$(pwd) wsgi_app:application",
                                    shell=True, preexec_fn=os.setsid)
            procs.append(proc)

        greenlets = []

        gl = gevent.spawn(spawn_subproc)

        while True:
            gevent.sleep(2)

    except GreenletExit:
        gl.kill()
        for p in procs:
            os.killpg(os.getpgid(p.pid), gevent.signal.SIGTERM)


def measurements_g(clients, measurements, format, results):
    """
    Measures the CPU, RAM and network usage.
    @param measurements: Number of measurements to take before returning.
    @param results: File to write to.
    :return:
    """
    proc = psutil.Process()
    mem = psutil.virtual_memory()

    # Wait before starting.
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

            report = "{},{},{},{},{},{},{}\n".format(clients, format, cpu, mem_used, bw, None, None)

            # Ignore the first iterations. They have unusually short times.
            if iterations > INIT_ITERATIONS:
                print(report)
                results.write(report)
                times_measured += 1
                results.flush()
            else:
                print("[INIT ONLY] " + report)

            iterations += 1
        except:
            print("Error taking measurement.")
            times_failed += 1
            if times_failed > 10:
                print("Abort.")
                break

        gevent.sleep(1)

    results.close()


if __name__ == "__main__":

    parser = OptionParser()
    parser.add_option("-c", "--clients", type="int", dest="clients", default=10, help="Number of clients to simulate")
    parser.add_option("-f", "--format", type="string", dest="format", default="img", help="img, h264, or all mode")
    parser.add_option("-n", "--measurements", type="int", dest="measurements", default=15, help="Number of measurements to take")
    parser.add_option("-a", "--all", dest="all", default=False, action="store_true", help="Execute the benchmark multiple times for a different number of clients up to the specified one")
    parser.add_option("-l", "--label", dest="label", default="bm_", help="Label for the result files")

    (options, args) = parser.parse_args()

    if options.format not in ("img", "h264", "all"):
        parser.print_usage()
        exit(1)

    if options.clients <= 0:
        parser.print_usage()
        exit(1)

    formats = []
    if options.format == "img":
        formats = ["img"]
    elif options.format == "h264":
        formats = ["h265"]
    elif options.format == "all":
        formats = ["img", "h264"]

    if options.all:
        client_numbers = range(1, options.clients+1)
    else:
        client_numbers = [options.clients]

    # Program the benchmarks for the client and format combination
    benchmark_runs = itertools.product(client_numbers, formats)

    # Open the file for storing the results
    results_file = seqfile.findNextFile(".", options.label, ".txt", maxattempts=100)

    results = open(results_file, "w")
    results.write("clients,format,cpu,mem_used,bw,fps,lat\n")

    for br in benchmark_runs:
        run(br[0], br[1], options.measurements, results)

    results.close()
