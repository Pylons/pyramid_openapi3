# Convenience makefile to build the dev env and run common commands
# Based on https://github.com/niteoweb/Makefile
.EXPORT_ALL_VARIABLES:
PIPENV_VENV_IN_PROJECT = 1
PIPENV_IGNORE_VIRTUALENVS=1

.PHONY: all
all: .installed

.PHONY: install
install:
	@rm -f .installed  # force re-install
	@make .installed

.installed: Pipfile Pipfile.lock
	@echo "Pipfile(.lock) is newer than .installed, (re)installing"
	@pipenv install --dev
	@pipenv run pre-commit install -f --hook-type pre-commit
	@pipenv run pre-commit install -f --hook-type pre-push
	@echo "This file is used by 'make' for keeping track of last install time. If Pipfile or Pipfile.lock are newer then this file (.installed) then all 'make *' commands that depend on '.installed' know they need to run pipenv install first." \
		> .installed

# Testing and linting targets
.PHONY: lint
lint: .installed
	@pipenv run pre-commit run --all-files --hook-stage push

.PHONY: type
type: types

.PHONY: types
types: .installed
	@pipenv run mypy pyramid_openapi3

.PHONY: sort
sort: .installed
	@pipenv run isort -rc --atomic pyramid_openapi3
	@pipenv run isort -rc --atomic setup.py

.PHONY: fmt
fmt: format

.PHONY: black
black: format

.PHONY: format
format: .installed sort
	@pipenv run black pyramid_openapi3
	@pipenv run black setup.py

# anything, in regex-speak
filter = "."
# additional arguments for pytest
args = ""
pytest_args = -k $(filter) $(args)
COVERAGE_THRESHOLD = 34
coverage_args = --cov=pyramid_openapi3 --cov-branch --cov-report html --cov-report xml:cov.xml --cov-report term-missing --cov-fail-under=$(COVERAGE_THRESHOLD)

.PHONY: unit
unit: .installed
	@pipenv run pytest pyramid_openapi3/ $(coverage_args) $(pytest_args)

.PHONY: test
test: tests

.PHONY: tests
tests: format lint types unit

.PHONY: clean
clean:
	@if [ -d ".venv/" ]; then pipenv --rm; fi
	@rm -rf .coverage htmlcov/ pyramid_openapi3.egg-info xunit.xml \
	    htmltypecov typecov \
	    .git/hooks/pre-commit .git/hooks/pre-push
	@rm -f .installed
