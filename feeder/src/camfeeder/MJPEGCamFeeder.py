import io

import gevent
import grequests
import redis
import time
import requests

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

        self._request_response = None  # type: requests.Response

    def _run_until_inactive(self):
        """
        Will just keep pushing images and checking the active status until
        the camera should not be active anymore.
        :return:
        """

        self._start_streaming_request()

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

    def _parse_next_image(self) -> (bytes, int):
        """
        Retrieves the next image from the stream.
        :return: Tuple containing the bytes for the file, and the time reported by the server.
        """
        headers = self._parse_headers()
        print('HEADERS ARE: ', headers)
        content_type = headers.get('content-type')
        if content_type is None:
            raise FrameGrabbingException('Unexpected response: Content type not present')
        if content_type != 'image/jpeg':
            raise FrameGrabbingException('Unexpected response: Content type is not a JPEG image')
        content_length = headers.get('content-length')
        if content_length is None:
            raise FrameGrabbingException('No content-length available')
        content_length = int(content_length)

        image = self._request_response.raw.read(content_length)
        if len(image) != content_length:
            raise FrameGrabbingException('Unexpected length of retrieved image')

        # Now skip until the boundary is reached.
        while True:
            line = self._request_response.raw.readline().strip()
            if b'boundary' in line:
                break

        return (image,0)

    def _parse_headers(self) -> dict:
        """
        Reads HTTP headers from the stream.
        :return: Dictionary with the headers. The dict is not case-insensitive but the keys are converted to lowercase.
        """
        headers = {}
        print("TYPE: ", type(self._request_response.raw))
        while True:
            line = self._request_response.raw.readline().strip()
            line = line.decode('utf-8')
            print("LINE: {}".format(line))
            if len(line) == 0:
                if len(headers) != 0:  # We want to skip initial new-lines.
                    break
                else:
                    continue

            key, val = line.split(':', 1)  # type: str, str
            headers[key.lower()] = val.strip()
        return headers


    def _start_streaming_request(self) -> None:
        """
        Starts a streaming session. The endpoint should be a multipart/x-mixed-replace MJPEG stream.
        Because the FPS is set by the remote server, desync issues can arise. Those desync issues can
        set a very high capture-store latency, so we will have to detect and handle them by restarting
        the stream.

        Post-condition: Ready to start reading the self._request_response
        :return:
        """
        r = grequests.get(self._url, stream=True)
        ar = r.send()
        self._request_response = ar.response  # type: requests.Response
        if self._request_response.status_code != 200:
            raise FrameGrabbingException('Unexpected response: not 200')
