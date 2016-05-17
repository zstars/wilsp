import gevent
import struct

from app import socketio, rdb
from io import BytesIO

from gevent import monkey
# So that redis pubsub listen can be done asynchronously.
monkey.patch_all()



class SocketIOMPEGRedisBroadcaster(object):
    """
    The MPEG Redis broadcaster will listen to a MPEG stream that is published through
    a particular Redis channel and forward the stream to the client through the Socket IO library.
    """

    def __init__(self, cam_name):
        self._cam_name = cam_name
        self._channel = "{}/mpeg".format(cam_name)

    def run(self):

        print("Running SocketIO MPEG Redis broadcaster")

        # First, we need to subscribe to the Redis channel.
        rchannel = rdb.pubsub()
        rchannel.subscribe([self._channel])

        print("Subscribed to REDIS channel...")

        b = BytesIO()

        # Send magic bytes first
        b.write(b'jsmp')

        # Send w and h
        b.write(struct.pack('!H', 320))
        b.write(struct.pack('!H', 240))

        socketio.emit('stream', b.getvalue(), namespace='/mpeg_stream')

        while True:
            for item in rchannel.listen():

                print('Received: {}'.format(item))
                if item['type'] == 'message':
                    print('Emitting {}'.format(repr(item)))
                    socketio.emit('stream', item['data'], namespace='/mpeg_stream')
                else:
                    print("Msg of type: {}".format(item['type']))
                    pass

        print("OUT")