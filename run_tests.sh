#!/bin/bash

set -o pipefail

function display_result {
    RESULT=$1
    EXIT_STATUS=$2
    TEST=$3

    if [ $RESULT -ne 0 ]; then
      echo
      echo -e "\033[31m$TEST failed\033[0m"
      echo
      exit $EXIT_STATUS
    else
      echo
      echo -e "\033[32m$TEST passed\033[0m"
      echo
    fi
}

basedir=$(dirname $0)
outdir="$basedir/out"

# cleanup output dir
mkdir -p "$outdir"
rm -f "$outdir/*"
rm -f ".coverage"

# install python packages
pip install -r requirements_for_tests.txt

# run unit tests
nosetests -v --with-xunit --with-coverage --cover-package=collector --xunit-file=$outdir/nosetests.xml
display_result $? 1 "Unit tests"
python -m coverage.__main__ xml --include=collector* -o "$outdir/coverage.xml"

# run style check
$basedir/pep-it.sh | tee "$outdir/pep8.out"
display_result $? 3 "Code style check"

