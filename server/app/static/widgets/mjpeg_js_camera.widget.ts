/// <reference path="typedefs/jquery.d.ts" />
/// <reference path="typedefs/socket.io-client.d.ts" />


import Socket = SocketIOClient.Socket;

class MJPEGJSCamera
{
    private mCanvasElement : HTMLCanvasElement;
    private mSocketIOURL : string;
    private mSocketIOPath: string;
    private mCamName : string;

    private mClient : Socket;

    private mRunning : boolean;

    private mTimeStarted : number;
    private mFailedFrames : number = 0; // To track the number of successful frames in this period.
    private mFramesRendered : number = 0;
    private mStoppedTime : number; // Time the refresher was stopped, to calc FPS when not active.


    /**
     * Creates a Camera object, that will rely on HTML5 Canvas and SocketIO for receiving and rendering
     * a MJPEG stream.
     * @param canvasElement: Canvas element on which we will draw.
     * @param socketIOURL: URL to the Socket IO URL. Namespace must be included.
     * @param camName: Name of the camera.
     * @param socketIOPath: Path to the socketio endpoint. Optional.
     */
    public constructor(canvasElement: HTMLCanvasElement, socketIOURL: string, camName: string, socketIOPath: string)
    {
        this.mCanvasElement = canvasElement;
        this.mSocketIOURL = socketIOURL;
        this.mCamName = camName;
        this.mSocketIOPath = socketIOPath;

        if(!(canvasElement instanceof HTMLCanvasElement))
            throw Error('canvasElement must be an HTMLCanvasElement');
        if(camName === undefined)
            throw Error('camName must be defined');
        if(socketIOPath === undefined)
            this.mSocketIOPath = "";
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
        this.mFailedFrames = 0;
        this.mFramesRendered = 0;
        this.mRunning = true;

        // Connect to the socketio URL.
        this.mClient = io.connect(this.mSocketIOURL, {path: this.mSocketIOPath, transports: ['polling']});

        let that = this;
		this.mClient.on('connect', function () {
            console.log("Client connected to the server");
            that.mClient.emit('start', {'cam': that.mCamName});
        });

        this.mClient.on('frame', this.onFrameReceived.bind(this));
    } // !start


    /**
     * Called when new frame data is received and should be rendered.
     * @param imageData
     */
    private onFrameReceived(imageData: ArrayBuffer)
    {
        let ctx:CanvasRenderingContext2D = this.mCanvasElement.getContext("2d");

        let imageDataBytes = new Uint8Array(imageData);
        var b64encoded = btoa(String.fromCharCode.apply(null, imageDataBytes));

        var img = new Image();
        img.src = "data:image/png;base64," + b64encoded;

        img.onload = () => {
            ctx.drawImage(img, 0, 0, 640, 480);
            this.mFramesRendered += 1;
        };

        img.onerror = () => {
            console.error("[mjpeg]: Image error");
            this.mFailedFrames += 1;
        };
    } // !onFrameReceived

    /**
     * Gets the average FPS during the current active period or the latest period if we are stopped.
     * @returns {number}
     */
    public getAverageFPS(): number
    {
        let finalTime : number;
        if(this.isRunning())
            finalTime = Date.now();
        else
            finalTime = this.mStoppedTime;

        let elapsed : number = finalTime - this.mTimeStarted;
        if(elapsed === 0)
        {
            return 0;
        }

        let fps : number = this.mFramesRendered / (elapsed/1000);
        return fps;
    } // !getAverageFPS

    /**
     * Stops refreshing.
     */
    public stop()
    {
        this.mRunning = false;
        this.mClient.close();
        this.mStoppedTime = Date.now();
    } // !stop

    /**
     * Retrieves the number of failed frames in the last active period.
     * @returns {number}
     */
    public getFailedFrames(): number
    {
        return this.mFailedFrames;
    }

    /**
     * Retrieves the number of successful frames in the last active period.
     */
    public getSuccessfulFrames(): number
    {
        return this.mFramesRendered;
    }

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