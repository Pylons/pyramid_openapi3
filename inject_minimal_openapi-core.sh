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

    grep "==0.13.4" Pipfile.lock
    sed -i 's/"==0.13.4"/"==0.13.1"/g' Pipfile.lock

    grep "b8b4283d84038495fb3bde4a868cd9377272ecf898f142d7706d6d49fc14d218" Pipfile.lock
    sed -i s/b8b4283d84038495fb3bde4a868cd9377272ecf898f142d7706d6d49fc14d218/d61305484f8fefda78fdddaf8890af6804fae99dff94013abd9480873880bddc/g Pipfile.lock
fi
