"""Wrap Pyramid's Request and Response."""

from openapi_core.validation.request.datatypes import OpenAPIRequest
from openapi_core.validation.request.datatypes import RequestParameters
from openapi_core.validation.response.datatypes import OpenAPIResponse
from pyramid.request import Request
from pyramid.response import Response
from urllib.parse import urljoin

import typing as t


class PyramidOpenAPIRequest:
    @classmethod
    def create(
        cls: t.Type["PyramidOpenAPIRequest"], request: Request
    ) -> "OpenAPIRequest":
        """Create OpenAPIRequest from Pyramid Request."""
        method = request.method.lower()
        path_pattern = (
            request.matched_route.pattern if request.matched_route else request.path
        )

        parameters = RequestParameters(
            path=request.matchdict,
            query=request.GET,
            header=request.headers,
            cookie=request.cookies,
        )
        full_url_pattern = urljoin(request.host_url, path_pattern)

        return OpenAPIRequest(
            full_url_pattern=full_url_pattern,
            method=method,
            parameters=parameters,
            body=request.body,
            mimetype=request.content_type,
        )


class PyramidOpenAPIResponse:
    @classmethod
    def create(
        cls: t.Type["PyramidOpenAPIResponse"], response: Response
    ) -> "OpenAPIResponse":
        """Create OpenAPIResponse from Pyramid Response."""
        return OpenAPIResponse(
            data=response.body,
            status_code=response.status_code,
            mimetype=response.content_type,
        )
