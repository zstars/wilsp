/// <reference path="typedefs/jquery.d.ts" />
var ImageRefreshCamera = (function () {
    /**
     * Creates a Camera object, that will refresh the specified image element
     * by modifying the src attribute.
     * @param imageElement
     * @param targetFPS
     * @param imageURL: URL to the image. If undefined, it will be retrieved from the src attribute.
     */
    function ImageRefreshCamera(imageElement, targetFPS, imageURL) {
        if (imageURL === void 0) { imageURL = undefined; }
        this.mImageElement = imageElement;
        this.setTargetFPS(targetFPS);
        if (imageURL !== undefined)
            this.mImageURL = imageURL;
        else
            this.mImageURL = this.mImageElement.src;
        if (this.mImageElement === undefined)
            throw new Error('A proper image URL was not provided, and one could not be obtained from the src attribute');
    } // !ctor
    /**
     * Checks whether the refresher is currently running.
     */
    ImageRefreshCamera.prototype.isRunning = function () {
        return this.mRefreshTimeout !== undefined;
    }; // !isRunning
    /**
     * Starts refreshing.
     */
    ImageRefreshCamera.prototype.start = function () {
        this.mTimeStarted = Date.now();
        this.mFramesRendered = 0;
        this.mFailedFrames = 0;
        this.mLastFrameTimeStart = 0;
        // Set the event handlers for the 'load' and 'error' event.
        jQuery(this.mImageElement).on('load', this.onImageLoad.bind(this));
        jQuery(this.mImageElement).on('error', this.onImageError.bind(this));
        this.refresh();
    }; // !start
    /**
     * Stops refreshing.
     */
    ImageRefreshCamera.prototype.stop = function () {
        clearTimeout(this.mRefreshTimeout);
        this.mStoppedTime = Date.now();
    }; // !stop
    /**
     * Resets the FPS counter.
     */
    ImageRefreshCamera.prototype.resetFPS = function () {
        this.mTimeStarted = Date.now();
        this.mFramesRendered = 0;
        this.mFailedFrames = 0;
        this.mLastFrameTimeStart = 0;
    }; // !resetFPS
    /**
     * Retrieves the FPS that has been achieved in the current start-refresh period.
     * If the refresher is not running, then the last period's average FPS is returned.
     * If no time has elapsed, 0 is returned.
     */
    ImageRefreshCamera.prototype.getAverageFPS = function () {
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
     * Retrieves the number of failed frames in the last active period.
     * @returns {number}
     */
    ImageRefreshCamera.prototype.getFailedFrames = function () {
        return this.mFailedFrames;
    };
    /**
     * Retrieves the number of successful frames in the last active period.
     */
    ImageRefreshCamera.prototype.getSuccessfulFrames = function () {
        return this.mFramesRendered;
    };
    /**
     * Changes the target FPS.
     * @param fps
     */
    ImageRefreshCamera.prototype.setTargetFPS = function (fps) {
        this.mTimeStarted = Date.now();
        this.mTargetFPS = fps;
        this.mFramesRendered = 0;
        this.mFailedFrames = 0;
        this.mTargetTimePerFrame = 1 / this.mTargetFPS;
    }; // !setTargetFPS
    ImageRefreshCamera.prototype.onImageLoad = function () {
        var elapsedMs = Date.now() - this.mLastFrameTimeStart;
        this.mFramesRendered += 1;
        var sleep = this.mTargetTimePerFrame - elapsedMs / 1000;
        if (sleep < 0)
            sleep = 0;
        this.mRefreshTimeout = setTimeout(this.refresh.bind(this), sleep * 1000);
    }; // !onImageLoad
    ImageRefreshCamera.prototype.onImageError = function () {
        var elapsedMs = Date.now() - this.mLastFrameTimeStart;
        this.mFailedFrames += 1;
        var sleep = this.mTargetTimePerFrame - elapsedMs / 1000;
        if (sleep < 0)
            sleep = 0;
        this.mRefreshTimeout = setTimeout(this.refresh.bind(this), sleep * 1000);
    }; // !onImageError
    /**
     * Refreshes the src attribute of the image. Calls itself with a certain frequency that
     * depends on the targetFPS.
     */
    ImageRefreshCamera.prototype.refresh = function () {
        // Change the image.
        this.mLastFrameTimeStart = Date.now();
        this.mImageElement.src = ImageRefreshCamera.getTimestampedURL(this.mImageURL);
    }; // !refresh
    /**
     * Retrieves the provided URL but with an added __ts parameter.
     * @param url
     * @returns {string}
     */
    ImageRefreshCamera.getTimestampedURL = function (url) {
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
    return ImageRefreshCamera;
}()); // !Camera
//# sourceMappingURL=image_refresh_camera.widget.js.map