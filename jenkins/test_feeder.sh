
. .pyenv/bin/activate

cd feeder/src
export PYTHONPATH="$PYTHONPATH:$(pwd)"

python test/camfeeder/CamFeederTest.py
python test/camfeeder/ImageRefreshCamFeederTest.py
python test/camfeeder/MJPEGCamFeederTest.py