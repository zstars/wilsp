from greenlet import GreenletExit

import gevent
from gevent import monkey
monkey.patch_all()

from optparse import OptionParser
import os
import time
import subprocess
import psutil
import seqfile
import itertools
import sys
import traceback

INIT_ITERATIONS = 4

abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(dname)

import benchmark.fr as fr
import benchmark.rem_browser as rem_browser

print(os.getcwd())

benchmark_runner_greenlet = None
benchmark_measurements_greenlet = None

rdb = None


def run(clients, format, measurements, results, basecomp, key, req_url, browserhost):

    print("BENCHMARK STARTING. Clients: {} | Format: {} | Measurements: {}".format(clients, format, measurements))

    if browserhost is not None and len(browserhost) > 0:
        fr_clients = clients - 1
    else:
        fr_clients = clients

    # First, we should run a number of requesters. So that they do not affect the benchmark, they should be run
    # on a different computer.
    try:
        fr.start_remote_fakerequester(basecomp, key, "/home/lrg/wilsa/wilsaproxy/fakerequester", fr_clients, req_url)
    except:
        print("[ERROR]: Could not start fakerequester. This is a fatal error. Aborting.")
        traceback.print_exc()
        sys.exit(1)

    # Verifies that the fakerequester is running
    try:
        fr.check_remote_fakerequester(basecomp, key, "/home/lrg/wilsa/wilsaproxy/fakerequester", fr_clients)
    except:
        print("[ERROR]: Does not seem the fakerequester is running properly. Aborting.")
        traceback.print_exc()
        sys.exit(1)

    if browserhost is not None and len(browserhost) > 0:
        # Now we run the remote browser requester.
        try:
            rem_browser.start_remote_browser(browserhost, key, "/home/lrg/wilsa/wilsaproxy/server/benchmark", clients, req_url, format)
        except:
            print("[ERROR]: Could not start remote browser requester. This is a fatal error. Aborting.")
            traceback.print_exc()
            sys.exit(1)


    # Runs the actual flask server to be benchmarked, with gunicorn.
    benchmark_runner_greenlet = gevent.spawn(benchmark_run_g)

    # Runs the greenlet that takes measurements.
    benchmark_measurements_greenlet = gevent.spawn(measurements_g, clients, measurements, format, results)

    # Run until the measurements greenlet returns, indicating that we have taken enough measurements.
    benchmark_measurements_greenlet.join()
    gevent.kill(benchmark_runner_greenlet, exception=GreenletExit)

    benchmark_runner_greenlet.join()

    # Stop the fake requesters.
    try:
        fr.stop_remote_fakerequester(basecomp, key)
    except:
        print("[ERROR]: Could not stop fakerequester. This is a fatal error. Aborting.")
        sys.exit(1)

    if browserhost is not None and len(browserhost) > 0:
        try:
            rem_browser.stop_remote_browser(browserhost, key)
        except:
            print("[ERROR]: Could not stop remote browser requester. This is a fatal error. Aborting.")
            traceback.print_exc()
            sys.exit(1)

    time.sleep(2)

    print("Run done.")


def benchmark_run_g():
    """
    Runs gunicorn for a single benchmark cycle.
    :return:
    """
    procs = []
    gl = None
    try:
        def spawn_subproc():
            proc = subprocess.Popen("gunicorn -w 4 -k gevent -b 0.0.0.0:5000 --pythonpath ../$(pwd) wsgi_app:application",
                                    shell=True, preexec_fn=os.setsid)
            procs.append(proc)

        greenlets = []

        gl = gevent.spawn(spawn_subproc)

        while True:
            gevent.sleep(2)

    except GreenletExit:
        for p in procs:
            os.killpg(os.getpgid(p.pid), gevent.signal.SIGTERM)
        gl.kill()


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

    # To calculate Bps
    last_bw = psutil.net_io_counters().bytes_sent
    last_bw_time = time.time()

    while times_measured < measurements:

        try:
            cpu = psutil.cpu_percent(interval=None, percpu=False)

            # Calculate bytes per second.
            bw = psutil.net_io_counters().bytes_sent
            bw_time = time.time()
            bytes_per_sec = int((bw - last_bw) / (bw_time - last_bw_time))
            last_bw, last_bw_time = bw, bw_time

            mem_used = mem.used / (1024.0 ** 2)

            report = "{},{},{},{},{},{},{}\n".format(clients, format, cpu, mem_used, bytes_per_sec, None, None)

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
            print("Reason: ")
            traceback.print_exc()
            times_failed += 1
            if times_failed > 10:
                print("Abort.")
                break

        gevent.sleep(1)


if __name__ == "__main__":

    parser = OptionParser()
    parser.add_option("-c", "--clients", type="int", dest="clients", default=10, help="Number of clients to simulate")
    parser.add_option("-f", "--format", type="string", dest="format", default="img", help="img, h264, or all mode")
    parser.add_option("-n", "--measurements", type="int", dest="measurements", default=15, help="Number of measurements to take")
    parser.add_option("-a", "--all", dest="all", default=False, action="store_true", help="Execute the benchmark multiple times for a different number of clients up to the specified one")
    parser.add_option("-l", "--label", dest="label", default="bm_", help="Label for the result files")
    parser.add_option("-b", "--basecomp", dest="basecomp", default="lrg@newplunder", help="ssh-style user@host where the fake requesters will be run")
    parser.add_option("-k", "--key", dest="key", default="~/.ssh/id_rsa.pub", help="path to the public key that will be used to connect to the remote base comp")
    parser.add_option("-u", "--requrl", dest="requrl", default="http://localhost:5000/cams/cam0_0", help="URL to request")

    # For the browser-based requester.
    parser.add_option("-r", "--browserhost", dest="browserhost", default="", help="ssh-style user@host for the browser requester")

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
        run(br[0], br[1], options.measurements, results, options.basecomp, options.key, options.requrl, options.browserhost)

    results.close()
