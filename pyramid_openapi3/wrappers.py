"""Wrap Pyramid's Request and Response."""

from openapi_core.validation.request.datatypes import OpenAPIRequest
from openapi_core.validation.request.datatypes import RequestParameters
from openapi_core.validation.response.datatypes import OpenAPIResponse
from pyramid.request import Request
from pyramid.response import Response

import typing as t


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
            header=request.headers.items(),
            cookie=request.cookies,
        )
        if "multipart/form-data" == request.content_type:
            body = request.POST.mixed()
        else:
            body = request.body

        return OpenAPIRequest(
            full_url_pattern=full_url_pattern,
            method=method,
            parameters=parameters,
            body=body,
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
