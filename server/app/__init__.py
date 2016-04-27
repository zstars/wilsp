
from flask import Flask, render_template
from flask.ext.bootstrap import Bootstrap
from flask.ext.mail import Mail
from flask.ext.moment import Moment
from flask.ext.redis import FlaskRedis
from flask.ext.sqlalchemy import SQLAlchemy
from redis import StrictRedis

from config import config


bootstrap = Bootstrap()
mail = Mail()
moment = Moment()
# db = SQLAlchemy()
rdb = None

def create_app(config_name):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)

    bootstrap.init_app(app)
    mail.init_app(app)
    moment.init_app(app)
    # db.init_app(app)
    global rdb
    rdb = FlaskRedis.from_custom_provider(StrictRedis, app)
    rdb.init_app(app)

    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    return app