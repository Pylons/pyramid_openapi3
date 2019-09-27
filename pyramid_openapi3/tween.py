"""A tween to validate openapi responses."""

from .exceptions import ResponseValidationError
from .wrappers import PyramidOpenAPIRequest
from .wrappers import PyramidOpenAPIResponse
from pyramid.httpexceptions import HTTPNotFound
from pyramid.request import Request
from pyramid.response import Response
from pyramid.tweens import reraise

import sys
import typing as t


def response_tween_factory(handler, registry) -> t.Callable[[Request], Response]:
    """Create response validation tween.

    This tween should run after pyramid exception renderer view, so that
    final response status and content_type are known and can be validated.

    The only problem here is, that when response validation fails, we have
    to return some exception response, with an unknown content type.
    The advantage is, that these are server errors, and if 500 errors are
    only possible due to response validation errors we don't need to document
    them in the openapi spec file.
    """

    def excview_tween(request: Request) -> Response:
        try:
            response = handler(request)
            if not request.environ.get("pyramid_openapi3.validate_response"):
                # not an openapi view or response validation not requested
                return response
            # validate response
            openapi_request = PyramidOpenAPIRequest.create(request)
            openapi_response = PyramidOpenAPIResponse.create(response)
            settings = request.registry.settings["pyramid_openapi3"]
            result = settings["response_validator"].validate(
                request=openapi_request, response=openapi_response
            )
            if result.errors:
                raise ResponseValidationError(errors=result.errors)
        # If there is no exception view, we also see request validation errors here
        except ResponseValidationError:
            exc_info = sys.exc_info()
            try:
                response = request.invoke_exception_view(exc_info)
            except HTTPNotFound:
                reraise(*exc_info)
            finally:
                del exc_info
            return response
        return response

    return excview_tween
