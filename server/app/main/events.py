from flask.ext.socketio import emit
from .. import socketio

@socketio.on('connected', namespace='/chat')
def handle_my_custom_event(data):
    print('Received: ' + type(data) + ' : ' + data)
    emit('status', {'msg': 'ok'})

@socketio.on('hello', namespace='/chat')
def handle_hello(data):
    print("HELLO WAS RECEIVED")

@socketio.on('hello')
def handle_hello_nons():
    print("HELLO WITH NO NS")
