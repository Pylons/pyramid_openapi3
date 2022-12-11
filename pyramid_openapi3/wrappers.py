"""Wrap Pyramid's Request and Response."""

from openapi_core.validation.request.datatypes import RequestParameters
from pyramid.request import Request
from pyramid.response import Response

import typing as t

# Ignore D401 for @property methods as imperative mood docstrings do not make sense
# for them


class PyramidOpenAPIRequest:
    def __init__(self, request: Request) -> None:
        self.request = request

        self.parameters = RequestParameters(
            path=self.request.matchdict,
            query=self.request.GET,
            header=self.request.headers,
            cookie=self.request.cookies,
        )

    @property
    def host_url(self) -> str:
        """Url with scheme and host. Example: https://localhost:8000."""  # noqa D401
        return self.request.host_url

    @property
    def path(self) -> str:
        """The request path."""  # noqa D401
        return self.request.path

    @property
    def path_pattern(self) -> str:
        """The matched url with path pattern."""  # noqa D401
        path_pattern = (
            self.request.matched_route.pattern
            if self.request.matched_route
            else self.request.path_info
        )
        return path_pattern

    @property
    def method(self) -> str:
        """The request method, as lowercase string."""  # noqa D401
        return self.request.method.lower()

    @property
    def body(self) -> t.Optional[t.Union[str, t.Dict]]:
        """The request body, as string."""  # noqa D401
        if "multipart/form-data" == self.request.content_type:
            return self.request.POST.mixed()
        if isinstance(self.request.body, bytes):
            return self.request.body.decode("utf-8")
        return self.request.body

    @property
    def mimetype(self) -> str:
        """The content type of the request."""  # noqa D401
        return self.request.content_type


class PyramidOpenAPIResponse:
    def __init__(self, response: Response) -> None:
        self.response = response

    @property
    def data(self) -> str:
        """The response body, as string."""  # noqa D401
        return self.response.text

    @property
    def status_code(self) -> int:
        """The status code as integer."""  # noqa D401
        return self.response.status_code

    @property
    def mimetype(self) -> str:
        """The content type of the response."""  # noqa D401
        return self.response.content_type

    @property
    def headers(self) -> t.Mapping[str, t.Any]:
        """The response headers."""  # noqa D401
        return self.response.headers
