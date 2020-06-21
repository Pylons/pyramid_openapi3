"""Configure pyramid_openapi3 addon."""

from .exceptions import extract_errors
from .exceptions import RequestValidationError
from .exceptions import ResponseValidationError
from .wrappers import PyramidOpenAPIRequestFactory
from openapi_core import create_spec
from openapi_core.validation.exceptions import InvalidSecurity
from openapi_core.validation.request.validators import RequestValidator
from openapi_core.validation.response.validators import ResponseValidator
from openapi_spec_validator import validate_spec
from openapi_spec_validator.schemas import read_yaml_file
from pyramid.config import Configurator
from pyramid.config import PHASE0_CONFIG
from pyramid.config.views import ViewDeriverInfo
from pyramid.exceptions import ConfigurationError
from pyramid.httpexceptions import exception_response
from pyramid.path import AssetResolver
from pyramid.request import Request
from pyramid.response import FileResponse
from pyramid.response import Response
from pyramid.tweens import EXCVIEW
from string import Template

import hupper
import logging
import typing as t

logger = logging.getLogger(__name__)


def includeme(config: Configurator) -> None:
    """Pyramid knob."""
    config.add_view_deriver(openapi_view)
    config.add_directive("pyramid_openapi3_add_formatter", add_formatter)
    config.add_directive("pyramid_openapi3_add_explorer", add_explorer_view)
    config.add_directive("pyramid_openapi3_spec", add_spec_view)
    config.add_tween("pyramid_openapi3.tween.response_tween_factory", over=EXCVIEW)

    if not config.registry.settings.get(  # pragma: no branch
        "pyramid_openapi3_extract_errors"
    ):
        config.registry.settings["pyramid_openapi3_extract_errors"] = extract_errors

    config.add_exception_view(
        view=openapi_validation_error, context=RequestValidationError, renderer="json"
    )

    config.add_exception_view(
        view=openapi_validation_error, context=ResponseValidationError, renderer="json"
    )


Context = t.TypeVar("Context")
View = t.Callable[[Context, Request], Response]


def openapi_view(view: View, info: ViewDeriverInfo) -> View:
    """View deriver that takes care of request/response validation.

    If `openapi=True` is passed to `@view_config`, this decorator will:

    - validate request and submit results into request.openapi_validated
    - Only request is validated here. The response is validated inside a tween,
    so that other tweens can intercept the response, and only the final
    response is validated against the openapi spec.
    """
    if info.options.get("openapi"):

        def wrapper_view(context: Context, request: Request) -> Response:
            # Validate request and attach all findings for view to introspect
            request.environ["pyramid_openapi3.validate_response"] = True
            settings = request.registry.settings["pyramid_openapi3"]

            # Needed to support relative `servers` entries in `openapi.yaml`,
            # see https://github.com/p1c2u/openapi-core/issues/218.
            settings["request_validator"].base_url = request.application_url
            settings["response_validator"].base_url = request.application_url

            openapi_request = PyramidOpenAPIRequestFactory.create(request)
            request.openapi_validated = settings["request_validator"].validate(
                openapi_request
            )
            if request.openapi_validated.errors:
                raise RequestValidationError(errors=request.openapi_validated.errors)
            # Do the view
            return view(context, request)

        return wrapper_view
    return view


openapi_view.options = ("openapi",)  # type: ignore


def add_explorer_view(
    config: Configurator,
    route: str = "/docs/",
    route_name: str = "pyramid_openapi3.explorer",
    template: str = "static/index.html",
    ui_version: str = "3.17.1",
) -> None:
    """Serve Swagger UI at `route` url path.

    :param route: URL path where to serve
    :param route_name: Route name that's being added
    :param template: Dotted path to the html template that renders Swagger UI response
    :param ui_version: Swagger UI version string
    """

    def register() -> None:
        resolved_template = AssetResolver().resolve(template)

        def explorer_view(request: Request) -> Response:
            settings = config.registry.settings
            if settings.get("pyramid_openapi3") is None:
                raise ConfigurationError(
                    "You need to call config.pyramid_openapi3_spec for explorer to work."
                )
            with open(resolved_template.abspath()) as f:
                template = Template(f.read())
                html = template.safe_substitute(
                    ui_version=ui_version,
                    spec_url=request.route_url(
                        settings["pyramid_openapi3"]["spec_route_name"]
                    ),
                )
            return Response(html)

        config.add_route(route_name, route)
        config.add_view(route_name=route_name, view=explorer_view)

    config.action(("pyramid_openapi3_add_explorer",), register, order=PHASE0_CONFIG)


def add_formatter(config: Configurator, name: str, func: t.Callable) -> None:
    """Add support for configuring formatters."""
    config.registry.settings.setdefault("pyramid_openapi3_formatters", {})
    reg = config.registry.settings["pyramid_openapi3_formatters"]
    reg[name] = func


def add_spec_view(
    config: Configurator,
    filepath: str,
    route: str = "/openapi.yaml",
    route_name: str = "pyramid_openapi3.spec",
) -> None:
    """Serve and register OpenApi 3.0 specification file.

    :param filepath: absolute/relative path to the specification file
    :param route: URL path where to serve specification file
    :param route_name: Route name under which specification file will be served
    """

    def register() -> None:
        if hupper.is_active():  # pragma: no cover
            hupper.get_reloader().watch_files([filepath])
        spec_dict = read_yaml_file(filepath)

        validate_spec(spec_dict)
        spec = create_spec(spec_dict)

        def spec_view(request: Request) -> FileResponse:
            return FileResponse(filepath, request=request, content_type="text/yaml")

        config.add_route(route_name, route)
        config.add_view(route_name=route_name, view=spec_view)

        custom_formatters = config.registry.settings.get("pyramid_openapi3_formatters")

        config.registry.settings["pyramid_openapi3"] = {
            "filepath": filepath,
            "spec_route_name": route_name,
            "spec": spec,
            "request_validator": RequestValidator(
                spec, custom_formatters=custom_formatters
            ),
            "response_validator": ResponseValidator(
                spec, custom_formatters=custom_formatters
            ),
        }

    config.action(("pyramid_openapi3_spec",), register, order=PHASE0_CONFIG)


def openapi_validation_error(
    context: t.Union[RequestValidationError, ResponseValidationError], request: Request
) -> Response:
    """Render any validation errors as JSON."""
    if isinstance(context, RequestValidationError):
        logger.warning(context)
    if isinstance(context, ResponseValidationError):
        logger.error(context)

    extract_errors = request.registry.settings["pyramid_openapi3_extract_errors"]
    errors = list(extract_errors(request, context.errors))

    # If validation failed for request, it is user's fault (-> 400), but if
    # validation failed for response, it is our fault (-> 500)
    if isinstance(context, RequestValidationError):
        status_code = 400
        for error in context.errors:
            if isinstance(error, InvalidSecurity):
                status_code = 401

    if isinstance(context, ResponseValidationError):
        status_code = 500

    return exception_response(status_code, json_body=errors)
