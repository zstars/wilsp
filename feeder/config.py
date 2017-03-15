import os

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:

    FFMPEG_BIN = "/usr/bin/ffmpeg"
    CAMS_YML = os.environ.get("CAMS_YML", None)

    @staticmethod
    def init_app(app):
        pass


class DevelopmentConfig(Config):
    DEBUG = True

    # Path to the cams definition file
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
