import gevent
import struct

from app import socketio, rdb
from io import BytesIO



class SocketIOMJPEGBroadcaster(object):

    def run(self):
        print("Running SocketIO MJPEG broadcaster")
        cam_key = "wilsa:cams:archimedes1"
        not_available = open("app/static/no_image_available.png", "rb").read()

        while True:

            frame = rdb.get(cam_key + ":lastframe")

            # Mark the cam as active. This signals the feeder so that it starts working on this. It could potentially
            # be made more efficient by working in a background
            # thread, but that would be overkill for now.
            rdb.setex(cam_key + ":active", 30, 1)

            if frame is not None:
                print("Rendering REAL frame")
                socketio.emit('frame', frame, namespace='/mjpeg_stream')
            else:
                print("Rendering NOT AVAILABLE frame")
                socketio.emit('frame', not_available, namespace='/mjpeg_stream')

            gevent.sleep(1)
            print("Iteration")
