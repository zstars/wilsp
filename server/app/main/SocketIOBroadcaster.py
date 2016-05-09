import gevent
import struct

from app import socketio
from io import BytesIO



class SocketIOBroadcaster(object):

    def run(self):
        print("Running SocketIO broadcaster")
        not_available = open("app/static/no_image_available.png", "rb").read()

        b = BytesIO()

        # Send magic bytes first
        b.write(b'jsmp')

        # Send w and h
        b.write(struct.pack('!H', 320))
        b.write(struct.pack('!H', 240))

        socketio.send(b.getvalue(), namespace='/stream')

        while True:

            socketio.send(not_available, namespace='/stream')

            gevent.sleep(1)
            print("Iteration")
