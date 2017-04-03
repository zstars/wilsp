
# FakeWebcam


## Deploying

To deploy the FakeWebcam you can:

```
gunicorn -w 3 -k gevent -b localhost:8050 wsgi_app:application
```

It will serve a webcam, by default, on:

- http://localhost:8050/fakewebcam/image.mjpeg
- http://localhost:8850/fakewebcam/image.jpg

By default the image will have a QR with the current date as an overlay, which can be useful
to take latency measurements, provided the fakewebcam's and the target server's clocks are synchronized.


