#!/bin/bash
#
# This script is to be used in CircleCI to run tests against the minimal
# supported version of openapi-core.
#
# It replaces the latest version of openapi-core (and its hash) in Pipfile.lock
# file with the minimal supported version. It fails with exit code 1 if
# the latest version (and its hash) were updated in Pipfile.lock and not
# changed here in this script.

set -e

if [[ $(python --version) =~ 3\.7 ]]; then
    echo "Replacing the openapi-core version in Pipfile.lock with the minimal supported version"

    grep "==0.13.7" Pipfile.lock
    sed -i 's/"==0.13.7"/"==0.13.1"/g' Pipfile.lock

    grep "c19afce48fe616dbbab2a56b5d1b14b604cc0bb37d6769421acfb06243ffb6c1" Pipfile.lock
    sed -i s/c19afce48fe616dbbab2a56b5d1b14b604cc0bb37d6769421acfb06243ffb6c1/d61305484f8fefda78fdddaf8890af6804fae99dff94013abd9480873880bddc/g Pipfile.lock
fi
