"""Test validation exceptions."""

from collections.abc import Iterator
from pyramid import testing
from pyramid.httpexceptions import HTTPBadRequest
from pyramid.httpexceptions import HTTPPreconditionFailed
from pyramid.request import Request
from pyramid.router import Router
from pyramid_openapi3.exceptions import ImproperAPISpecificationWarning
from pyramid_openapi3.tests.utils import DummyStartResponse
from pyramid_openapi3.tests.utils import get_view
from pyramid_openapi3.tests.utils import make_request

import json
import logging
import pytest
import typing as t


class RequestValidationBase:  # noqa: D101
    openapi_spec: bytes

    @pytest.fixture
    def spec(self, request: pytest.FixtureRequest) -> bytes:
        """Return the class's spec; subclasses can override to parametrize it."""
        return self.openapi_spec

    @pytest.fixture(autouse=True)
    def setup_config(
        self, spec: bytes, write_spec: t.Callable[..., str]
    ) -> Iterator[None]:
        """Set up a minimal pyramid configuration for each test."""
        with testing.testConfig() as config:
            self.config = config
            self.config.include("pyramid_openapi3")
            self.config.pyramid_openapi3_spec(
                write_spec(spec), route="/foo.yaml", route_name="foo_api_spec"
            )
            yield

    def _add_view(
        self, view_func: t.Callable | None = None, openapi: bool = True
    ) -> None:
        """Add a simple example view.

        :param view_func: an optional view callable.
        :param openapi: if True, enable openapi view deriver
        """
        self.config.add_route("foo", "/foo")
        if not view_func:
            view_func = lambda *arg: "foo"  # noqa: E731
        self.config.add_view(
            openapi=openapi, renderer="json", view=view_func, route_name="foo"
        )


