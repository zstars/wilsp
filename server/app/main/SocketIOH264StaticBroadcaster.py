import eventlet
from eventlet import monkey_patch

monkey_patch(all=True)

import struct

from app import socketio, rdb
from io import BytesIO


class SocketIOH264StaticBroadcaster(object):
    """
    The H264 Static broadcaster will stream a static H.264 file, mainly for testing purposes.

    The Node stream server for the JavaScript renderer originally worked over WebSockets and sent the 'jsmp' bytes first,
    then the height and width, and then the actual stream. Though I have currently not verified it, only the second
    part seems to be an actual part of the expected stream. Eventually we should maybe consider sending these bytes through
    a different socktio channel (event name) in order to ensure that multiple users can eventually be seamlessly
    supported.

    TODO: Exit the threadlet when inactive, or whatever.
    """

    SOCKETIO_NAMESPACE = "/h264"

    def __init__(self, cam_name, client_sid):
        """
        Creates the SocketIOMPEGRedisBroadcaster object.
        :param cam_name: Name of the camera.
        :param client_sid: SocketIO SID for the client that we will send the data to. (We cannot just use the flask
        request because I think we do not have access to it here).
        """
        self._cam_name = cam_name
        self._data = open("/home/lrg/repos/player/samples/test.h264", "rb").read()
        self._client_sid = client_sid

    def run(self):

        print("Running SocketIO H264 Static broadcaster")

        print("We are serving client {}...".format(self._client_sid))

        i = 0
        while True:

            if len(self._data) < i*1024 + 1024:
                i = 0
                continue

            socketio.emit('stream', self._data[i*1024:i*1024+1024], namespace=SocketIOH264StaticBroadcaster.SOCKETIO_NAMESPACE,
                          room=self._client_sid)
            i += 1

            eventlet.sleep(0.1)

        print("OUT")
