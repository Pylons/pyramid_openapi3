## Validate [Pyramid](https://trypyramid.com) views against an [OpenAPI 3.0](https://swagger.io/specification/) document

> **Warning: This project is currently in beta. Stable release planned in May 2019. If you're curious about the progress, ping `zupo` on [irc.freenode.net](https://webchat.freenode.net/?channels=niteo).**

<p align="center">
  <img height="200" src="https://github.com/niteoweb/pyramid_openapi3/blob/master/header.jpg?raw=true" />
</p>

<p align="center">
  <a href="https://circleci.com/gh/niteoweb/pyramid_openapi3">
    <img alt="CircleCI for pyramid_openapi3 (master branch)"
         src="https://circleci.com/gh/niteoweb/pyramid_openapi3.svg?style=shield">
  </a>
  <a href="https://github.com/niteoweb/pyramid_openapi3/blob/master/Makefile#L56">
    <img alt="Test coverage (master branch)"
         src="https://img.shields.io/badge/coverage-100%25-brightgreen.svg">
  </a>
  <a href="https://pypi.org/project/pyramid_openapi3/">
    <img alt="latest version of pyramid_openapi3 on PyPI"
         src="https://img.shields.io/pypi/v/pyramid_openapi3.svg">
  </a>
  <a href="https://pypi.org/project/pyramid_openapi3/">
    <img alt="Supported Python versions"
         src="https://img.shields.io/pypi/pyversions/pyramid_openapi3.svg">
  </a>
  <a href="https://github.com/niteoweb/pyramid_openapi3/blob/master/LICENSE">
    <img alt="License: MIT"
         src="https://img.shields.io/badge/License-MIT-yellow.svg">
  </a>
  <a href="https://github.com/niteoweb/pyramid_openapi3/graphs/contributors">
    <img alt="Built by these great folks!"
         src="https://img.shields.io/github/contributors/niteoweb/pyramid_openapi3.svg">
  </a>
  <a href="https://webchat.freenode.net/?channels=pyramid">
    <img alt="Talk to us in #pyramid on Freenode IRC"
         src="https://img.shields.io/badge/irc-freenode-blue.svg">
  </a>
</p>

## Peace of Mind

The reason this package exists is to give you peace of mind when providing a RESTful API with your Pyramid app. Instead of chasing down preventable bugs and saying sorry to consumers, you can focus on more important things in life.

- Your **API documentation is never out-of-date**, since it is generated out of the API document that you write.
- The documentation comes with **_try-it-out_ examples** for every endpoint in your API. You don't have to provide (and maintain) `curl` commands to showcase how your API works. Users can try it themselves, right in their browsers.
- Your **API document is always valid**, since your Pyramid app won't even start if the document is not according to OpenAPI 3.0 specification.
- Automatic request **payload validation and sanitization**. Your views do not require any code for validation and input sanitation. Your view code only deals with business logic. Tons of tests never need to be written since every request, and its payload, is validated against your API document before it reaches your view code.
- Your API **responses always match your API document**. Every response from your view is validated against your document and a `500 Internal Server Error` is returned if the response does not exactly match what your document says the output of a certain API endpoint should be.
- **A single source of truth**. Because of the checks outlined above you can be sure that whatever your API document says is in fact what is going on in reality. You have a single source of truth to consult when asking an API related question, such as "Remind me again, which fields does the endpoint /user/info return?".

## Features

