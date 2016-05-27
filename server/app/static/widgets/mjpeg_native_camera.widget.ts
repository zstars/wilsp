/// <reference path="typedefs/jquery.d.ts" />

class MJPEGNativeCamera
{
    private mDivElement : HTMLDivElement;
    private mMJPEGURL : string;

    private mRunning : boolean;

    private mTimeStarted : number;
    private mFailures : number; // To track the number of times we have to restart the stream somehow.
    private mStoppedTime : number; // Time the refresher was stopped, to calc FPS when not active.

    private mImageElement : HTMLImageElement;


    /**
     * Creates a Camera object, that will rely on the native browser's method for rendering MJPEG.
     * Native MJPEG gives us no control over the FPS: it is configured server-side.
     * @param divElement: DIV element within which the camera element will be created.
     * @param MJPEGURL: URL to the MJPEG URL. If undefined, it will be retrieved from the src attribute.
     */
    public constructor(divElement: HTMLDivElement, MJPEGURL: string)
    {
        this.mDivElement = divElement;
        this.mMJPEGURL = MJPEGURL;

        if(this.mDivElement === undefined)
            throw new Error('A proper MJPEG URL was not provided');
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

        this.mImageElement = document.createElement('img');

        // Set the event handlers for the 'load' and 'error' event.
        jQuery(this.mDivElement).on('load', this.onImageLoad.bind(this));
        jQuery(this.mDivElement).on('error', this.onImageError.bind(this));

        // Create the nested element.
        this.mImageElement.src = this.mMJPEGURL;
        this.mDivElement.appendChild(this.mImageElement);
    } // !start

    /**
     * Stops refreshing.
     */
    public stop()
    {
        this.mRunning = false;

        // Just remove the element so that it stops.
        // TODO: Some browsers are reportedly bugged. Check.
        this.mImageElement.remove();

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