# pyramid_openapi3

[![Build Status](https://travis-ci.com/niteoweb/pyramid_openapi3.svg?branch=master)](https://travis-ci.com/niteoweb/pyramid_openapi3)
[![PyPi](https://img.shields.io/pypi/v/pyramid_openapi3.svg)](https://pypi.org/project/pyramid_openapi3/)

Validate [OpenAPI 3.0](https://swagger.io/specification/) specification against
[pyramid framework](trypyramid.com) configuration and views.

## Features

- Validates OpenAPI3 file against openapi 3.0 specification using [openapi-spec-validator](https://github.com/p1c2u/openapi-spec-validator)
- Serves [Swagger UI](https://swagger.io/tools/swagger-ui/)
- Validates request and response using [openapi-core](https://github.com/p1c2u/openapi-core)

## Getting started

1. Put `pyramid_openapi3` as a dependency in your pyramid project.

2. Include the following lines:

```python        
config.include("pyramid_openapi3")
config.pyramid_openapi3_spec('demo.yaml', route='/api/v1/openapi.yaml')
config.pyramid_openapi3_add_explorer(route='/api/v1/')
```

3. In order to enable request/response validation:

```python
@view_config(route_name="foobar", requires_openapi=True, renderer='json')
def myview(request):
    return request.openapi_validated.parameters
```

For requests, `request.openapi_validated` is available with two fields: `parameters` and `body`.
For responses, if api specification is not valid, an exception will be raised.

## Demo

    $ pip install -e .[dev]
    $ python demo.py

## Why? - Design defense

pyramid_openapi3 uses validation of the spec instead of generation:

a) Generating or validating against a spec is a lossy process, there will always
   be something missing. Having to write code for a library in order to generate
   the specification that might be just needed for the frontend is unfortunate.
   Validation on the other hand allows one to skip validation if it's not written,
   but it's not blocking a team from shipping the spec.

b) Validation approach does sacrifice DRY-ness, one has to write the spec and then the
   api in pyramid. This does have some good effects like when reviewing code the intent
   and result are both present.

c) If it chose generation, there's a drawback how to support knobs for features that pyramid
   doesn't have or are specific only to documentation or client side of the api. Feels like
   something that doesn't belong to the backend.

## Running tests

    $ tox

## Related projects

- [pyramid_swagger](https://github.com/striglia/pyramid_swagger) does a similar
  thing, but for Swagger 2.0 specification
- [pyramid_apispec](https://github.com/ergo/pyramid_apispec) uses generation with
  help of apispec and marshmallow validation library
