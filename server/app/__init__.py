from gevent import monkey
monkey.patch_all()

from flask_socketio import SocketIO
from flask import Flask
from flask_bootstrap import Bootstrap
from flask_mail import Mail
from flask_moment import Moment
from flask_redis import FlaskRedis

from config import config

bootstrap = Bootstrap()
mail = Mail()
moment = Moment()
# db = SQLAlchemy()
socketio = SocketIO()
rdb = FlaskRedis(strict=True)


def create_app(config_name):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)

    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    bootstrap.init_app(app)
    mail.init_app(app)
    moment.init_app(app)
    # db.init_app(app)

    rdb.init_app(app)
    socketio.init_app(app, async_mode='gevent', engine_io_logger=True)

    return app