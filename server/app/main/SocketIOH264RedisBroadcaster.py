import json

from eventlet import monkey_patch

monkey_patch(all=True)

from app import socketio, rdb


class SocketIOH264RedisBroadcaster(object):
    """
    The H264 Redis broadcaster will listen to an H264 stream that is published through
    a particular Redis channel and forward the stream to the client through the Socket IO library.

    The Node stream server for the JavaScript renderer originally worked over WebSockets and sent the 'jsmp' bytes first,
    then the height and width, and then the actual stream. Though I have currently not verified it, only the second
    part seems to be an actual part of the expected stream. Eventually we should maybe consider sending these bytes through
    a different socktio channel (event name) in order to ensure that multiple users can eventually be seamlessly
    supported.

    TODO: Exit the threadlet when inactive, or whatever.
    """

    SOCKETIO_NAMESPACE = "/h264"

    FRAME_SEPARATOR = b'\x00\x00\x00\x01'

    def __init__(self, cam_name, client_sid):
        """
        Creates the SocketIOMPEGRedisBroadcaster object.
        :param cam_name: Name of the camera.
        :param client_sid: SocketIO SID for the client that we will send the data to. (We cannot just use the flask
        request because I think we do not have access to it here).
        """
        self._cam_name = cam_name
        self._channel = "{}/h264".format(cam_name)  # Redis channel to listen to.
        self._client_sid = client_sid

    def run(self):

        print("Running SocketIO H264 Redis broadcaster")

        # First, we need to subscribe to the Redis channel.
        rchannel = rdb.pubsub()
        rchannel.subscribe([self._channel])

        print("Subscribed to REDIS channel...")
        print("We are serving client {}...".format(self._client_sid))

        # NOTE: This is here for reference, and the client still supports canvas initialization, but it is no longer
        # needed. Now, the player automatically initialises itself with the starting width and height of the
        # provided Canvas.
        
        # init = {
        #     'action': 'init',
        #     'width': 640,
        #     'height': 360 # Normally 480
        # }
        #
        # socketio.emit('cmd', json.dumps(init), namespace=SocketIOH264RedisBroadcaster.SOCKETIO_NAMESPACE,
        #       room=self._client_sid)

        buffer = bytearray()

        while True:
            for item in rchannel.listen():

                # Print commented out because it works and spams the console.
                # print('Received: {}'.format(item))
                if item['type'] == 'message':
                    # print('Emitting {}'.format(repr(item)))
                    buffer.extend(item['data'])

                    while True:
                        # Try to extract a packet.
                        splits = buffer.split(SocketIOH264RedisBroadcaster.FRAME_SEPARATOR, 1)
                        if len(splits) < 2:
                            break

                        packet, buffer = splits[:]

                        # For the H.264 format, the client expects to receive the packets split by \x00\x00\x00\x01.
                        socketio.emit('stream', SocketIOH264RedisBroadcaster.FRAME_SEPARATOR + packet, namespace=SocketIOH264RedisBroadcaster.SOCKETIO_NAMESPACE,
                                      room=self._client_sid)
                else:
                    print("Msg of type: {}".format(item['type']))
                    pass

        print("OUT")
