from flask.ext.socketio import SocketIO

from flask import Flask
from flask.ext.bootstrap import Bootstrap
from flask.ext.redis import FlaskRedis

from config import config

bootstrap = Bootstrap()
socketio = SocketIO()
rdb = FlaskRedis(strict=True)


def create_app(config_name):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)

    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    bootstrap.init_app(app)

    rdb.init_app(app)
    socketio.init_app(app)

    return app
