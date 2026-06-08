# Convenience makefile to build the dev env and run common commands
# Based on https://github.com/niteoweb/Makefile

# Python version uv should use for the environment
python ?= 3.14

# Pass `frozen=1` to run against the locked environment without re-resolving.
# Used by the CI jobs.
ifeq ($(frozen),1)
  uv_run := uv run --no-sync --python $(python)
  uv_sync := uv sync --frozen --python $(python)
else
  uv_run := uv run --python $(python)
  uv_sync := uv sync --python $(python)
endif

.PHONY: all
all: tests

# Regenerate both lockfiles: uv.lock (latest deps) and uv-oldest.lock
# (a lowest-direct resolution used by the oldest-supported-deps CI job).
# uv's lockfile indentation differs between versions; normalize both with tombi
# so the result matches the prek `tombi` hook and the locks stay reproducible
# regardless of which uv version generated them.
.PHONY: lock
lock:
	@uv lock --resolution lowest-direct
	@cp uv.lock uv-oldest.lock
	@uv lock
	@tombi format uv.lock uv-oldest.lock

# Sync the development environment. The ty hook and the test suite run against
# this .venv, so linting and testing targets depend on it.
.PHONY: install
install:
	@$(uv_sync)

# Run prek checks on changed files only:
# 1. get all unstaged modified files
# 2. get all staged modified files
# 3. get all untracked files
# 4. run prek checks on them
.PHONY: lint
lint: install
	@{ git diff --name-only ./; git diff --name-only --staged ./; git ls-files --other --exclude-standard; } \
		| sort -u | uniq | xargs prek run --files

# Run prek checks on all files in the repository.
.PHONY: lint-all
lint-all: install
	@prek run --all-files

.PHONY: type
type: types

.PHONY: types
types: install
	@ty check --error-on-warning pyramid_openapi3 examples


# anything, in regex-speak
filter = "."

# additional arguments for pytest
full_suite = "false"
ifeq ($(filter),".")
	full_suite = "true"
endif
ifdef path
	full_suite = "false"
endif
args = ""
pytest_args = -k $(filter) $(args)
ifeq ($(args),"")
	pytest_args = -k $(filter)
endif
verbosity = ""
ifeq ($(full_suite),"false")
	verbosity = -vv
endif
full_suite_args = ""
ifeq ($(full_suite),"true")
	full_suite_args = --junitxml junit.xml --durations 10 --cov=pyramid_openapi3 --cov-branch --cov-report html --cov-report xml:cov.xml --cov-report term-missing --cov-fail-under=100
endif


.PHONY: unit
unit:
ifndef path
	@$(uv_run) pytest pyramid_openapi3 $(verbosity) $(full_suite_args) $(pytest_args)
else
	@$(uv_run) pytest $(path)
endif

.PHONY: test
test: tests

.PHONY: tests
tests: lint-all types unit
