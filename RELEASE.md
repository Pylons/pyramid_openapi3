# How to release a new version

1. Set the new version in `pyproject.toml`.
1. `make lock`
1. `make tests`
1. `export VERSION=<new version>`
1. `git add -p && git ci -m "release $VERSION"`
1. `git push origin main` and wait for GitHub Actions to pass the build.
1. `gh release create $VERSION --target main --generate-notes`

Publishing the GitHub Release triggers the Release workflow, which builds the
package, uploads it to PyPI, and attaches the distribution files to the release.
Then go to https://github.com/Pylons/pyramid_openapi3/releases/ and edit the
latest release to remove cleanup/unnecessary items from the description.
