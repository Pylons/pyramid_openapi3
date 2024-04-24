# pyramid_openapi3

## Validate [Pyramid](https://trypyramid.com) views against [OpenAPI 3.0/3.1](https://swagger.io/specification/) documents

<p align="center">
  <img alt="Pyramid and OpenAPI logos"
       height="200"
       src="https://github.com/Pylons/pyramid_openapi3/blob/main/header.jpg?raw=true">
</p>

<p align="center">
  <a href="https://github.com/Pylons/pyramid_openapi3/actions/workflows/ci.yml">
    <img alt="CI for pyramid_openapi3 (main branch)"
         src="https://github.com/Pylons/pyramid_openapi3/actions/workflows/ci.yml/badge.svg">
  </a>
  <img alt="Test coverage (main branch)"
       src="https://img.shields.io/badge/tests_coverage-100%25-brightgreen.svg">
  <img alt="Test coverage (main branch)"
       src="https://img.shields.io/badge/types_coverage-100%25-brightgreen.svg">
  <a href="https://pypi.org/project/pyramid_openapi3/">
    <img alt="latest version of pyramid_openapi3 on PyPI"
         src="https://img.shields.io/pypi/v/pyramid_openapi3.svg">
  </a>
  <a href="https://pypi.org/project/pyramid_openapi3/">
    <img alt="Supported Python versions"
         src="https://img.shields.io/pypi/pyversions/pyramid_openapi3.svg">
  </a>
  <a href="https://github.com/Pylons/pyramid_openapi3/blob/main/LICENSE">
    <img alt="License: MIT"
         src="https://img.shields.io/badge/License-MIT-yellow.svg">
  </a>
  <a href="https://github.com/Pylons/pyramid_openapi3/graphs/contributors">
    <img alt="Built by these great folks!"
         src="https://img.shields.io/github/contributors/Pylons/pyramid_openapi3.svg">
  </a>
</p>

## Peace of Mind

The reason this package exists is to give you peace of mind when providing a RESTful API. Instead of chasing down preventable bugs and saying sorry to consumers, you can focus on more important things in life.