- Validates your API document (for example, `openapi.yaml` or `openapi.json`) against the OpenAPI 3.0 specification using the [openapi-spec-validator](https://github.com/p1c2u/openapi-spec-validator).
- Generates and serves the [Swagger try-it-out documentation](https://swagger.io/tools/swagger-ui/) for your API.
- Validates incoming requests *and* outgoing responses against your API document using [openapi-core](https://github.com/p1c2u/openapi-core).


## Getting started

1. Declare `pyramid_openapi3` as a dependency in your Pyramid project.

2. Include the following lines:

```python
config.include("pyramid_openapi3")
config.pyramid_openapi3_spec('openapi.yaml', route='/api/v1/openapi.yaml')
config.pyramid_openapi3_add_explorer(route='/api/v1/')
```

3. Use the `openapi` [view predicate](https://docs.pylonsproject.org/projects/pyramid/en/latest/narr/viewconfig.html#view-configuration-parameters) to enable request/response validation:

```python
@view_config(route_name="foobar", openapi=True, renderer='json')
def myview(request):
    return request.openapi_validated.parameters
```

For requests, `request.openapi_validated` is available with two fields: `parameters` and `body`.
For responses, if the payload does not match the API document, an exception is raised.

## Demo

    $ pip install -e .[dev]
    $ python demo.py

There's also a self-contained [TODO app example](https://github.com/zupo/minimal_openapi).

## Design defense

The authors of pyramid_openapi3 believe that the approach of validating a manually-written API document is superior to the approach of generating the API document from Python code. Here are the reasons:

a) Both generation and validation against a document are lossy processes. The underlying libraries running the generation/validation will always have something missing. Either a feature from the latest OpenAPI specification, or an implementation bug. Having to fork the underlying library in order to generate the part of your API document that might only be needed for the frontend is unfortunate.

   Validation on the other hand allows one to skip parts of validation that are not supported yet, and not block a team from shipping the document.

b) Validation approach does sacrifice DRY-ness, one has to write the API document and then the (view) code in Pyramid. Feels a bit redundant at first. However, this provides a clear separation between the intent and the implementation.

c) Generation approach has the drawback of having to write Python code even for parts of the API document that the Pyramid backend does not handle, as it might be handled by a different system, or be specific only to documentation or only to the client side of the API. This bloats your Pyramid codebase with code that does not belong there.

## Running tests

You need to have [pipenv](https://pipenv.readthedocs.io/) and Python 3.7 installed on your machine. Then you can run:

    $ make tests

## Related packages

These packages tackle the same problem-space:

- [pyramid_swagger](https://github.com/striglia/pyramid_swagger) does a similar
  thing, but for Swagger 2.0 documents
- [pyramid_apispec](https://github.com/ergo/pyramid_apispec) uses generation with
  help of apispec and marshmallow validation library. See above [why we prefer validation instead of generation](#why---design-defense).

## Use in the wild

A couple of projects that use pyramid_openapi3 in production:

- [WooCart API](https://app.woocart.com/api/v1/) - Users' control panel for WooCart Managed WooCommerce service.

## TODO

- [x] Makefile.
- [x] Flake8.
- [x] Black.
- [x] mypy.
- [x] codespell.
- [x] pre-commit.
- [x] Testing framework.
- [x] CircleCI integration.
- [x] Beta PyPI release.
- [x] Go through all docstrings.
- [x] Automatic PyPI releases for tags, via CircleCI.
- [x] 100% test coverage.
- [x] How to contribute.
- [x] Add Changelog.
- [x] How to release (`vim setup.py && git add setup.py && git ci -m "release 0.2.0" && git tag 0.2.0 && git push --tags`
- [ ] Document that `pyramid_openapi3_validation_error_view()` is [registered without permissions](https://github.com/niteoweb/pyramid_openapi3/pull/6#discussion_r272651906).
- [ ] Move demo.py into examples/singlefile/
- [ ] Move https://github.com/zupo/minimal_openapi into examples/minimal/
- [ ] Move this repo to https://github.com/Pylons organization.
- [ ] Documentation how to validate Enums, Dataclases, PyDantic models against schema.
- [ ] Create a http://todobackend.com/ example.
- [ ] Create a https://realworld.io/ example.
- [ ] Add to https://trypyramid.com/extending-pyramid.html.
- [x] Add to https://github.com/p1c2u/openapi-core.
- [ ] Add to https://github.com/p1c2u/openapi-spec-validator.
- [ ] Add to https://github.com/uralbash/awesome-pyramid.
- [ ] Add to https://github.com/vinta/awesome-python.
- [ ] Announcement blog post.
