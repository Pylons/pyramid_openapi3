# An single-file example RESTful API app showcasing the power of pyramid_openapi3

The `app.py` file in this folder showcases how to use the [pyramid_openapi3](https://github.com/Pylons/pyramid_openapi3) Pyramid add-on for building robust RESTful APIs. With only a few lines of code you get automatic validation of requests and responses against an OpenAPI v3 schema, along with Swagger "try-it-out" documentation for your API.

## How to run

```bash
* mkdir my-openapi
* cd my-openapi
* wget https://raw.githubusercontent.com/Pylons/pyramid_openapi3/master/examples/singlefile/app.py
* pip install pyramid_openapi3
* python app.py
```

Then use the Swagger interface at http://localhost:6543/docs/ to discover the API. Use the `Try it out` button to run through a few request/response scenarios.

For example:
* Say Hello by doing a GET request to `http://localhost:6543/hello?name=john`.
* Get an Exception raised if you omit the required `name` query parameter.
* Get an Exception raised if the query parameter `name` is too short.

All of these examples are covered with tests that you can run with `$ python -m unittest app.py`.


## Further read

* A slightly more complex, multi-file example is available in the [`examples/todoapp`](https://github.com/Pylons/pyramid_openapi3/tree/master/examples/todoapp) folder.

* More information about the library providing the integration between OpenAPI specs and Pyramid, more advanced features and design defence, is available in the main [README](https://github.com/Pylons/pyramid_openapi3) file.

* More validators for fields are listed in the [OpenAPI Specification](https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.0.0.md#properties) document. You can use Regex as well.

* For an idea of a fully-fledged production OpenApi specification, check out [WooCart's OpenAPI docs](https://app.woocart.com/api/v1/).
