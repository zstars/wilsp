/// <reference path="jquery.d.ts" />
var MJPEGNativeCamera = (function () {
    /**
     * Creates a Camera object, that will rely on the native browser's method for rendering MJPEG.
     * Native MJPEG gives us no control over the FPS: it is configured server-side.
     * @param divElement: DIV element within which the camera element will be created.
     * @param MJPEGURL: URL to the MJPEG URL. If undefined, it will be retrieved from the src attribute.
     */
    function MJPEGNativeCamera(divElement, MJPEGURL) {
        this.mDivElement = divElement;
        this.mMJPEGURL = MJPEGURL;
        if (this.mDivElement === undefined)
            throw new Error('A proper MJPEG URL was not provided');
    } // !ctor
    /**
     * Checks whether the refresher is currently running.
     */
    MJPEGNativeCamera.prototype.isRunning = function () {
        return this.mRunning;
    }; // !isRunning
    /**
     * Starts refreshing.
     */
    MJPEGNativeCamera.prototype.start = function () {
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
    }; // !start
    /**
     * Stops refreshing.
     */
    MJPEGNativeCamera.prototype.stop = function () {
        // Just remove the element so that it stops.
        // TODO: Some browsers are reportedly bugged. Check.
        this.mImageElement.remove();
        this.mStoppedTime = Date.now();
    }; // !stop
    /**
     * Retrieves the number of failures in the last active period.
     * @returns {number}
     */
    MJPEGNativeCamera.prototype.getFailures = function () {
        return this.mFailures;
    };
    MJPEGNativeCamera.prototype.onImageLoad = function () {
    }; // !onImageLoad
    MJPEGNativeCamera.prototype.onImageError = function () {
        console.error('Error while loading MJPEG image. Restarting stream in 500 ms.');
        var that = this;
        setTimeout(function () {
            that.stop();
            that.start();
        }, 500);
    }; // !onImageError
    /**
     * Retrieves the provided URL but with an added __ts parameter.
     * @param url
     * @returns {string}
     */
    MJPEGNativeCamera.getTimestampedURL = function (url) {
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
    return MJPEGNativeCamera;
}()); // !Camera
//# sourceMappingURL=mjpeg_native_camera.widget.js.map