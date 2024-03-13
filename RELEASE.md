# How to release a new version

1. Set the new version in `pyproject.toml`.
1. `make lock`
1. `make tests`
1. `export VERSION=<new version>`
1. `git add -p && git ci -m "release $VERSION"`
1. `git push origin main` and wait for GitHub Actions to pass the build.
1. `git tag $VERSION`
1. `git push --tags`

The Action should build & test the package, and then upload it to PyPI.
Then, automatically create a new GitHub Release with generated changelog.
