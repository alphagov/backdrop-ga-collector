#!/bin/bash

set -e

projectdir=$(dirname $0)
pep8 --ignore=E201,E202,E241,E251 --exclude=tests "$projectdir"
pep8 --ignore=E201,E202,E241,E251,E501 "$projectdir/tests"
