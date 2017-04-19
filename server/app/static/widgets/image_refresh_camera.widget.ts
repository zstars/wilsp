/// <reference path="typedefs/jquery.d.ts" />

class ImageRefreshCamera
{
    private mImageElement : HTMLImageElement;
    private mTargetFPS : number;
    private mImageURL : string;
    private mTargetTimePerFrame : number;

    private mTimeStarted : number;
    private mFramesRendered : number;
    private mFailedFrames : number;
    private mLastFrameTimeStart : number; // TS of the last frame start (src change time).
    private mStoppedTime : number; // Time the refresher was stopped, to calc FPS when not active.

    private mRefreshTimeout : number; // Identifier for the currently active refresh timeout.

    /**
     * Creates a Camera object, that will refresh the specified image element
     * by modifying the src attribute.
     * @param imageElement
     * @param targetFPS
     * @param imageURL: URL to the image. If undefined, it will be retrieved from the src attribute.
     */
    public constructor(imageElement: HTMLImageElement, targetFPS: number, imageURL: string = undefined)
    {
        this.mImageElement = imageElement;

        this.setTargetFPS(targetFPS);

        if(imageURL !== undefined)
            this.mImageURL = imageURL;
        else
            this.mImageURL = this.mImageElement.src;

        if(this.mImageElement === undefined)
            throw new Error('A proper image URL was not provided, and one could not be obtained from the src attribute');
    } // !ctor

    /**
     * Checks whether the refresher is currently running.
     */
    public isRunning() : boolean
    {
        return this.mRefreshTimeout !== undefined;
    } // !isRunning

    /**
     * Starts refreshing.
     */
    public start()
    {
        this.mTimeStarted = Date.now();
        this.mFramesRendered = 0;
        this.mFailedFrames = 0;
        this.mLastFrameTimeStart = 0;

        // Set the event handlers for the 'load' and 'error' event.
        jQuery(this.mImageElement).on('load', this.onImageLoad.bind(this));
        jQuery(this.mImageElement).on('error', this.onImageError.bind(this));

        this.refresh();
    } // !start

    /**
     * Stops refreshing.
     */
    public stop()
    {
        clearTimeout(this.mRefreshTimeout);
        this.mStoppedTime = Date.now();
    } // !stop

    /**
     * Resets the FPS counter.
     */
    public resetFPS()
    {
        this.mTimeStarted = Date.now();
        this.mFramesRendered = 0;
        this.mFailedFrames = 0;
        this.mLastFrameTimeStart = 0;
    } // !resetFPS

    /**
     * Retrieves the FPS that has been achieved in the current start-refresh period.
     * If the refresher is not running, then the last period's average FPS is returned.
     * If no time has elapsed, 0 is returned.
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
     * Changes the target FPS.
     * @param fps
     */
    public setTargetFPS(fps: number): void
    {
        this.mTimeStarted = Date.now();
        this.mTargetFPS = fps;
        this.mFramesRendered = 0;
        this.mFailedFrames = 0;
        this.mTargetTimePerFrame = 1 / this.mTargetFPS;
    } // !setTargetFPS

    private onImageLoad()
    {
        let elapsedMs: number = Date.now() - this.mLastFrameTimeStart;
        this.mFramesRendered += 1;

        let sleep: number = this.mTargetTimePerFrame - elapsedMs / 1000;
        if(sleep < 0)
            sleep = 0;

        this.mRefreshTimeout = setTimeout(this.refresh.bind(this), sleep * 1000);
    } // !onImageLoad

    private onImageError()
    {
        let elapsedMs: number = Date.now() - this.mLastFrameTimeStart;
        this.mFailedFrames += 1;

        let sleep: number = this.mTargetTimePerFrame - elapsedMs / 1000;
        if(sleep < 0)
            sleep = 0;

        this.mRefreshTimeout = setTimeout(this.refresh.bind(this), sleep * 1000);
    } // !onImageError

    /**
     * Refreshes the src attribute of the image. Calls itself with a certain frequency that
     * depends on the targetFPS.
     */
    private refresh()
    {
        // Change the image.
        this.mLastFrameTimeStart = Date.now();
        this.mImageElement.src = ImageRefreshCamera.getTimestampedURL(this.mImageURL);
    } // !refresh

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