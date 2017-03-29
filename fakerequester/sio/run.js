var io = require('socket.io-client');

console.log("Starting");

var socket = io.connect('http://localhost:5000/h264');

socket.on('connect', function () {
    console.log("socket connected");

    socket.emit('start', {'cam': 'cam0_0'});
});

socket.on('disconnect', function () {
    console.log("socket disconnected");
});

socket.on('stream', function (arg) {
    console.log('stream event received');
});


var socket2 = io.connect('http://localhost:5000/h264');

socket2.on('connect', function () {
    console.log("socket2 connected");

    socket2.emit('start', {'cam': 'cam0_0'});
});

socket2.on('disconnect', function () {
    console.log("socket2 disconnected");
});

socket2.on('stream', function (arg) {
    console.log('stream event received 2');
});


