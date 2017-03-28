import os

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'this is a secr3t'
    CLIP_DIR = os.environ.get('CLIP_DIR') or os.path.join(basedir, 'data', 'archimedes')

    TYPE = os.environ.get('TYPE', 'sio')
    TFPS = os.environ.get('TFPS', 30)
    NUMBER = os.environ.get('NUMBER', 1)

    @staticmethod
    def init_app(app):
        pass


class DevelopmentConfig(Config):
    DEBUG = True


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
