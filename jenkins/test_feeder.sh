
. .pyenv/bin/activate

cd feeder/src
export PYTHONPATH="$PYTHONPATH:$(pwd)"

python feeder/src/test/camfeeder/CamFeederTest.py
python feeder/src/test/camfeeder/ImageRefreshCamFeederTest.py
python feeder/src/test/camfeeder/MJPEGCamFeederTest.py