# Contributing

All projects under the Pylons Project, including this one, follow the guidelines established at [How to Contribute](https://pylonsproject.org/community-how-to-contribute.html), [Coding Style and Standards](https://pylonsproject.org/community-coding-style-standards.html), and [Pylons Project Documentation Style Guide](https://docs.pylonsproject.org/projects/docs-style-guide/).

You can contribute to this project in several ways.

*   [File an Issue on GitHub](https://github.com/Pylons/pyramid_openapi3/issues)
*   Fork this project, create a new branch, commit your suggested change, and push to your fork on GitHub.
    When ready, submit a pull request for consideration.
    [GitHub Flow](https://guides.github.com/introduction/flow/index.html) describes the workflow process and why it's a good practice.
*   Join the [IRC channel #pyramid on irc.freenode.net](https://webchat.freenode.net/?channels=pyramid).

## Git Branches

Git branches and their purpose and status at the time of this writing are listed below.

*   [main](https://github.com/Pylons/pyramid_openapi3/) - The branch which should always be *deployable*. The default branch on GitHub.
*   For development, create a new branch. If changes on your new branch are accepted, they will be merged into the main branch and deployed.

## Running tests

You need [uv](https://docs.astral.sh/uv/) installed on your machine. uv manages the
supported Python versions (3.11 and 3.14) and all project dependencies for you, so the
unit tests run without Nix:

```shell
make unit    # run the test suite
```

Everything else (`make lint`, `make types`) needs [prek](https://prek.j178.dev/) and the
linters, which are deliberately kept out of `uv.lock` so that it pins only project
dependencies. The easiest way to get all the tools is [nix](https://nix.dev/tutorials/declarative-and-reproducible-developer-environments):
run `nix-shell` to drop into a shell that has uv and every linter prepared, then run the
whole pipeline:

```shell
make tests
```

If you don't use Nix, install the tools yourself:

```shell
uv tool install prek            # pre-commit hook runner
uv tool install ruff            # Python linter and formatter
uv tool install ty              # Python type checker
uv tool install codespell       # spell checker
uv tool install detect-secrets  # secret scanner
uv tool install tombi           # TOML formatter
uv tool install zizmor          # GitHub Actions auditor
brew install actionlint         # GitHub Actions linter
brew install shellcheck         # shell script linter
brew install yamlfmt            # YAML formatter
```

(`brew` works on both macOS and Linux; your distro's package manager has these too.)

The remaining hooks (`nixfmt-rfc-style`, `deadnix`, `statix`) only check Nix files, so
without Nix installed just skip them:

```shell
SKIP=nixfmt-rfc-style,deadnix,statix make tests
```

## Testing oldest supported versions

In CI, we want to test the oldest supported versions of `openapi-core` and `pyramid` on the oldest supported Python version. We do it like so:

* The oldest supported direct dependencies are pinned in `uv-oldest.lock`
  (a lowest-direct resolution), committed alongside the regular `uv.lock`.
  Run `make lock` to regenerate both whenever dependencies change. The lower
  bounds on the dev dependencies in `pyproject.toml` keep that resolution on
  working tool versions.
* The dedicated "Python 3.11 Tests" CI job installs `uv-oldest.lock` and runs
  the suite against it.
