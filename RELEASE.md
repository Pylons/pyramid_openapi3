# How to release a new version

1. Add a new version to CHANGELOG.md. Browse through https://github.com/niteoweb/pyramid_openapi3/commits/master to see what was done since last release.
1. Set the same version in setup.py.
1. `make tests`
1. `git ci -m "release 0.2.0"`
1. `git status` should be empty.
1. `git tag 0.2.0`
1. `git push --tags && git push origin master`
