"""Wrap Pyramid's Request and Response."""

from openapi_core.wrappers.base import BaseOpenAPIRequest
from openapi_core.wrappers.base import BaseOpenAPIResponse
from pyramid.request import Request
from pyramid.response import Response

import typing as t


class PyramidOpenAPIRequest(BaseOpenAPIRequest):
    def __init__(self, request: Request) -> None:
        self.request = request

    @property
    def host_url(self) -> str:
        """Map openapi_core's host_url to pyramid's host_url."""
        return self.request.host_url

    @property
    def path(self) -> str:
        """Map openapi_core's path to pyramid's path."""
        return self.request.path

    @property
    def method(self) -> str:
        """Map openapi_core's methor to pyramid's method."""
        return self.request.method.lower()

    @property
    def path_pattern(self) -> str:
        """Map openapi_core's path_pattern to pyramid's path_pattern."""
        if self.request.matched_route:
            return self.request.matched_route.pattern
        else:
            return self.path

    @property
    def parameters(self) -> t.Dict:
        """Map openapi_core's parameters to pyramid's request info."""
        return {
            "path": self.request.matchdict,
            "query": self.request.GET,
            "header": self.request.headers,
            "cookie": self.request.cookies,
        }

    @property
    def body(self) -> str:
        """Map openapi_core's body to pyramid's body."""
        return self.request.body

    @property
    def mimetype(self) -> str:
        """Map openapi_core's mimetype to pyramid's content_type."""
        return self.request.content_type


class PyramidOpenAPIResponse(BaseOpenAPIResponse):
    def __init__(self, response: Response):
        self.response = response

    @property
    def data(self) -> bytes:
        """Map openapi_core's data to pyramid's body."""
        return self.response.body

    @property
    def status_code(self) -> int:
        """Map openapi_core's status_code to pyramid's status_code."""
        return self.response.status_code

    @property
    def mimetype(self) -> str:
        """Map openapi_core's mimetype to pyramid's content_type."""
        return self.response.content_type
