"""Wrap Pyramid's Request and Response."""

from openapi_core.validation.request.datatypes import OpenAPIRequest
from openapi_core.validation.request.datatypes import RequestParameters
from openapi_core.validation.response.datatypes import OpenAPIResponse
from pyramid.request import Request
from pyramid.response import Response

import typing as t


def request_headers(request: Request):
    """
    request_headers extract headers from a pyramid Request.

    :return : a dict items from openapi_core 0.13.4, a dict in previous versions
    """
    import openapi_core

    use_dict = openapi_core.__version__ < "0.13.4"
    return request.headers if use_dict else request.headers.items()


class PyramidOpenAPIRequestFactory:
    @classmethod
    def create(
        cls: t.Type["PyramidOpenAPIRequestFactory"], request: Request
    ) -> "OpenAPIRequest":
        """Create OpenAPIRequest from Pyramid Request."""
        method = request.method.lower()
        path_pattern = (
            request.matched_route.pattern
            if request.matched_route
            else request.path_info
        )
        # a path pattern is not normalized in pyramid so it may or may not
        # start with a leading /, so normalize it here
        path_pattern = path_pattern.lstrip("/")
        full_url_pattern = request.application_url + "/" + path_pattern

        parameters = RequestParameters(
            path=request.matchdict,
            query=request.GET,
            header=request_headers(request),
            cookie=request.cookies,
        )

        return OpenAPIRequest(
            full_url_pattern=full_url_pattern,
            method=method,
            parameters=parameters,
            body=request.body,
            mimetype=request.content_type,
        )


class PyramidOpenAPIResponseFactory:
    @classmethod
    def create(
        cls: t.Type["PyramidOpenAPIResponseFactory"], response: Response
    ) -> "OpenAPIResponse":
        """Create OpenAPIResponse from Pyramid Response."""
        return OpenAPIResponse(
            data=response.body,
            status_code=response.status_code,
            mimetype=response.content_type,
        )
