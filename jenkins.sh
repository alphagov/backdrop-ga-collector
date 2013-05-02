#!/bin/bash

VIRTUALENV_DIR=/var/tmp/virtualenvs/$(echo ${JOB_NAME} | tr ' ' '-')
PIP_DOWNLOAD_CACHE=/var/tmp/pip_download_cache

basedir=$(dirname $0)

# create empty virtualenv
virtualenv --clear --no-site-packages $VIRTUALENV_DIR
source $VIRTUALENV_DIR/bin/activate

./run_tests.sh
