/// <reference path="typedefs/jquery.d.ts" />
/// <reference path="typedefs/socket.io-client.d.ts" />
var MPEGJSCamera = (function () {
    /**
     * Creates a Camera object, that will rely on HTML5 Canvas and SocketIO for receiving and rendering
     * a MJPEG stream.
     * @param canvasElement: Canvas element on which we will draw.
     * @param socketIOURL: URL to the Socket IO URL. Namespace must be included.
     * @param camName: Name of the camera.
     */
    function MPEGJSCamera(canvasElement, socketIOURL, camName) {
        this.mFailedFrames = 0; // To track the number of successful frames in this period.
        this.mFramesRendered = 0;
        this.mCanvasElement = canvasElement;
        this.mSocketIOURL = socketIOURL;
        this.mCamName = camName;
        if (!(canvasElement instanceof HTMLCanvasElement))
            throw Error('canvasElement must be an HTMLCanvasElement');
        if (camName === undefined)
            throw Error('camName must be defined');
    } // !ctor
    /**
     * Checks whether the camera is currently running.
     */
    MPEGJSCamera.prototype.isRunning = function () {
        return this.mRunning;
    }; // !isRunning
    /**
     * Starts refreshing.
     */
    MPEGJSCamera.prototype.start = function () {
        this.mTimeStarted = Date.now();
        this.mFailedFrames = 0;
        this.mFramesRendered = 0;
        this.mRunning = true;
        var that = this;
        this.mClient = io.connect(this.mSocketIOURL);
        this.mClient.on('connect', function () {
            console.log("Client connected to the server");
            that.mClient.emit('start', { 'cam': that.mCamName });
        });
        this.mJSMPEG = new jsmpeg(that.mClient, { canvas: this.mCanvasElement, useSocketIO: true });
    }; // !start
    /**
     * Gets the average FPS during the current active period or the latest period if we are stopped.
     * @returns {number}
     */
    MPEGJSCamera.prototype.getAverageFPS = function () {
        var finalTime;
        if (this.isRunning())
            finalTime = Date.now();
        else
            finalTime = this.mStoppedTime;
        var elapsed = finalTime - this.mTimeStarted;
        if (elapsed === 0) {
            return 0;
        }
        var fps = this.getSuccessfulFrames() / (elapsed / 1000);
        return fps;
    }; // !getAverageFPS
    /**
     * Stops refreshing.
     */
    MPEGJSCamera.prototype.stop = function () {
        this.mRunning = false;
        this.mClient.close();
        this.mStoppedTime = Date.now();
        this.mJSMPEG.stop();
    }; // !stop
    /**
     * Retrieves the number of successful frames in the last active period.
     */
    MPEGJSCamera.prototype.getSuccessfulFrames = function () {
        return this.mJSMPEG.framesRendered;
    };
    /**
     * Retrieves the provided URL but with an added __ts parameter.
     * @param url
     * @returns {string}
     */
    MPEGJSCamera.getTimestampedURL = function (url) {
        // Get a random str to prevent cache issues.
        var tsr = Math.random().toString();
        // Not very pretty.
        if (url.search("\\?") != -1) {
            return url + "&__ts=" + tsr;
        }
        else {
            return url + "?__ts=" + tsr;
        }
    }; // !getTimestampedURL
    return MPEGJSCamera;
}()); // !Camera
//# sourceMappingURL=mpeg_js_camera.widget.js.map