class TestRequestValidation(RequestValidationBase):  # noqa: D101
    openapi_spec = (
        b"openapi: '3.1.0'\n"
        b"info:\n"
        b"  version: '1.0.0'\n"
        b"  title: Foo API\n"
        b"paths:\n"
        b"  /foo:\n"
        b"    get:\n"
        b"      parameters:\n"
        b"        - name: bar\n"
        b"          in: query\n"
        b"          required: true\n"
        b"          schema:\n"
        b"            type: integer\n"
        b"      responses:\n"
        b"        200:\n"
        b"          description: A foo\n"
        b"          content:\n"
        b"            application/json:\n"
        b"              schema:\n"
        b"                type: object\n"
        b"                properties:\n"
        b"                  test:\n"
        b"                    type: string\n"
        b"        400:\n"
        b"          description: Bad Request\n"
    )

    @pytest.fixture(params=["3.1.0", "3.2.0"])
    def spec(self, request: pytest.FixtureRequest) -> bytes:
        """Run every scenario against both OpenAPI 3.1 and 3.2."""
        spec = self.openapi_spec.replace(b"3.1.0", request.param.encode())
        assert f"openapi: '{request.param}'".encode() in spec
        return spec

    def test_view_raises_valid_http_exception(self) -> None:
        """Test View raises HTTPException.

        Example view raises a defined response code.
        """

        def view_func(*args: t.Any) -> Exception:
            raise HTTPBadRequest("bad foo request")

        self._add_view(view_func)
        view = get_view(self.config, "foo")
        request = make_request(
            self.config, "foo", params={"bar": "1"}, content_type="text/html"
        )
        with pytest.raises(HTTPBadRequest) as exc_info:
            view(None, request)
        response = exc_info.value
        # not enough of pyramid has been set up so we need to render the
        # exception response ourselves.
        response.prepare({"HTTP_ACCEPT": "application/json"})
        assert "bad foo request" in response.json["message"]

    def test_view_valid_request_response(self) -> None:
        """Test openapi validated view which has correct request and response."""
        self._add_view(lambda *arg: {"test": "correct"})
        # run request through router
        router = Router(self.config.registry)
        environ = {
            "wsgi.url_scheme": "http",
            "SERVER_NAME": "localhost",
            "SERVER_PORT": "8080",
            "REQUEST_METHOD": "GET",
            "PATH_INFO": "/foo",
            "HTTP_ACCEPT": "application/json",
            "QUERY_STRING": "bar=1",
        }
        start_response = DummyStartResponse()
        response = router(environ, start_response)
        assert start_response.status == "200 OK"
        assert json.loads(response[0]) == {"test": "correct"}

    def test_request_validation_error(self, caplog: pytest.LogCaptureFixture) -> None:
        """Request validation errors are rendered as 400 JSON responses."""
        self._add_view()
        # run request through router
        router = Router(self.config.registry)
        environ = {
            "wsgi.url_scheme": "http",
            "SERVER_NAME": "localhost",
            "SERVER_PORT": "8080",
            "REQUEST_METHOD": "GET",
            "PATH_INFO": "/foo",
            "HTTP_ACCEPT": "application/json",
        }
        start_response = DummyStartResponse()
        with caplog.at_level(logging.WARNING):
            response = router(environ, start_response)

        assert start_response.status == "400 Bad Request"
        assert json.loads(response[0]) == [
            {
                "exception": "MissingRequiredParameter",
                "message": "Missing required query parameter: bar",
                "field": "bar",
            }
        ]
        assert caplog.record_tuples == [
            (
                "pyramid_openapi3",
                logging.WARNING,
                "Missing required query parameter: bar",
            )
        ]

    def test_response_validation_error(self, caplog: pytest.LogCaptureFixture) -> None:
        """Test View raises ResponseValidationError.

        Example view raises an undefined response code.
        The response validation tween should catch this as response validation error,
        and return an error 500.
        """
        self._add_view(lambda *arg: HTTPPreconditionFailed())

        # run request through router
        router = Router(self.config.registry)
        environ = {
            "wsgi.url_scheme": "http",
            "SERVER_NAME": "localhost",
            "SERVER_PORT": "8080",
            "REQUEST_METHOD": "GET",
            "PATH_INFO": "/foo",
            "HTTP_ACCEPT": "application/json",
            "QUERY_STRING": "bar=1",
        }
        start_response = DummyStartResponse()
        with caplog.at_level(logging.ERROR):
            response = router(environ, start_response)
        assert start_response.status == "500 Internal Server Error"
        assert json.loads(response[0]) == [
            {
                "exception": "ResponseNotFound",
                "message": "Unknown response http status: 412",
            }
        ]
        assert caplog.record_tuples == [
            ("pyramid_openapi3", logging.ERROR, "Unknown response http status: 412")
        ]

    def test_nonapi_view(self) -> None:
        """Test View without openapi validation."""
        self._add_view(openapi=False)
        # run request through router
        router = Router(self.config.registry)
        environ = {
            "wsgi.url_scheme": "http",
            "SERVER_NAME": "localhost",
            "SERVER_PORT": "8080",
            "REQUEST_METHOD": "GET",
            "PATH_INFO": "/foo",
        }
        start_response = DummyStartResponse()
        response = router(environ, start_response)
        assert start_response.status == "200 OK"
        assert b"foo" in b"".join(response)

    def test_nonapi_view_raises_AttributeError(self) -> None:
        """Test non-openapi view that accesses request.openapi_validated."""

        def should_raise_error(request: Request) -> None:
            request.openapi_validated

        self._add_view(openapi=False, view_func=should_raise_error)
        # run request through router
        router = Router(self.config.registry)
        environ = {
            "wsgi.url_scheme": "http",
            "SERVER_NAME": "localhost",
            "SERVER_PORT": "8080",
            "REQUEST_METHOD": "GET",
            "PATH_INFO": "/foo",
        }
        start_response = DummyStartResponse()
        with pytest.raises(AttributeError) as exc_info:
            router(environ, start_response)

        assert (
            str(exc_info.value)
            == "Cannot do openapi request validation on a view marked with openapi=False"
        )

    def test_request_validation_disabled(self) -> None:
        """Test View with request validation disabled."""
        self._add_view(lambda *arg: {"test": "correct"})

        # by default validation is enabled
        router = Router(self.config.registry)
        environ = {
            "wsgi.url_scheme": "http",
            "SERVER_NAME": "localhost",
            "SERVER_PORT": "8080",
            "REQUEST_METHOD": "GET",
            "PATH_INFO": "/foo",
            "HTTP_ACCEPT": "application/json",
            "QUERY_STRING": "bad=parameter",
        }
        start_response = DummyStartResponse()
        response = router(environ, start_response)
        assert start_response.status == "400 Bad Request"

        # now let's disable it
        self.config.registry.settings["pyramid_openapi3.enable_request_validation"] = (
            False
        )
        start_response = DummyStartResponse()
        response = router(environ, start_response)
        assert start_response.status == "200 OK"
        assert json.loads(response[0]) == {"test": "correct"}

    def test_response_validation_disabled(self) -> None:
        """Test View with response validation disabled."""
        self._add_view(lambda *arg: "not-valid")

        # by default validation is enabled
        router = Router(self.config.registry)
        environ = {
            "wsgi.url_scheme": "http",
            "SERVER_NAME": "localhost",
            "SERVER_PORT": "8080",
            "REQUEST_METHOD": "GET",
            "PATH_INFO": "/foo",
            "HTTP_ACCEPT": "application/json",
            "QUERY_STRING": "bar=1",
        }
        start_response = DummyStartResponse()
        response = router(environ, start_response)
        assert start_response.status == "500 Internal Server Error"

        # now let's disable it
        self.config.registry.settings["pyramid_openapi3.enable_response_validation"] = (
            False
        )
        start_response = DummyStartResponse()
        response = router(environ, start_response)
        assert start_response.status == "200 OK"
        assert json.loads(response[0]) == "not-valid"

    def test_request_validation_disabled_response_validation_enabled(self) -> None:
        """Test response validation still works if request validation is disabled."""
        self._add_view(lambda *arg: "not-valid")

        self.config.registry.settings["pyramid_openapi3.enable_request_validation"] = (
            False
        )

        # by default validation is enabled
        router = Router(self.config.registry)
        environ = {
            "wsgi.url_scheme": "http",
            "SERVER_NAME": "localhost",
            "SERVER_PORT": "8080",
            "REQUEST_METHOD": "GET",
            "PATH_INFO": "/foo",
            "HTTP_ACCEPT": "application/json",
            "QUERY_STRING": "bar=1",
        }
        start_response = DummyStartResponse()
        router(environ, start_response)
        assert start_response.status == "500 Internal Server Error"


