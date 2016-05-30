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

    The Node stream server for the JavaScript renderer originally worked over WebSockets and sent the 'jsmp' bytes first,
    then the height and width, and then the actual stream. Though I have currently not verified it, only the second
    part seems to be an actual part of the expected stream. Eventually we should maybe consider sending these bytes through
    a different socktio channel (event name) in order to ensure that multiple users can eventually be seamlessly
    supported.

    TODO: Exit the threadlet when inactive, or whatever.
    """

    SOCKETIO_NAMESPACE = "/mpeg"

    def __init__(self, cam_name, client_sid):
        """
        Creates the SocketIOMPEGRedisBroadcaster object.
        :param cam_name: Name of the camera.
        :param client_sid: SocketIO SID for the client that we will send the data to. (We cannot just use the flask
        request because I think we do not have access to it here).
        """
        self._cam_name = cam_name
        self._channel = "{}/mpeg".format(cam_name)  # Redis channel to listen to.
        self._client_sid = client_sid

    def run(self):

        print("Running SocketIO MPEG Redis broadcaster")

        # First, we need to subscribe to the Redis channel.
        rchannel = rdb.pubsub()
        rchannel.subscribe([self._channel])

        print("Subscribed to REDIS channel...")
        print("We are serving client {}...".format(self._client_sid))

        b = BytesIO()

        # Send magic bytes first
        b.write(b'jsmp')

        # Send w and h
        b.write(struct.pack('!H', 640))
        b.write(struct.pack('!H', 480))

        print('Emitted to "stream" on namespace {}'.format(SocketIOMPEGRedisBroadcaster.SOCKETIO_NAMESPACE))

        socketio.emit('stream', b.getvalue(), namespace=SocketIOMPEGRedisBroadcaster.SOCKETIO_NAMESPACE,
                      room=self._client_sid)

        while True:
            for item in rchannel.listen():

                # Print commented out because it works and spams the console.
                # print('Received: {}'.format(item))
                if item['type'] == 'message':
                    # print('Emitting {}'.format(repr(item)))
                    socketio.emit('stream', item['data'], namespace=SocketIOMPEGRedisBroadcaster.SOCKETIO_NAMESPACE,
                                  room=self._client_sid)
                else:
                    print("Msg of type: {}".format(item['type']))
                    pass

        print("OUT")
