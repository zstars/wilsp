/// <reference path="typedefs/jquery.d.ts" />
/// <reference path="typedefs/socket.io-client.d.ts" />
var MJPEGJSCamera = (function () {
    /**
     * Creates a Camera object, that will rely on HTML5 Canvas and SocketIO for receiving and rendering
     * a MJPEG stream.
     * @param canvasElement: Canvas element on which we will draw.
     * @param socketIOURL: URL to the Socket IO URL. Namespace must be included.
     * @param camName: Name of the camera.
     * @param socketIOPath: Path to the socketio endpoint. Optional.
     * @param targetFPS: Target FPS to ask from the server. Optional. Default: 5.
     */
    function MJPEGJSCamera(canvasElement, socketIOURL, camName, socketIOPath, targetFPS) {
        this.mFailedFrames = 0; // To track the number of successful frames in this period.
        this.mFramesRendered = 0;
        this.mCanvasElement = canvasElement;
        this.mSocketIOURL = socketIOURL;
        this.mCamName = camName;
        this.mSocketIOPath = socketIOPath;
        if (!(canvasElement instanceof HTMLCanvasElement))
            throw Error('canvasElement must be an HTMLCanvasElement');
        if (camName === undefined)
            throw Error('camName must be defined');
        if (socketIOPath === undefined)
            this.mSocketIOPath = "";
        if (targetFPS === undefined)
            this.mTargetFPS = 5;
    } // !ctor
    /**
     * Checks whether the camera is currently running.
     */
    MJPEGJSCamera.prototype.isRunning = function () {
        return this.mRunning;
    }; // !isRunning
    /**
     * Starts refreshing.
     */
    MJPEGJSCamera.prototype.start = function () {
        this.mTimeStarted = Date.now();
        this.mFailedFrames = 0;
        this.mFramesRendered = 0;
        this.mRunning = true;
        // Connect to the socketio URL.
        this.mClient = io.connect(this.mSocketIOURL, { path: this.mSocketIOPath });
        var that = this;
        this.mClient.on('connect', function () {
            console.log("Client connected to the server");
            that.mClient.emit('start', { 'cam': that.mCamName, 'tfps': that.mTargetFPS });
        });
        this.mClient.on('frame', this.onFrameReceived.bind(this));
    }; // !start
    /**
     * Called when new frame data is received and should be rendered.
     * @param imageData
     */
    MJPEGJSCamera.prototype.onFrameReceived = function (imageData) {
        var _this = this;
        var ctx = this.mCanvasElement.getContext("2d");
        var imageDataBytes = new Uint8Array(imageData);
        var b64encoded = btoa(String.fromCharCode.apply(null, imageDataBytes));
        var img = new Image();
        img.src = "data:image/png;base64," + b64encoded;
        img.onload = function () {
            ctx.drawImage(img, 0, 0, 640, 480);
            _this.mFramesRendered += 1;
        };
        img.onerror = function () {
            console.error("[mjpeg]: Image error");
            _this.mFailedFrames += 1;
        };
    }; // !onFrameReceived
    /**
     * Gets the average FPS during the current active period or the latest period if we are stopped.
     * @returns {number}
     */
    MJPEGJSCamera.prototype.getAverageFPS = function () {
        var finalTime;
        if (this.isRunning())
            finalTime = Date.now();
        else
            finalTime = this.mStoppedTime;
        var elapsed = finalTime - this.mTimeStarted;
        if (elapsed === 0) {
            return 0;
        }
        var fps = this.mFramesRendered / (elapsed / 1000);
        return fps;
    }; // !getAverageFPS
    /**
     * Stops refreshing.
     */
    MJPEGJSCamera.prototype.stop = function () {
        this.mRunning = false;
        this.mClient.close();
        this.mStoppedTime = Date.now();
    }; // !stop
    /**
     * Retrieves the number of failed frames in the last active period.
     * @returns {number}
     */
    MJPEGJSCamera.prototype.getFailedFrames = function () {
        return this.mFailedFrames;
    };
    /**
     * Retrieves the number of successful frames in the last active period.
     */
    MJPEGJSCamera.prototype.getSuccessfulFrames = function () {
        return this.mFramesRendered;
    };
    /**
     * Retrieves the provided URL but with an added __ts parameter.
     * @param url
     * @returns {string}
     */
    MJPEGJSCamera.getTimestampedURL = function (url) {
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
    return MJPEGJSCamera;
}()); // !Camera
//# sourceMappingURL=mjpeg_js_camera.widget.js.map