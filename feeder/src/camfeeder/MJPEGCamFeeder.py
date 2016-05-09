from camfeeder.old.CamFeeder import CamFeeder


class MJPEGCamFeeder(CamFeeder):
    """
    The MJPEG CamFeeder retrieves the images from the MJPEG stream of a camera.
    Most IP cameras (such as most Logitech models) provide MJPEG streams at particular URLs.
    """

    def __init__(self, rdb, redis_prefix, cam_name, url, rotation=None):
        super(MJPEGCamFeeder, self).__init__(rdb, redis_prefix, cam_name, url, rotation)

