# An example RESTful API app showcasing how to split YAML spec into multiple files

This folder showcases how to use the [pyramid_openapi3](https://github.com/Pylons/pyramid_openapi3) Pyramid add-on for building robust RESTful APIs defined with a multi-file YAML schema.

## How to run

```bash
$ git clone https://github.com/Pylons/pyramid_openapi3.git
$ cd pyramid_openapi3/examples/splitfile
$ virtualenv -p python3.9 .
$ source bin/activate
$ pip install pyramid_openapi3
$ python app.py
```

Then use the Swagger interface at http://localhost:6543/docs/ to discover the API. Use the `Try it out` button to run through a few request/response scenarios.

For example:
* Get all TODO items using the GET request.
* Adding a new TODO item using the POST request.
* Getting a 400 BadRequest response for an empty POST request
* Getting a 400 BadRequest response for a POST request when `title` is too long (over 40 characters).

All of these examples are covered with tests that you can run with `$ python -m unittest tests.py`. The tests need the Python webtest module installed. If your virtualenv is still activated you can install it with `pip install webtest`.


## Further read

* A slightly simpler, multi-file (single spec file) example is available in the [`examples/todoapp`](https://github.com/Pylons/pyramid_openapi3/tree/master/examples/todoapp) folder.

* A simpler, single-file (spec in app) example is available in the [`examples/singlefile`](https://github.com/Pylons/pyramid_openapi3/tree/master/examples/singlefile) folder.

* A fully built-out app, with 100% test coverage, providing a [RealWorld.io](https://realworld.io) API is available at [niteoweb/pyramid-realworld-example-app](https://github.com/niteoweb/pyramid-realworld-example-app). It is a Heroku-deployable Pyramid app that provides an API for a Medium.com-like social app. You are encouraged to use it as a scaffold for your next project.

* More information about the library providing the integration between OpenAPI specs and Pyramid, more advanced features and design defence, is available in the main [README](https://github.com/Pylons/pyramid_openapi3) file.

* More validators for fields are listed in the [OpenAPI Specification](https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.0.0.md#properties) document. You can use Regex as well.

* For an idea of a fully-fledged production OpenApi specification, check out [WooCart's OpenAPI docs](https://app.woocart.com/api/v1/).
