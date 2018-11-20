#!/bin/bash

PYTHONPATH=$(pwd):$PYTHONPATH
nosetests ./tests/
