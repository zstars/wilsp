"""
This module uses Selenium to open a Chrome and obtain latency information automatically.
"""

import gevent
import zlib
from gevent import monkey
from seqfile import seqfile

monkey.patch_all()

from PIL import Image
import zbarlight

import time
from optparse import OptionParser
from selenium import webdriver

from pyvirtualdisplay import Display

import traceback

DEFAULT_URL = "http://localhost:5000/exps/imgrefresh/cam0_0"
DEFAULT_TIMES = 15

driver = None  # Selenium webdriver


def calculate_elapsed(current_time, snapshot_path):
    """
    Reads the QR from the snapshot path, which contains a timestamp, and calculates the delay.
    :param current_time: Timestamp in milliseconds. (Not in seconds!)
    :param snapshot_path:
    :return:
    """
    # Note: Opening and parsing the QR takes around 27 ms.
    image = Image.open(snapshot_path)
    image.load()
    codes = zbarlight.scan_codes('qrcode', image)

    if codes is None or len(codes) != 1:
        print("No code in image")
        return None

    code = codes[0]
    timestamp, crc = code.split(b'|')
    crc_expected = hex(zlib.crc32(timestamp)).encode('utf-8')
    if crc != crc_expected:
        print("Code was parsed wrong")
        print("CRC: {}; expected: {}".format(crc, crc_expected))
        return None

    then_time = int(timestamp)
    elapsed = current_time - then_time

    return elapsed


def background_g(times, results, preppend):

    # Results recorded
    num_results = 0

    num_failures = 0

    # Wait for a while to start
    gevent.sleep(5)

    driver.execute_script("cam.resetFPS()")

    gevent.sleep(2)

    while num_results < times:
        try:
            gevent.sleep(1)

            current_time = time.time()

            driver.save_screenshot('snapshot.jpeg')

            elapsed = calculate_elapsed(int(current_time * 1000), 'snapshot.jpeg')

            # Try to get FPS
            fps = driver.execute_script("return stats_fps")

            out = "{}{},{}\n".format(preppend, fps, elapsed)

            results.write(out)
            results.flush()

            print("RESULTS: {}".format(out))

            num_results += 1
            num_failures = 0
        except:
            traceback.print_exc()
            print("Error measuring elapsed time. Retrying.")
            num_failures += 1
            if num_failures > 20:
                print("Aborting.")
                break

    results.close()


def run(url, times, results, preppend):

    global driver

    display = Display(visible=0, size=(800, 600))
    display.start()

    driver = webdriver.Firefox()
    driver.get(url)

    glet = gevent.spawn(background_g, times, results, preppend)

    print("Driver is: {}".format(driver))

    glet.join()

    driver.quit()


if __name__ == "__main__":

    parser = OptionParser()
    parser.add_option("-u", "--url", default=DEFAULT_URL, dest="url")
    parser.add_option("-t", "--times", type="int", default=DEFAULT_TIMES, dest="times")
    parser.add_option("-c", "--csvoutput", metavar="FILE", default="out.csv", dest="csvoutput", help="Path to the CSV output file")
    parser.add_option("-p", "--preppend", default="", dest="preppend")

    (options, args) = parser.parse_args()

    results = open(options.csvoutput, "w+")

    if len(options.preppend) > 0:
        results.write("clients,format,fps,lat\n")
    else:
        results.write("fps,lat\n")

    run(options.url, options.times, results, options.preppend)
