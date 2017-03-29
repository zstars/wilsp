"""
This module uses Selenium to open a Chrome and obtain latency information automatically.
"""

import gevent
import zlib
from gevent import monkey
monkey.patch_all()

from PIL import Image
import zbarlight

import io
import time

URL = "http://localhost:5000/exps/imgrefresh/cam0_0"

from selenium import webdriver

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

    if len(codes) != 1:
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


def background_g():
    while True:
        gevent.sleep(4)

        current_time = time.time()

        driver.save_screenshot('snapshot.jpeg')

        elapsed = calculate_elapsed(int(current_time * 1000), 'snapshot.jpeg')

        print("ELAPSED: {}".format(elapsed))

def run():

    global driver

    glet = gevent.spawn(background_g)

    driver = webdriver.Chrome()
    driver.get(URL)

    glet.join(120)

if __name__ == "__main__":
    run()
