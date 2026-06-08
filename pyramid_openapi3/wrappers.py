"""Wrap Pyramid's Request and Response."""

from openapi_core.validation.request.datatypes import RequestParameters
from pyramid.request import Request
from pyramid.response import Response

import typing as t


class PyramidOpenAPIRequest:
    """Map Pyramid Request attributes to what openapi expects."""

    def __init__(self, request: Request) -> None:
        self.request = request

        self.parameters = RequestParameters(
            path=self.request.matchdict,  # ty: ignore[invalid-argument-type]
            query=self.request.GET,
            header=self.request.headers,
            cookie=self.request.cookies,
        )

    @property
    def host_url(self) -> str:
        """Url with scheme and host. Example: https://localhost:8000."""
        return self.request.host_url

    @property
    def path(self) -> str:
        """The request path."""
        return self.request.path

    @property
    def path_pattern(self) -> str:
        """The matched url with path pattern."""
        path_pattern = (
            self.request.matched_route.pattern
            if self.request.matched_route
            else self.request.path_info
        )
        return self.request.script_name + path_pattern

    @property
    def method(self) -> str:
        """The request method, as lowercase string."""
        return self.request.method.lower()

    @property
    def body(self) -> bytes | str | dict | None:
        """The request body."""
        return self.request.body

    @property
    def content_type(self) -> str:
        """The content type of the request."""
        if self.request.content_type == "multipart/form-data":
            # Pyramid does not include boundary in request.content_type, but
            # openapi-core needs it to parse the request body.
            return self.request.headers.environ.get(
                "CONTENT_TYPE", "multipart/form-data"
            )
        return self.request.content_type

    @property
    def mimetype(self) -> str:
        """The content type of the request."""
        return self.request.content_type


class PyramidOpenAPIResponse:
    """Map Pyramid Response attributes to what openapi expects."""

    def __init__(self, response: Response) -> None:
        self.response = response

    @property
    def data(self) -> bytes:
        """The response body."""
        return self.response.body

    @property
    def status_code(self) -> int:
        """The status code as integer."""
        return self.response.status_code

    @property
    def content_type(self) -> str:
        """The content type of the response."""
        return self.response.content_type

    @property
    def mimetype(self) -> str:
        """The content type of the response."""
        return self.response.content_type

    @property
    def headers(self) -> t.Mapping[str, t.Any]:
        """The response headers."""
        return self.response.headers
