import gevent
from gevent import monkey
monkey.patch_all()

import time

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

    Issues:
     - We need an efficient way to know when we should exit the threadlet (remote user no longer listening).
    """

    SOCKETIO_NAMESPACE = '/mjpeg'

    def __init__(self, cam_name, client_sid, fps=5):
        self._cam_name = cam_name
        self._fps = fps
        self._target_sleep = 1.0 / self._fps
        self._should_stop = False

        print("CLIENT SID IS: ", client_sid)
        self._client_sid = client_sid

        self._cam_key = '{}:cams:{}'.format(current_app.config['REDIS_PREFIX'], self._cam_name)

    def stop(self):
        """
        Stops the broadcaster. It should be stopped, for instance, when the client loses connection.
        Otherwise we "leak" greenlets.
        :return:
        """
        self._should_stop = True

    def run(self):
        print("Running SocketIO MJPEG broadcaster at {} target FPS".format(self._fps))

        not_available = open("app/static/no_image_available.png", "rb").read()

        while not self._should_stop:

            frame_start_time = time.time()

            frame = rdb.get(self._cam_key + ":lastframe")

            # Mark the cam as active. This signals the feeder so that it starts working on this. It could potentially
            # be made more efficient by working in a background
            # thread, but that would be overkill for now.
            rdb.setex(self._cam_key + ":active", 30, 1)

            if frame is not None:
                r = socketio.emit('frame', frame, namespace=SocketIOMJPEGBroadcaster.SOCKETIO_NAMESPACE,
                              room=self._client_sid)
            else:
                r = socketio.emit('frame', not_available, namespace=SocketIOMJPEGBroadcaster.SOCKETIO_NAMESPACE,
                              room=self._client_sid)

            time_to_sleep = self._target_sleep - (time.time() - frame_start_time)
            if(time_to_sleep < 0):
                time_to_sleep = 0

            gevent.sleep(time_to_sleep)

        print("SocketIO MJPEG broadcaster stopped for client [{}]".format(self._client_sid))
