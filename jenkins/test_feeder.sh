
. .pyenv/bin/activate

cd feeder
export PYTHONPATH="$PYTHONPATH:$(pwd)"

nosetests test/feeder/*