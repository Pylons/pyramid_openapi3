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

## Prerequisites

Follow the instructions in [README.rst](https://github.com/Pylons/pyramid_openapi3/) to install the tools needed to run the project.

## Testing oldest supported versions

In CI, we want to test the oldest supported versions of `openapi-core` and `pyramid` on the oldest supported Python version. We do it like so:

* Have the `py38` folder with additional `pyproject.toml` and `poetry.lock` files
  that are changed to pin `openapi-core` and `pyramid` to minimally supported version.
* They are auto-generated when running `make lock`.
* They are used by Nix to prepare the Python 3.8 env.
* `PYTHON=python3.8 make tests` then run tests with an older Python version.
