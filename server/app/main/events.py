import gevent
from flask.ext.socketio import emit

from app.main.SocketIOMJPEGBroadcaster import SocketIOMJPEGBroadcaster
from app.main.SocketIOMPEGBroadcaster import SocketIOMPEGBroadcaster
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

@socketio.on('connected', namespace='/stream')
def connected_stream(data):
    print('Connected to stream')
    emit('status', {'msg': 'connected indeed'})

    # Start the broadcaster
    t = SocketIOMPEGBroadcaster()
    gevent.spawn(t.run)

@socketio.on('connected', namespace='/mjpeg_stream')
def connected_mjpeg_stream(data):
    print('Connected to MJPEG stream')
    emit('status', {'msg': 'connected indeed'})

    # Start the broadcaster
    t = SocketIOMJPEGBroadcaster()
    gevent.spawn(t.run)