
class MJPEGRenderer
{
    private mCanvas: HTMLCanvasElement;

    public constructor(canvas : HTMLCanvasElement)
    {
        console.log("Now constructing MJPEG Renderer");

        this.mCanvas = canvas;
    } // !ctor

    public RenderFrame(imageData: Uint8Array)
    {
        var ctx:CanvasRenderingContext2D = this.mCanvas.getContext("2d");

        var b64encoded = btoa(String.fromCharCode.apply(null, imageData));

        var img = new Image();
        img.src = "data:image/png;base64," + b64encoded;

        img.onload = () => {
            console.log("Image Onload");
            ctx.drawImage(img, 0, 0, 640, 480);
        };

        img.onerror = () => {
            console.log("Img Onerror");
        };
    } // !RenderFrame
} // !class