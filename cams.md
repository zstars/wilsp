This file contains the documentation for the cams.yml YAML file.

The cams.yml file expects the following format:

    cams:
      cam_name_1:
        img_url: str
        mjpeg_url: str
        mpeg: True

The root level is always the 'cams' dictionary, which indexes each offered camera by name.

The key (such as `cam_name_1`) is the name of the camera. It will mainly be used on the URLs that are offered
to the client.

Each camera object can contain a number of keys which represent the sources from which to get images. Not all sources
are required for the camera to work, but depending on which ones are provided, more or less output formats
may be available.

* *img_url* An URL to the webcam's latest provided static image.
* *mjpeg_url* An URL to a MJPEG stream emitted by the camera.
* *mpeg* If set to True a MPEG stream will be generated and offered. Eventally there could be different sources for the stream,
but, for now, if set to True, it will use the same URLs that are specified in img_url or mjpeg_url.




## Image transformations

The main camera endpoints support certain transformations that can be passed as GET parameters, such as:
  - rotate=<value>
  - crop_left
  - crop_right
  - crop_bottom
  - crop_top
