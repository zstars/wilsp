import gevent
import grequests
import redis
import requests
import time
from dateutil.parser import parse

from camfeeder.CamFeeder import CamFeeder


class FrameGrabbingException(Exception):
    def __init__(self, message, errors=None):
        super(FrameGrabbingException, self).__init__(message)
        self.errors = errors


class MJPEGCamFeeder(CamFeeder):
    """
    The MJPEG CamFeeder retrieves the images from the MJPEG stream of a camera.
    Most IP cameras (such as most Logitech models) provide MJPEG streams at particular URLs.
    """

    # If set to True an attempt will be made to re-establish the connection to re-sync when there is a too-long difference
    # between the capture time reported by the remote webcam and the receive-time. This can cause due to limited bandwidth.
    LIVE_DELAY_CONTROL = True
    # Maximum number of seconds of delay before a connection re-establish takes place. Because the webcam.
    # With a 1-second granularity webcams, being lower than 2 could easily trigger unnecessary resyncs.
    LIVE_DELAY_MAX = 2

    WAIT_ON_ERROR = 0.1  # Time to wait when an error occurs.

    def __init__(self, rdb: redis.StrictRedis, redis_prefix: str, cam_name: str, url: str, max_fps: int,
                 rotation: float = None):
        super(MJPEGCamFeeder, self).__init__(rdb, redis_prefix, cam_name, url, max_fps, rotation)

        # For live-delay control. Keeps track of webcam-side time so that we can know how much delay there currently is.
        self._server_sync_time = None  # webcam server-side time
        self._local_sync_time = None  # local time
        self._server_frame_time = None  # last frame time (webcam server-side)
        self._local_frame_time = None  # local frame time (local side)

        self._request_response = None  # type: requests.Response
        self._request_response_boundary = None  # type: str

        self._stats_live_control_restablish = 0

    # Override
    def _push_stats(self):
        """
        Pushes statistics to redis. Is automatically called every once in a while.
        :return:
        """
        super()._push_stats()

        base_key = "{}:cams:{}:stats:".format(self._redis_prefix, self._cam_name)

        self._rdb.setex(base_key + 'cycle_live_control_restablish', CamFeeder.IMAGE_EXPIRE_TIME * 3, self._stats_live_control_restablish)


    def _run_until_inactive(self):
        """
        Will just keep pushing images and checking the active status until
        the camera should not be active anymore.
        :return:
        """

        while self._active:

            need_to_sync = False

            # We cannot control the rate client-side (it is set by the remote webcam) so we have to read
            # as fast as possible.
            gevent.sleep(0)

            self._check_active()

            # Re-establish the connection because we are out of sync?
            live_control_restablish = self.LIVE_DELAY_CONTROL and self._is_too_delayed()

            if self._request_response is None or live_control_restablish:
                try:
                    self._start_streaming_request()
                except Exception as ex:
                    print("Failed to start_streaming request. Cause: {}".format(ex))
                    gevent.sleep(MJPEGCamFeeder.WAIT_ON_ERROR)
                    continue

                # Keep track that we have just established a new connection, so that we store the date in the next
                # frame.
                need_to_sync = True

                # If we just re-established due to a live-control trigger, we register it.
                if live_control_restablish:
                    self._stats_live_control_restablish += 1

            try:
                frame, date = self._parse_next_image()
                if need_to_sync:
                    self._server_sync_time = date
                    self._local_sync_time = time.time()
                self._server_frame_time = date
                self._local_frame_time = time.time()
                frame = self._rotated(frame, self._rotation)
                self._put_frame(frame)
            except Exception as ex:
                print("Restarting connection. Cause: {}".format(ex))
                self._request_response = None
                gevent.sleep(MJPEGCamFeeder.WAIT_ON_ERROR)
                continue

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
            raise FrameGrabbingException(
                'Unexpected length of retrieved image. Expected {} got {}.'.format(content_length, len(image)))

        # Now skip until the boundary is reached.
        while True:
            rawline = self._request_response.raw.readline()
            if len(rawline) == 0:
                # EOF
                raise FrameGrabbingException('No more data received')
            line = rawline.strip()
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
            line = self._request_response.raw.readline()
            if len(line) == 0:
                raise FrameGrabbingException('EOF reached before being able to read headers')
            line = line.strip()
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

    def _is_too_delayed(self) -> bool:
        """
        Checks if the server is providing the images in slower than real time by comparing the webcam-side time elapsed
        since last frame to the local-side.
        :return:
        """
        try:
            elapsed_server_side = (self._server_frame_time - self._server_sync_time).seconds
            elapsed_client_side = self._local_frame_time - self._local_sync_time
        except TypeError:
            return False

        return elapsed_client_side - elapsed_server_side > MJPEGCamFeeder.LIVE_DELAY_MAX
