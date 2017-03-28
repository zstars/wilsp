import os

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:

    FFMPEG_BIN = os.environ.get("FFMPEG_BIN", "/usr/bin/ffmpeg")

    # Path to the cams definition file
    CAMS_YML = os.environ.get("CAMS_YML", None)

    REDIS_PREFIX = 'wilsa'
    REDIS_HOST = 'localhost'
    REDIS_PORT = 6379
    REDIS_DB = 0

    IMAGE_EXPIRE_TIME = 180

    @staticmethod
    def init_app(app):
        pass


class DevelopmentConfig(Config):
    DEBUG = True

    CAMS_YML = os.environ.get("CAMS_YML", "../cams.yml")


class TestingConfig(Config):
    TESTING = True


class ProductionConfig(Config):
    IMAGE_EXPIRE_TIME = 90

config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
