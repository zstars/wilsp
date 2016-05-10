from abc import abstractmethod

import gevent
import io
import redis
from PIL import Image


class FrameGrabbingException(Exception):
    """
    Exception is internally raised when an attempt to get a frame from the webcam fails, or
    when the content is invalid.
    """

    def __init__(self, msg: str, cause=None):
        super().__init__(msg, cause)


class CamFeeder(object):
    TARGET_FPS = 150
    ACTIVE_CHECK_PERIOD = 0.01  # Check if webcam is active every X seconds.
    SLEEP_TIME_INACTIVE = 0.01  # Wait for x seconds after checking and being found inactive.
    DEBUG = True

    ########################################################
    # PUBLIC API
    ########################################################

    def __init__(self, rdb: redis.StrictRedis, redis_prefix: str, cam_name: str, url: str, max_fps: int,
                 rotation: float = None):
        self._g = None
        self._rdb = rdb  # type: redis.StrictRedis
        self._redis_prefix = redis_prefix
        self._url = url
        self._cam_name = cam_name
        self._rotation = rotation if rotation is not None else 0
        self._max_fps = max_fps

        self._frames_this_cycle = None
        self._active = None  # Whether the camera is active or not (being used, according to redis)
        self._active_since = None  # Timestamp when we last became active

    def get_current_fps(self) -> float:
        raise NotImplementedError()

    def start(self):
        self._g = gevent.Greenlet(self.run)
        self._g.start()


    ########################################################
    # PRIVATE API
    ########################################################

    @abstractmethod
    def _run_until_inactive(self) -> None:
        """
        Runs, feeding images to redis, until it is time to become inactive.
        :return:
        """
        raise NotImplementedError("_run_until_active should be implemented")

    def _wait_until_active(self) -> None:
        """
        Waits until it is time to become active. In order to do so, checks often
        whether someone has started using the webcam.
        :return:
        """
        raise NotImplementedError()

    def _run(self) -> None:
        """
        Greenlet's main thread. Will loop forever between the active and inactive loops.
        :return:
        """
        raise NotImplementedError()

    def _check_active(self) -> None:
        """
        Checks whether we should change our activity status, and thus change the current mode.
        :return:
        """
        raise NotImplementedError()

    def _notify_frame_put(self):
        """
        Should be called just after a new frame is put into redis so that internal FPS calculations, etc,
        can be carried out automatically.
        :return:
        """
        raise NotImplementedError()

    @staticmethod
    def _rotated(data: bytes, rotation: float) -> bytes:
        """
        Rotates the given image.
        :param data: The image as a full image file (such as a full JPG).
        :param rotation: Rotation to apply.
        :return: Full resulting jpeg image, expanded as necessary.
        """
        if rotation == 0:
            return data

        sio_in = io.BytesIO(data)
        img = Image.open(sio_in)  # type: Image
        img = img.rotate(rotation, expand=True)
        sio_out = io.BytesIO()
        img.save(sio_out, 'jpeg')
        data = sio_out.getvalue()
        img.close()

        return data

    def _put_frame(self, frame: bytes) -> None:
        raise NotImplementedError()


if __name__ == "__main__":
    import doctest
    doctest.testmod()