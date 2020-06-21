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

    grep "==0.13.3" Pipfile.lock
    sed -i 's/"==0.13.3"/"==0.13.1"/g' Pipfile.lock

    grep "57973b7383214a529012cf65ddac8c22b25a4df497366e588e88c627581c2928" Pipfile.lock
    sed -i s/57973b7383214a529012cf65ddac8c22b25a4df497366e588e88c627581c2928/d61305484f8fefda78fdddaf8890af6804fae99dff94013abd9480873880bddc/g Pipfile.lock
fi
