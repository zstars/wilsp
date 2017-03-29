var io = require('socket.io-client');
var request = require('request');

var number = 1;
var type = "img";

var IMG_URL = "http://localhost:5000/exps/imgrefresh/cam0_0"

if(process.argv.length == 4) {
    number = parseInt(process.argv[2]);
    type = process.argv[3];

    if(type != "img" && type != "h264") {
        console.log("Unrecognized type.");
        process.exit(1);
    }
}

console.log("Starting for " + number.toString() + " and type " + type);


for(var i = 0; i < number; i++) {

    if(type == "h264") {
        (function () {
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
    } else {
        (function() {
            var period = 1000 / 30; // 30 FPS target
            var count = 0;
            var programStartTime = Date.now();

            var cycle = function () {
                var updateStartTime = Date.now();
                (function () {
                    request(IMG_URL, function (error, response, body) {
                        count++;
                        var elapsed = Date.now() - updateStartTime;
                        var time_left = period - elapsed;

                        setTimeout(cycle, time_left);

                        console.log("Frames: " + count.toString() + " | FPS: " + (count / ((Date.now() - programStartTime) / 1000)).toString());
                    });
                })();
            };

            cycle();
        })();
    }
}


