/// <reference path="typedefs/jquery.d.ts" />
/// <reference path="typedefs/socket.io-client.d.ts" />
var H264JSCamera = (function () {
    /**
     * Creates a Camera object, that will rely on HTML5 Canvas and SocketIO for receiving and rendering
     * a MJPEG stream.
     * @param canvasElement: Canvas element on which we will draw.
     * @param socketIOURL: URL to the Socket IO URL. Namespace must be included.
     * @param camName: Name of the camera.
     * @param socketIOPath: The specific socketio path. This is used in case the /socket.io endpoint is not located
     * in the domain's root.
     */
    function H264JSCamera(canvasElement, socketIOURL, camName, socketIOPath) {
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
        if (socketIOPath == undefined) {
            this.mSocketIOPath = "";
        }
    } // !ctor
    /**
     * Checks whether the camera is currently running.
     */
    H264JSCamera.prototype.isRunning = function () {
        return this.mRunning;
    }; // !isRunning
    /**
     * Starts refreshing.
     */
    H264JSCamera.prototype.start = function () {
        this.mTimeStarted = Date.now();
        this.mFailedFrames = 0;
        this.mFramesRendered = 0;
        this.mRunning = true;
        var that = this;
        this.mClient = io.connect(this.mSocketIOURL, { path: this.mSocketIOPath });
        console.debug("Connecting to URL: " + this.mSocketIOURL);
        console.debug("Connecting to Socket IO Path: " + this.mSocketIOPath);
        this.mClient.on('connect', function () {
            console.log("Client connected to the server");
            that.mClient.emit('start', { 'cam': that.mCamName });
            that.mWSAvc = new WSAvcPlayer(that.mCanvasElement, "webgl", 1, 35);
            // Force a Canvas initialization. The original player does not do this. Instead, it waits for the
            // init 'cmd' sent by the server. It should work, though.
            that.mWSAvc.initCanvas(that.mCanvasElement.width, that.mCanvasElement.height);
            that.mWSAvc.connect(that.mClient);
            // window.wsavc = wsavc;    TODO: Remove this if it proves non-needed.
            // this.mWSAvc.playStream();
        });
    }; // !start
    /**
     * Gets the average FPS during the current active period or the latest period if we are stopped.
     * @returns {number}
     */
    H264JSCamera.prototype.getAverageFPS = function () {
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
    H264JSCamera.prototype.stop = function () {
        this.mRunning = false;
        this.mClient.close();
        this.mStoppedTime = Date.now();
        this.mWSAvc.stopStream();
    }; // !stop
    /**
     * Resets the FPS counter.
     */
    H264JSCamera.prototype.resetFPS = function () {
        this.mTimeStarted = Date.now();
        this.mFramesRendered = 0;
        this.mFailedFrames = 0;
    }; // !resetFPS
    /**
     * Retrieves the number of successful frames in the last active period.
     */
    H264JSCamera.prototype.getSuccessfulFrames = function () {
        // TODO: Implement this.
        return 0;
        // return this.mJSMPEG.framesRendered;
    };
    return H264JSCamera;
}()); // !Camera
//# sourceMappingURL=h264_js_camera.widget.js.map