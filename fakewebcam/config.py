import os


basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'this is a secr3t'
    CLIP_DIR = os.environ.get('CLIP_DIR') or os.path.join(basedir, 'data', 'archimedes')

    MJPEG_FPS = 30

    # Note that this takes a significant amount of resources, which can affect the benchmark if the
    # fakewebcamserver is running in the same computer. (It can reduce the FPS from 30 to 25 with only 8 cams).
    EMBED_QR = True

    # Every how often we will embed a QR. 1 for every time. 30 for once every 30 frames. And so on.
    EMBED_QR_FREQ = 10

    @staticmethod
    def init_app(app):
        pass


class DevelopmentConfig(Config):
    DEBUG = True


class TestingConfig(Config):
    TESTING = True


class ProductionConfig(Config):
    pass

class BenchmarkConfig(Config):
    pass

config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'benchmark': BenchmarkConfig,
    'default': DevelopmentConfig
}
