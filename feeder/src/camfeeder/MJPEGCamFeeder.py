import io
import traceback

import gevent
import grequests
import redis
import time
import requests

from dateutil.parser import parse

from camfeeder.CamFeeder import CamFeeder


class FrameGrabbingException(Exception):
    def __init__(self, message, errors):
        super(FrameGrabbingException, self).__init__(message)
        self.errors = errors


class MJPEGCamFeeder(CamFeeder):
    """
    The MJPEG CamFeeder retrieves the images from the MJPEG stream of a camera.
    Most IP cameras (such as most Logitech models) provide MJPEG streams at particular URLs.
    """

    WAIT_ON_ERROR = 0.1  # Time to wait when an error occurs.

    def __init__(self, rdb: redis.StrictRedis, redis_prefix: str, cam_name: str, url: str, max_fps: int,
                 rotation: float = None):
        super(MJPEGCamFeeder, self).__init__(rdb, redis_prefix, cam_name, url, max_fps, rotation)

        self._request_response = None  # type: requests.Response
        self._request_response_boundary = None  # type: str

    def _run_until_inactive(self):
        """
        Will just keep pushing images and checking the active status until
        the camera should not be active anymore.
        :return:
        """

        while self._active:

            if self._request_response is None:
                try:
                    self._start_streaming_request()
                except Exception as ex:
                    traceback.print_exc(ex)
                    continue

            try:
                frame, date = self._parse_next_image()
                frame = self._rotated(frame, self._rotation)
                self._put_frame(frame)
            except Exception as ex:
                print("Restarting connection. Cause: {}".format(ex))
                self._request_response = None
                gevent.sleep(MJPEGCamFeeder.WAIT_ON_ERROR)

            self._check_active()

            # We cannot control the rate client-side (it is set by the remote webcam) so we have to read
            # as fast as possible.
            gevent.sleep(0)

    def _parse_next_image(self) -> (bytes, int):
        """
        Retrieves the next image from the stream.
        :return: Tuple containing the bytes for the file, and the time reported by the server.
        """
        headers = self._parse_headers()
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
            line = line.decode('utf-8')
            if len(line) > 0:
                if line == self._request_response_boundary:
                    break
                else:
                    raise FrameGrabbingException('Did not find expected boundary: ', line)

        date = headers['date']
        if date is None:
            raise FrameGrabbingException('No date header received')

        # TODO: This will support a very limited number of formats.
        date = str.join(' ', date.split(' ')[:3])
        date = parse(date, fuzzy=True)

        return image, date

    def _parse_headers(self) -> dict:
        """
        Reads HTTP headers from the stream.
        :return: Dictionary with the headers. The dict is not case-insensitive but the keys are converted to lowercase.
        """
        headers = {}
        while True:
            line = self._request_response.raw.readline().strip()
            line = line.decode('utf-8')
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
        the stream. It is also expected that it reports a boundary, which will be parsed.

        Post-condition: Ready to start reading the self._request_response. The self._request_response is not set
        unless the start was apparently successful.
        :return:
        """
        r = grequests.get(self._url, stream=True)
        ar = r.send()
        resp = ar.response  # type: requests.Response
        if resp.status_code != 200:
            raise FrameGrabbingException('Unexpected response: not 200')

        headers = resp.headers
        content_type = headers['content-type']
        if content_type is None:
            raise FrameGrabbingException('Content-type not provided')

        # TODO: If no x-mixed-replace and no boundary send a warning (unexpected respons: maybe not MJPEG)
        ctype, boundary = content_type.split(';', 1)
        ctype = ctype.strip()

        if ctype != 'multipart/x-mixed-replace':
            raise FrameGrabbingException('Response content type is not multipart/x-mixed-replace')

        boundary = boundary.split('=', 1)[1].strip()

        self._request_response_boundary = boundary
        self._request_response = resp
