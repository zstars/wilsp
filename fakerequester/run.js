var io = require('socket.io-client');
var request = require('request');
var argv = require('yargs')
	.usage('Usage: $0 -w [num] -u [u] -t [type]')
    .demandOption(['w'])
    .default({ u: "localhost:5000", t: "img"})
    .argv;


var type = argv.t;

if(type != "img" && type != "h264") {
    console.log("Unrecognized type.");
    process.exit(1);
}


var url = undefined;
// if (type == "img") {
//    url = "http://" + argv.u + "/cams/cams_0_0";
// } else {
//    url = "http://" + argv.u + "/264";
// }
url = argv.u;

console.log("Starting for " + argv.w.toString() + " and type " + argv.t + " and url " + argv.u);


for(var i = 0; i < argv.w; i++) {

    if(type == "h264") {
        (function () {
            var socket = io.connect(url);

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
            var errors = 0;
            var programStartTime = Date.now();
            var lastPrint = Date.now();

            var cycle = function () {
                var updateStartTime = Date.now();
                (function () {
                    request(url, function (error, response, body) {
                        if(error)
                            errors += 1;
                        else
                            count++;
                        var now = Date.now();
                        var elapsed = now - updateStartTime;
                        var time_left = period - elapsed;

                        setTimeout(cycle, time_left);

                        // Print at most every 5 seconds.
                        var sincePrint = now - lastPrint;
                        if(sincePrint > 4*1000) {

                            if(body == undefined) {
                                body = {length: 0};
                            }
                            var logentry = "W: " + argv.w + " | L: " + body.length + " | Frames: " + count.toString() + " | FPS: " + (count / ((Date.now() - programStartTime) / 1000)).toString() + " | Errors: " + errors.toString();
                            console.log(logentry);
                            lastPrint = now;
                        }
                    });
                })();
            };

            cycle();
        })();
    }
}


