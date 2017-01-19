"""
Small experiment to check the performance of requests and grequests with gevent.
"""


import gevent
from gevent import monkey
# monkey.patch_all()
import requests
import grequests
import time
import random

def retrieve():
    r = requests.get("http://www.fakeresponse.com/api/?sleep=5&random={}".format(random.randint(0, 999999)), stream=True)
    # r = grequests.map([grequests.get("http://www.fakeresponse.com/api/?sleep=5")])
    return r.json()

start_time = time.time()
glets = []
for i in range(5):
    glets.append(gevent.spawn(retrieve))
result = gevent.joinall(glets)


print("Finished in {} seconds".format(time.time() - start_time))

for r in result:
    print(r.value)


# REQUESTS and NOT MONKEY (and NOT GREQUESTS): 26 seconds.
# REQUESTS and MONKEY: 5.2 seconds.
# REQUESTS and IMPORTING GREQUESTS: 5.2 seconds.
# GREQUESTS: 5.2 seconds.

# Extra notes: Using stream=True does not affect the results.

# Conclusion: It does not matter whether you use grequests or requests, as long as you monkey_patch *or* import grequests,
# which probably is monkey patching requests, either way.