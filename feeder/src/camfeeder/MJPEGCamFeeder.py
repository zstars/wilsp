import gevent
import grequests
import redis
import time

from camfeeder.CamFeeder import CamFeeder


class FrameGrabbingException(Exception):
    def __init__(self, msg, cause=None):
        super().__init__(msg, cause)


class MJPEGCamFeeder(CamFeeder):
    """
    The MJPEG CamFeeder retrieves the images from the MJPEG stream of a camera.
    Most IP cameras (such as most Logitech models) provide MJPEG streams at particular URLs.
    """

    def __init__(self, rdb: redis.StrictRedis, redis_prefix: str, cam_name: str, url: str, max_fps: int,
                 rotation: float = None):
        super(MJPEGCamFeeder, self).__init__(rdb, redis_prefix, cam_name, url, max_fps, rotation)

    def _run_until_inactive(self):
        """
        Will just keep pushing images and checking the active status until
        the camera should not be active anymore.
        :return:
        """
        while self._active:

            update_start_time = time.time()

            frame = self._grab_frame()
            frame = self._rotated(frame, self._rotation)
            self._put_frame(frame)

            self._check_active()

            elapsed = time.time() - update_start_time
            intended_period = 1 / self._max_fps  # That's the approximate time a frame should take.

            time_left = intended_period - elapsed
            if time_left < 0:
                # We are simply not managing to keep up with the intended frame rate, but for this
                # cam feeder, that is not a (big) problem.
                gevent.sleep(0)
            else:
                gevent.sleep(time_left)

    def _grab_frame(self) -> bytes:
        """
        Grabs a frame. It will use the specified URL. Some special protocols may eventually be supported.
        :return:
        """
        try:
            rs = [grequests.get(self._url, stream=True)]
            r = grequests.map(rs)[0]
            if r.status_code != 200:
                raise FrameGrabbingException("Status code is not 200")
            content = r.content
            if len(content) < 100:
                raise FrameGrabbingException("Retrieved content is too small")
            return content
        except FrameGrabbingException:
            raise
        except Exception as exc:
            raise FrameGrabbingException("Exception occurred", exc)
