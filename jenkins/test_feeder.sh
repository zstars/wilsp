
. .pyenv/bin/activate

cd feeder/src
export PYTHONPATH="$PYTHONPATH:$(pwd)"

nosetests test/camfeeder/*