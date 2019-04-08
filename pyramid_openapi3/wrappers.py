"""Wrap Pyramid's Request and Response."""

from openapi_core.wrappers.base import BaseOpenAPIRequest
from openapi_core.wrappers.base import BaseOpenAPIResponse


class PyramidOpenAPIRequest(BaseOpenAPIRequest):
    def __init__(self, request):
        self.request = request

    @property
    def host_url(self):
        """Map openapi_core's host_url to pyramid's host_url."""
        return self.request.host_url

    @property
    def path(self):
        """Map openapi_core's path to pyramid's path."""
        return self.request.path

    @property
    def method(self):
        """Map openapi_core's methor to pyramid's method."""
        return self.request.method.lower()

    @property
    def path_pattern(self):
        """Map openapi_core's path_pattern to pyramid's path_pattern."""
        if self.request.matched_route:
            return self.request.matched_route.pattern
        else:
            return self.path

    @property
    def parameters(self):
        """Map openapi_core's parameters to pyramid's request info."""
        return {
            "path": self.request.matchdict,
            "query": self.request.GET,
            "headers": self.request.headers,
            "cookies": self.request.cookies,
        }

    @property
    def body(self):
        """Map openapi_core's body to pyramid's body."""
        return self.request.body

    @property
    def mimetype(self):
        """Map openapi_core's mimetype to pyramid's content_type."""
        return self.request.content_type


class PyramidOpenAPIResponse(BaseOpenAPIResponse):
    def __init__(self, response):
        self.response = response

    @property
    def data(self):
        """Map openapi_core's data to pyramid's body."""
        return self.response.body

    @property
    def status_code(self):
        """Map openapi_core's status_code to pyramid's status_code."""
        return self.response.status_code

    @property
    def mimetype(self):
        """Map openapi_core's mimetype to pyramid's content_type."""
        return self.response.content_type
