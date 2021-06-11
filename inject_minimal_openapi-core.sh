#!/bin/bash
#
# This script is to be used in CircleCI to run tests against the minimal
# supported version of openapi-core and Pyramid.
#
# It replaces the latest version of openapi-core/Pyramid (and its hash) in
# Pipfile.lock file with the minimal supported version. It fails with exit
# code 1 if the latest version (and its hash) were updated in Pipfile.lock
# and not changed here in this script.

set -e

if [[ $(python --version) =~ 3\.7 ]]; then
    echo "Replacing the openapi-core version in Pipfile.lock with the minimal supported version"

    grep "==0.13.8" Pipfile.lock
    sed -i 's/"==0.13.8"/"==0.13.4"/g' Pipfile.lock

    grep "1662fef13e90a924570c32685426ba96845bbd7a0ff10ead4b2a675e81d131c5" Pipfile.lock
    sed -i s/1662fef13e90a924570c32685426ba96845bbd7a0ff10ead4b2a675e81d131c5/f2ef90ae4a97a6efa0c47a2e8740afcd378cd478e76e778115a8c0c376e9541e/g Pipfile.lock
fi

if [[ $(python --version) =~ 3\.7 ]]; then
    echo "Replacing the Pyramid version in Pipfile.lock with the minimal supported version"

    grep '"==2.0"' Pipfile.lock
    sed -i 's/"==2.0"/"==1.10.7"/g' Pipfile.lock

    grep "45431b387587ed0fac6213b54d6e9f0936f0cc85238a8f5af7852fc9484c5c77" Pipfile.lock
    sed -i s/45431b387587ed0fac6213b54d6e9f0936f0cc85238a8f5af7852fc9484c5c77/9ad975d336cfe315ab80b3c9b9f4b3af3bc08fe05f7e057265eb1eb1dcdfc48e/g Pipfile.lock
fi
