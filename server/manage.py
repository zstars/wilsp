#!/usr/bin/env python
import os

import flask

from app import create_app, socketio
from flask.ext.script import Manager, Shell, Command

app = create_app(os.getenv('FLASK_CONFIG') or 'default')
manager = Manager(app)


def make_shell_context():
    return dict(app=app)

class RunServerSocketIO(Command):
    """
    Alternative runserver command for socketio compatibility.
    """
    def run(self):
        run()

@manager.command
def run():
   socketio.run(app,
                host='127.0.0.1',
                port=5000,
                use_reloader=True)

@manager.command
def runprod():
    socketio.run(app,
                 host='127.0.0.1',
                 port=8500,
                 use_reloader=False,
                 )

manager.add_command("shell", Shell(make_context=make_shell_context()))
manager.add_command("runserver", RunServerSocketIO())

if __name__ == '__main__':
    manager.run()
