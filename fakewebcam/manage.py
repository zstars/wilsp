#!/usr/bin/env python
import os


from app import create_app
from flask.ext.script import Manager, Shell, Command

app = create_app(os.getenv('FLASK_CONFIG') or 'default')
manager = Manager(app)

def make_shell_context():
    return dict(app=app)

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

if __name__ == '__main__':
    manager.run()
