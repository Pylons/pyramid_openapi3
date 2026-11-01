"""Test path-level parameters."""

from pyramid.config import Configurator
from pyramid.request import Request
from webtest.app import TestApp

import typing as t


def _foo_view(request: Request) -> int:
    return request.openapi_validated.parameters.path["foo_id"]


def test_path_parameter_validation(write_spec: t.Callable[..., str]) -> None:
    """Test validated parameters in context factory."""
    spec = write_spec(b"""\
openapi: "3.1.0"
info:
  version: "1.0.0"
  title: Foo API
paths:
  /foo/{foo_id}:
    parameters:
      - name: foo_id
        in: path
        required: true
        schema:
          type: integer
    get:
      responses:
        200:
          description: A foo
""")

    with Configurator() as config:
        config.include("pyramid_openapi3")
        config.pyramid_openapi3_spec(spec)
        config.pyramid_openapi3_register_routes()
        config.add_route("foo_route", "/foo/{foo_id}")
        config.add_view(
            _foo_view, route_name="foo_route", renderer="json", openapi=True
        )
        app = config.make_wsgi_app()
        test_app = TestApp(app)
        resp = test_app.get("/foo/1")
        assert resp.json == 1
