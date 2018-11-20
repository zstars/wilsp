import requests
import time


webcam_url = "http://cams.weblab.deusto.es/webcam/proxied.py/arquimedes2_rotate"
start_time = time.time()

while True:
    elapsed = time.time() - start_time

    r = requests.get(webcam_url)
    f = open("ar_{}.jpg".format(int((elapsed * 1000))), 'w')
    f.write(r.content)
    f.close()

    if elapsed > 20:
        break

print("Done")