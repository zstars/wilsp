from camfeeder.old.CamFeeder import CamFeeder


class ImageRefreshCamFeeder(CamFeeder):
    """
    The ImageRefreshCamFeeder retrieves images by simply repeteadly requesting the image URL of the camera.
    (Most IP cameras provide such an URL).
    """

    def __init__(self, rdb, redis_prefix, cam_name, url, rotation=None):
        super(ImageRefreshCamFeeder, self).__init__(rdb, redis_prefix, cam_name, url, rotation)