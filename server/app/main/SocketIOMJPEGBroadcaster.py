import gevent

from flask import current_app
from app import socketio, rdb


class SocketIOMJPEGBroadcaster(object):
    """
    Broadcasts MJPEG through SocketIO to a specific user.

    Remarks:
     - SocketIO namespace: /mjpeg
     - Clients start receiving the stream by sending a 'start' event.
     - The 'frame' events are directed to the specific client.

    Possible improvements:
     - It might be possible and more efficient to truly broadcast to a room, but in that case
     there would be a single instance of this class.
    """

    SOCKETIO_NAMESPACE = '/mjpeg'

    def __init__(self, cam_name, client_sid):
        self._cam_name = cam_name
        self._client_sid = client_sid

        self._cam_key = '{}:cams:{}'.format(current_app.config['REDIS_PREFIX'], self._cam_name)

    def run(self):
        print("Running SocketIO MJPEG broadcaster")

        not_available = open("app/static/no_image_available.png", "rb").read()

        while True:

            frame = rdb.get(self._cam_key + ":lastframe")

            # Mark the cam as active. This signals the feeder so that it starts working on this. It could potentially
            # be made more efficient by working in a background
            # thread, but that would be overkill for now.
            rdb.setex(self._cam_key + ":active", 1, 30)

            if frame is not None:
                print("Rendering REAL frame")
                socketio.emit('frame', frame, namespace=SocketIOMJPEGBroadcaster.SOCKETIO_NAMESPACE,
                              room=self._client_sid)
            else:
                print("Rendering NOT AVAILABLE frame")
                socketio.emit('frame', not_available, namespace=SocketIOMJPEGBroadcaster.SOCKETIO_NAMESPACE,
                              room=self._client_sid)

            gevent.sleep(1)
            print("Iteration")
