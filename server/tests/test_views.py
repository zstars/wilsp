from __future__ import unicode_literals

from flask import Response

from tests.base import BaseTestCase


class TestViewsExps(BaseTestCase):

    CLIENT_PER_TEST = True

    def test_pass(self):
        pass

    def test_imgrefresh_links_script(self):
        """
        Ensure the exp links the right JavaScript even if the cam does not exist.
        :return:
        """
        response = self.client.get('/exps/imgrefresh/not_existing')  # type: Response
        self.assertEquals(response.status_code, 200)

        # The native JS widget is included
        self.assertIn('image_refresh_camera.widget.js', response.data.decode('utf-8'))

    def test_mjpeg_js_links_script(self):
        """
        Ensure the exp links the right JavaScript even if the cam does not exist.
        :return:
        """
        response = self.client.get('/exps/mjpegjs/not_existing')  # type: Response
        self.assertEquals(response.status_code, 200)

        # The MJPEG JS widget is included
        self.assertIn('mjpeg_js_camera.widget.js', response.data.decode('utf-8'))

        # Same for other important ones
        self.assertIn('socket.io', response.data.decode('utf-8'))

    def test_h264_js_links_script(self):
        """
        Ensure the exp links the right JavaScript even if the cam does not exist.
        :return:
        """
        response = self.client.get('/exps/h264js/not_existing')  # type: Response
        self.assertEquals(response.status_code, 200)

        # The H264 JS widget is included
        self.assertIn('264_js_camera.widget.js', response.data.decode('utf-8'))

        # Same for other important ones
        self.assertIn('socket.io', response.data.decode('utf-8'))
