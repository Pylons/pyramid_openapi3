"""A tween to validate openapi responses."""

from .exceptions import ResponseValidationError
from .wrappers import PyramidOpenAPIRequestFactory
from .wrappers import PyramidOpenAPIResponseFactory
from pyramid.request import Request
from pyramid.response import Response

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
            openapi_request = PyramidOpenAPIRequestFactory.create(request)
            openapi_response = PyramidOpenAPIResponseFactory.create(response)
            settings = request.registry.settings["pyramid_openapi3"]
            result = settings["response_validator"].validate(
                request=openapi_request, response=openapi_response
            )
            if result.errors:
                raise ResponseValidationError(errors=result.errors)
        # If there is no exception view, we also see request validation errors here
        except ResponseValidationError:
            return request.invoke_exception_view(reraise=True)
        return response

    return excview_tween
