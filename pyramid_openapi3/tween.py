"""A tween to validate openapi responses."""
from .exceptions import ImproperAPISpecificationWarning
from .exceptions import ResponseValidationError
from .wrappers import PyramidOpenAPIRequestFactory
from .wrappers import PyramidOpenAPIResponseFactory
from pyramid.request import Request
from pyramid.response import Response

import typing as t
import warnings


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
            settings_key = "pyramid_openapi3"
            gsettings = settings = request.registry.settings[settings_key]
            if "routes" in gsettings:
                settings_key = gsettings["routes"][request.matched_route.name]
                settings = request.registry.settings[settings_key]
            result = settings["response_validator"].validate(
                request=openapi_request, response=openapi_response
            )
            request_validated = request.environ.get("pyramid_openapi3.validate_request")
            if result.errors:
                if request_validated and request.openapi_validated.errors:
                    warnings.warn_explicit(
                        ImproperAPISpecificationWarning(
                            "Discarding {response.status} validation error with body "
                            "{response.text} as it is not a valid response for "
                            "{request.method} to {request.path} ({route.name})".format(
                                response=response,
                                request=request,
                                route=request.matched_route,
                            )
                        ),
                        None,
                        registry.settings[settings_key]["filepath"],
                        0,
                    )
                raise ResponseValidationError(response=response, errors=result.errors)

        # If there is no exception view, we also see request validation errors here
        except ResponseValidationError:
            return request.invoke_exception_view(reraise=True)
        return response

    return excview_tween
