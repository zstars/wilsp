var io = require('socket.io-client');

var number = 1;

if(process.argv.length == 3) {
    number = parseInt(process.argv[2]);
}

console.log("Starting for " + number.toString());


for(var i = 0; i < number; i++) {
    (function() {
        var socket = io.connect('http://localhost:5000/h264');

        socket.on('connect', function () {
            console.log("socket connected");

            socket.emit('start', {'cam': 'cam0_0'});
        });

        socket.on('disconnect', function () {
            console.log("socket disconnected");
        });

        socket.on('stream', function (arg) {
            // console.log('stream event received');
        });
    })();
}