class TestServerRequestValidation(RequestValidationBase):  # noqa: D101
    openapi_spec = (
        b"openapi: '3.1.0'\n"
        b"info:\n"
        b"  version: '1.0.0'\n"
        b"  title: Foo API\n"
        b"servers:\n"
        b"  - url: /prefix/v1\n"
        b"  - url: http://example.com/prefix\n"
        b"paths:\n"
        b"  /foo:\n"
        b"    get:\n"
        b"      responses:\n"
        b"        200:\n"
        b"          description: A foo\n"
        b"          content:\n"
        b"            application/json:\n"
        b"              schema:\n"
        b"                type: object\n"
        b"                properties:\n"
        b"                  test:\n"
        b"                    type: string\n"
        b"        400:\n"
        b"          description: Bad Request\n"
    )

    def test_server_validation_works_with_script_name(self) -> None:
        """Expect to find a match for http://localhost:8080/prefix/v1/foo."""
        self._add_view(lambda *arg: {"test": "correct"})
        # run request through router
        router = Router(self.config.registry)
        environ = {
            "wsgi.url_scheme": "http",
            "SERVER_NAME": "localhost",
            "SERVER_PORT": "8080",
            "REQUEST_METHOD": "GET",
            "SCRIPT_NAME": "/prefix/v1",
            "PATH_INFO": "/foo",
            "HTTP_ACCEPT": "application/json",
        }
        start_response = DummyStartResponse()
        response = router(environ, start_response)

        assert start_response.status == "200 OK"
        assert json.loads(response[0]) == {"test": "correct"}

    def test_server_validation_works_with_script_name_and_hostname(self) -> None:
        """Expect to find a match for http://example.com/prefix/foo."""
        self._add_view(lambda *arg: {"test": "correct"})
        # run request through router
        router = Router(self.config.registry)
        environ = {
            "wsgi.url_scheme": "http",
            "SERVER_NAME": "localhost",
            "SERVER_PORT": "8080",
            "REQUEST_METHOD": "GET",
            "SCRIPT_NAME": "/prefix",
            "PATH_INFO": "/foo",
            "HTTP_HOST": "example.com",
            "HTTP_ACCEPT": "application/json",
        }
        start_response = DummyStartResponse()
        response = router(environ, start_response)

        assert start_response.status == "200 OK"
        assert json.loads(response[0]) == {"test": "correct"}

    def test_server_validation_fails_with_bad_hostname(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Expect to fail for /prefix/v2/foo."""
        self._add_view()
        # run request through router
        router = Router(self.config.registry)
        environ = {
            "wsgi.url_scheme": "http",
            "SERVER_NAME": "localhost",
            "SERVER_PORT": "8080",
            "REQUEST_METHOD": "GET",
            "SCRIPT_NAME": "/prefix/v2",
            "PATH_INFO": "/foo",
            "HTTP_HOST": "example.com",
            "HTTP_ACCEPT": "application/json",
        }
        start_response = DummyStartResponse()
        with (
            caplog.at_level(logging.ERROR),
            pytest.warns(ImproperAPISpecificationWarning) as record,
        ):
            response = router(environ, start_response)
        # pytest.warns records every warning in its block, ignored ones included.
        assert [
            str(w.message)
            for w in record
            if issubclass(w.category, ImproperAPISpecificationWarning)
        ] == [
            (
                "Discarding 400 Bad Request validation error with body "
                '[{"exception":"ServerNotFound",'
                '"message":"Server not found for http://example.com/prefix/v2/foo"}] '
                "as it is not a valid response for GET to /prefix/v2/foo (foo)"
            )
        ]
        assert start_response.status == "500 Internal Server Error"
        assert json.loads(response[0]) == [
            {
                "exception": "ServerNotFound",
                "message": "Server not found for http://example.com/prefix/v2/foo",
            }
        ]
        assert caplog.record_tuples == [
            (
                "pyramid_openapi3",
                logging.ERROR,
                "Server not found for http://example.com/prefix/v2/foo",
            )
        ]


class TestImproperAPISpecValidation(RequestValidationBase):  # noqa: D101
    openapi_spec = (
        b'openapi: "3.1.0"\n'
        b"info:\n"
        b'  version: "1.0.0"\n'
        b"  title: Foo API\n"
        b"paths:\n"
        b"  /foo:\n"
        b"    get:\n"
        b"      parameters:\n"
        b"        - name: bar\n"
        b"          in: query\n"
        b"          required: true\n"
        b"          schema:\n"
        b"            type: integer\n"
        b"      responses:\n"
        b"        200:\n"
        b"          description: A foo\n"
    )

    def test_request_validation_error_causes_response_validation_error(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Tests fallback for when request validation is disallowed by the spec.

        When a request fails validation an exception is raised which causes
        a 400 error to be raised to the end user specifying what the problem was.
        If the API spec disallows 400 errors, this will be transformed into a
        500 error with a response validation message about incorrect types.

        We should also raise a warning in this case, so developers are alerted to
        such problems.
        """
        self._add_view()
        # run request through router
        router = Router(self.config.registry)
        environ = {
            "wsgi.url_scheme": "http",
            "SERVER_PROTOCOL": "HTTP/1.1",
            "SERVER_NAME": "localhost",
            "SERVER_PORT": "8080",
            "REQUEST_METHOD": "GET",
            "PATH_INFO": "/foo",
            "HTTP_ACCEPT": "application/json",
            "QUERY_STRING": "unknown=1",
        }
        start_response = DummyStartResponse()
        with (
            caplog.at_level(logging.ERROR),
            pytest.warns(ImproperAPISpecificationWarning) as record,
        ):
            response = router(environ, start_response)
        # pytest.warns records every warning in its block, ignored ones included.
        assert [
            str(w.message)
            for w in record
            if issubclass(w.category, ImproperAPISpecificationWarning)
        ] == [
            (
                "Discarding 400 Bad Request validation error with body "
                '[{"exception":"MissingRequiredParameter",'
                '"message":"Missing required query parameter: bar","field":"bar"}] '
                "as it is not a valid response for GET to /foo (foo)"
            )
        ]
        assert caplog.record_tuples == [
            ("pyramid_openapi3", logging.ERROR, "Unknown response http status: 400")
        ]

        assert start_response.status == "500 Internal Server Error"
        assert json.loads(response[0]) == [
            {
                "exception": "ResponseNotFound",
                "message": "Unknown response http status: 400",
            }
        ]