- Your **API documentation is never out-of-date**, since it is generated out of the API document that you write.
- The documentation comes with **_try-it-out_ examples** for every endpoint in your API. You don't have to provide (and maintain) `curl` commands to showcase how your API works. Users can try it themselves, right in their browsers.
- Your **API document is always valid**, since your Pyramid app won't even start if the document does not comply with the OpenAPI 3.0 specification.
- Automatic request **payload validation and sanitization**. Your views do not require any code for validation and input sanitation. Your view code only deals with business logic. Tons of tests never need to be written since every request, and its payload, is validated against your API document before it reaches your view code.
- Your API **responses always match your API document**. Every response from your view is validated against your document and a `500 Internal Server Error` is returned if the response does not exactly match what your document says the output of a certain API endpoint should be. This decreases the effects of [Hyrum's Law](https://www.hyrumslaw.com).
- **A single source of truth**. Because of the checks outlined above, you can be sure that whatever your API document says is in fact what is going on in reality. You have a single source of truth to consult when asking an API related question, such as "Remind me again, which fields are returned by the endpoint `/user/info`?".
- Based on [Pyramid](https://trypyramid.com), a **mature Python Web framework**. Companies such as Mozilla, Yelp, RollBar and SurveyMonkey [trust Pyramid](https://trypyramid.com/community-powered-by-pyramid.html), and the new [pypi.org](https://github.com/pypa/warehouse) runs on Pyramid, too. Pyramid is thoroughly [tested](https://github.com/Pylons/Pyramid/actions?query=workflow%3A%22Build+and+test%22) and [documented](https://docs.pylonsproject.org/projects/pyramid/en/latest/), providing flexibility, performance, and a large ecosystem of [high-quality add-ons](https://trypyramid.com/extending-pyramid.html).

<p align="center">
<a href="https://www.youtube.com/watch?v=P0zNxrDO0sE&amp;t=1061" title="Building Robust APIs" rel="nofollow" class="rich-diff-level-one"><img src="https://user-images.githubusercontent.com/311580/97364772-6d246a80-189c-11eb-84f2-a0ad23236003.png" alt="Building Robust APIs" style="max-width:100%;"></a>
</p>

## Features

- Validates your API document (for example, `openapi.yaml` or `openapi.json`) against the OpenAPI 3.0 specification using the [openapi-spec-validator](https://github.com/p1c2u/openapi-spec-validator).
- Generates and serves the [Swagger try-it-out documentation](https://swagger.io/tools/swagger-ui/) for your API.
- Validates incoming requests _and_ outgoing responses against your API document using [openapi-core](https://github.com/p1c2u/openapi-core).

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

## Advanced configuration

### Relative File References in Spec

A feature introduced in OpenAPI3 is the ability to use `$ref` links to external files (<https://github.com/OAI/OpenAPI-Specification/blob/main/versions/3.1.0.md#reference-object>).

To use this, you must ensure that you have all of your spec files in a given directory (ensure that you do not have any code in this directory as all the files in it are exposed as static files), then **replace** the `pyramid_openapi3_spec` call that you did in [Getting Started](#getting-started) with the following:

```python
config.pyramid_openapi3_spec_directory('path/to/openapi.yaml', route='/api/v1/spec')
```

Some notes:

- Do not set the `route` of your `pyramid_openapi3_spec_directory` to the same value as the `route` of `pyramid_openapi3_add_explorer`.
- The `route` that you set for `pyramid_openapi3_spec_directory` should not contain any file extensions, as this becomes the root for all of the files in your specified `filepath`.
- You cannot use `pyramid_openapi3_spec_directory` and `pyramid_openapi3_spec` in the same app.

### Endpoints / Request / Response Validation

Provided with `pyramid_openapi3` are a few validation features:

- incoming request validation (i.e., what a client sends to your app)
- outgoing response validation (i.e., what your app sends to a client)
- endpoint validation (i.e., your app registers routes for all defined API endpoints)

These features are enabled as a default, but you can disable them if you need to:

```python
config.registry.settings["pyramid_openapi3.enable_endpoint_validation"] = False
config.registry.settings["pyramid_openapi3.enable_request_validation"] = False
config.registry.settings["pyramid_openapi3.enable_response_validation"] = False
```

> [!WARNING]
> Disabling request validation will result in `request.openapi_validated` no longer being available to use.

### Register Pyramid's Routes

You can register routes in your pyramid application.
First, write the `x-pyramid-route-name` extension in the PathItem of the OpenAPI schema.

```yaml
paths:
  /foo:
    x-pyramid-route-name: foo_route
    get:
      responses:
        200:
          description: GET foo
```

Then put the config directive `pyramid_openapi3_register_routes` in the app_factory of your application.

```python
config.pyramid_openapi3_register_routes()
```

This is equal to manually writing the following:

```python
config.add_route("foo_route", pattern="/foo")
```

The `pyramid_openapi3_register_routes()` method supports setting a factory and route prefix as well. See the source for details.

### Specify protocol and port for getting the OpenAPI 3 spec file

Sometimes, it is necessary to specify the protocol and port to access the openapi3 spec file. This can be configured using the `proto_port` optional parameter to the the `pyramid_openapi3_add_explorer` function:

```python
config.pyramid_openapi3_add_explorer(proto_port=('https', 443))
```

## Demo / Examples

There are three examples provided with this package:

- A fairly simple [single-file app providing a Hello World API](https://github.com/Pylons/pyramid_openapi3/tree/main/examples/singlefile).
- A slightly more [built-out app providing a TODO app API](https://github.com/Pylons/pyramid_openapi3/tree/main/examples/todoapp).
- Another TODO app API, defined using a [YAML spec split into multiple files](https://github.com/Pylons/pyramid_openapi3/tree/main/examples/splitfile).

All examples come with tests that exhibit pyramid_openapi's error handling and validation capabilities.

A **fully built-out app**, with 100% test coverage, providing a [RealWorld.io](https://realworld.io) API is available at [niteoweb/pyramid-realworld-example-app](https://github.com/niteoweb/pyramid-realworld-example-app). It is a Heroku-deployable Pyramid app that provides an API for a Medium.com-like social app. You are encouraged to use it as a scaffold for your next project.

## Design defense

The authors of pyramid_openapi3 believe that the approach of validating a manually-written API document is superior to the approach of generating the API document from Python code. Here are the reasons:

1. Both generation and validation against a document are lossy processes. The underlying libraries running the generation/validation will always have something missing. Either a feature from the latest OpenAPI specification, or an implementation bug. Having to fork the underlying library in order to generate the part of your API document that might only be needed for the frontend is unfortunate.

    Validation on the other hand allows one to skip parts of validation that are not supported yet, and not block a team from shipping the document.

2. The validation approach does sacrifice DRY-ness, and one has to write the API document and then the (view) code in Pyramid. It feels a bit redundant at first. However, this provides a clear separation between the intent and the implementation.

3. The generation approach has the drawback of having to write Python code even for parts of the API document that the Pyramid backend does not handle, as it might be handled by a different system, or be specific only to documentation or only to the client side of the API. This bloats your Pyramid codebase with code that does not belong there.

## Running tests

You need to have [poetry](https://python-poetry.org/) and Python 3.10 & 3.12 installed on your machine. All `Makefile` commands assume you have the Poetry environment activated, i.e. `poetry shell`.

Alternatively, if you use [nix](https://nix.dev/tutorials/declarative-and-reproducible-developer-environments), run `nix-shell` to drop into a shell that has everything prepared for development.

Then you can run:

```shell
make tests
```

## Related packages

These packages tackle the same problem-space:

- [pyramid_oas3](https://github.com/kazuki/pyramid-oas3) seems to do things very similarly to pyramid_openapi3, but the documentation is not in English and we sadly can't fully understand what it does by just reading the code.
- [pyramid_swagger](https://github.com/striglia/pyramid_swagger) does a similar
  thing, but for Swagger 2.0 documents.
- [connexion](https://github.com/zalando/connexion) takes the same "write spec first, code second" approach as pyramid_openapi3, but is based on Flask.
- [bottle-swagger](https://github.com/ampedandwired/bottle-swagger) takes the same "write spec first, code second" approach too, but is based on Bottle.
- [pyramid_apispec](https://github.com/ergo/pyramid_apispec) uses generation with
  help of apispec and the marshmallow validation library. See above [why we prefer validation instead of generation](#design-defense).

## Deprecation policy

We do our best to follow the rules below.

- Support the latest few releases of Python, currently Python 3.10 through 3.12.
- Support the latest few releases of Pyramid, currently 1.10.7 through 2.0.2.
- Support the latest few releases of `openapi-core`, currently just 0.19.0.
- See `poetry.lock` for a frozen-in-time known-good-set of all dependencies.

## Use in the wild

A couple of projects that use pyramid_openapi3 in production:

- [Pareto Security Team Dashboard API](https://dash.paretosecurity.com/api/v1) - Team Dashboard for Pareto Security macOS security app.
- [SEO Domain Finder API](https://app.seodomainfinder.com/api/v1) - A tool for finding expired domains with SEO value.
- [Rankalyzer.io](https://app.rankalyzer.io/api/v1) - Monitor SEO changes and strategies of competitors to improve your search traffic.
- [Kafkai API](https://app.kafkai.com/api/v1) - User control panel for Kafkai text generation service.
- [Open on-chain data API](https://tradingstrategy.ai/api/explorer/) - Decentralised exchange and blockchain trading data open API.
- [Mayet RX](https://app.mayetrx.com/api/v1) - Vendor management system for pharma/medical clinical trials.
