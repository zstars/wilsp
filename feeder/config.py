import os

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:

    FFMPEG_BIN = "/usr/bin/ffmpeg"

    # Path to the cams definition file
    CAMS_YML = os.environ.get("CAMS_YML", None)

    REDIS_PREFIX = 'wilsa'
    REDIS_HOST = 'localhost'
    REDIS_PORT = 6379
    REDIS_DB = 0

    @staticmethod
    def init_app(app):
        pass


class DevelopmentConfig(Config):
    DEBUG = True

    CAMS_YML = os.environ.get("CAMS_YML", "../cams.yml")


class TestingConfig(Config):
    TESTING = True


class ProductionConfig(Config):
    pass

config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
