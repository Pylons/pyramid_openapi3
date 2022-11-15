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

*   [master](https://github.com/Pylons/pyramid_openapi3/) - The branch which should always be *deployable*. The default branch on GitHub.
*   For development, create a new branch. If changes on your new branch are accepted, they will be merged into the master branch and deployed.

## Prerequisites

Follow the instructions in [README.rst](https://github.com/Pylons/pyramid_openapi3/) to install the tools needed to run the project.

## Testing oldest supported versions

In CI, we want to test the oldest supported versions of `openapi-core` and `pyramid` on the oldest supported Python version. We do it like so:

* Have the `pyproject_py37.toml` and `poetry_py37.lock` files in this repo.
* In the Python 3.7 CI run, `mv` them to `pyproject.toml` and `poetry.lock`.

### How to prepare these two files

1.  In `pyproject.toml` modify the `openapi-core` and `pyramid` dependencies to be pinned to the
    oldest supported version.

    ```diff
    - openapi-core = ">=0.13.4,<0.14"
    - pyramid = ">=1.10.7"
    + openapi-core = "==0.13.4"
    + pyramid = "==1.10.7"
    ```
1.  Re-generate the lockfile and put it into place to be picked up by CI.

    ```shell

    # update poetry.lock with new constraints
    $ nix-shell shell_py37.nix --run "poetry lock --no-update"

    # move changes into *_py37 files that will be picked up by CI
    $ mv pyproject.toml pyproject_py37.toml
    $ mv poetry.lock poetry_py37.lock
    $ git add pyproject_py37.toml poetry_py37.lock && git commit

    # cleanup
    $ git checkout pyproject.toml poetry.lock
    ```
