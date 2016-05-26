/// <reference path="jquery.d.ts" />
/// <reference path="socket.io-client.d.ts" />


import Socket = SocketIOClient.Socket;

class MJPEGJSCamera
{
    private mCanvasElement : HTMLCanvasElement;
    private mSocketIOURL : string;
    private mCamName : string;

    private mClient : Socket;

    private mRunning : boolean;

    private mTimeStarted : number;
    private mFailures : number; // To track the number of times we have to restart the stream somehow.
    private mStoppedTime : number; // Time the refresher was stopped, to calc FPS when not active.


    /**
     * Creates a Camera object, that will rely on HTML5 Canvas and SocketIO for receiving and rendering
     * a MJPEG stream.
     * @param canvasElement: Canvas element on which we will draw.
     * @param mSocketIOURL: URL to the Socket IO URL. Namespace must be included.
     */
    public constructor(canvasElement: HTMLCanvasElement, mSocketIOURL: string, camName: string)
    {
        this.mCanvasElement = canvasElement;
        this.mSocketIOURL = mSocketIOURL;
        this.mCamName = camName;
    } // !ctor

    /**
     * Checks whether the camera is currently running.
     */
    public isRunning() : boolean
    {
        return this.mRunning;
    } // !isRunning

    /**
     * Starts refreshing.
     */
    public start()
    {
        this.mTimeStarted = Date.now();
        this.mFailures = 0;
        this.mRunning = true;

        // Connect to the socketio URL.
        this.mClient = io.connect(this.mSocketIOURL);

		this.mClient.on('connect', function () {
            console.log("Client connected to the server");
            this.mClient.emit('start', {'cam': this.mCamName});
        });

        // TODO:
    } // !start

    /**
     * Stops refreshing.
     */
    public stop()
    {
        this.mClient.close();

        this.mStoppedTime = Date.now();
    } // !stop

    /**
     * Retrieves the number of failures in the last active period.
     * @returns {number}
     */
    public getFailures(): number
    {
        return this.mFailures;
    }

    private onImageLoad()
    {
    } // !onImageLoad

    private onImageError()
    {
        console.error('Error while loading MJPEG image. Restarting stream in 500 ms.');

        let that = this;

        setTimeout(function() {
            that.stop();
            that.start();
        }, 500);
    } // !onImageError

    /**
     * Retrieves the provided URL but with an added __ts parameter.
     * @param url
     * @returns {string}
     */
    private static getTimestampedURL(url: string): string
    {
        // Get a random str to prevent cache issues.
        let tsr: string = Math.random().toString();

        // Not very pretty.
        if (url.search("\\?") != -1) {
            return url + "&__ts=" + tsr;
        } else {
            return url + "?__ts=" + tsr;
        }
    } // !getTimestampedURL

} // !Camera