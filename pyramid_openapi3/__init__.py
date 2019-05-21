"""Configure pyramid_openapi3 addon."""

from .wrappers import PyramidOpenAPIRequest
from .wrappers import PyramidOpenAPIResponse
from openapi_core import create_spec
from openapi_core.shortcuts import RequestValidator
from openapi_core.shortcuts import ResponseValidator
from openapi_spec_validator import validate_spec
from openapi_spec_validator.schemas import read_yaml_file
from pyramid.config import Configurator
from pyramid.config import PHASE0_CONFIG
from pyramid.config.views import ViewDeriverInfo
from pyramid.exceptions import ConfigurationError
from pyramid.httpexceptions import HTTPException
from pyramid.path import AssetResolver
from pyramid.request import Request
from pyramid.response import FileResponse
from pyramid.response import Response
from pyramid.view import render_view_to_response
from string import Template

import typing as t


def includeme(config: Configurator) -> None:
    """Pyramid knob."""
    config.add_view_deriver(openapi_view)
    config.add_directive("pyramid_openapi3_add_formatter", add_formatter)
    config.add_directive("pyramid_openapi3_add_explorer", add_explorer_view)
    config.add_directive("pyramid_openapi3_spec", add_spec_view)
    config.add_directive(
        "pyramid_openapi3_validation_error_view", add_validation_error_view
    )


View = t.Callable[[t.Any, Request], Response]


def openapi_view(view: View, info: ViewDeriverInfo) -> t.Optional[View]:
    """View deriver that takes care of request/response validation.

    If `openapi=True` is passed to `@view_config`, this decorator will:

    - validate request and submit results into request.openapi_validated
    - validate response and raise an Exception if errors are found
    """
    if info.options.get("openapi"):

        def wrapper_view(context, request):
            # Validate request and attach all findings for view to introspect
            settings = request.registry.settings["pyramid_openapi3"]
            open_request = PyramidOpenAPIRequest(request)
            request.openapi_validated = settings["request_validator"].validate(
                open_request
            )

            try:
                if request.openapi_validated.errors and getattr(
                    request.registry, "_pyramid_openapi3_validation_view_name", None
                ):
                    # handle request errors
                    view_name = (
                        request.registry._pyramid_openapi3_validation_view_name  # noqa: SF01
                    )
                    response = render_view_to_response(
                        context, request, name=view_name, secure=False
                    )
                else:
                    # Do the view
                    request.openapi_validated.raise_for_errors()
                    response = view(context, request)

            except HTTPException as exc:
                # If view raises one of the HTTPExceptions, catch it
                # so that we can validate the response and hence make sure
                # all possible responses are documented in openapi spec.
                response = exc

            # Validate response and raise if an error is found
            open_response = PyramidOpenAPIResponse(response)
            result = settings["response_validator"].validate(
                request=open_request, response=open_response
            )
            result.raise_for_errors()

            return response

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

    def register():
        resolved_template = AssetResolver().resolve(template)

        def explorer_view(request):
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


def add_formatter(config: Configurator, name: str, func: t.Callable):
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
            "request_validator": RequestValidator(spec, custom_formatters),
            "response_validator": ResponseValidator(spec, custom_formatters),
        }

    config.action(("pyramid_openapi3_spec",), register, order=PHASE0_CONFIG)


def add_validation_error_view(config: Configurator, view_name: str) -> None:
    """Use this to register a view for rendering validation errors."""

    def register() -> None:
        config.registry._pyramid_openapi3_validation_view_name = view_name  # noqa: SF01

    config.action(
        ("pyramid_openapi3_validation_error_view",), register, order=PHASE0_CONFIG
    )
