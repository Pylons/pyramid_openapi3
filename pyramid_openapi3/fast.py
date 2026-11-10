"""Response validation with jsonschema-rs, the Rust JSON Schema validator."""

from .wrappers import PyramidOpenAPIRequest
from .wrappers import PyramidOpenAPIResponse
from functools import partial
from jsonschema_path import SchemaPath
from jsonschema_path.handlers import default_handlers
from jsonschema_path.retrievers import SchemaRetriever
from openapi_core.templating.media_types.exceptions import MediaTypeNotFound
from openapi_core.templating.media_types.finders import MediaTypeFinder
from openapi_core.templating.paths.exceptions import PathError
from openapi_core.templating.paths.finders import APICallPathFinder
from openapi_core.templating.responses.exceptions import ResponseFinderError
from openapi_core.templating.responses.finders import ResponseFinder
from openapi_schema_validator import OAS30ReadValidator
from pyramid.exceptions import ConfigurationError
from referencing import Registry
from referencing.jsonschema import DRAFT202012
from urllib.parse import urldefrag
from urllib.parse import urljoin
from xml.etree.ElementTree import ParseError

import json
import jsonschema_rs
import re
import typing as t


class FastValidationError(Exception):
    """A response body that cannot be read or does not match its schema."""

    def __init__(self, message: str, path: list[str | int] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.path = path or []


def is_json(mimetype: str) -> bool:
    """Whether a media type carries a JSON body."""
    mimetype = mimetype.lower()
    return mimetype == "application/json" or mimetype.endswith("+json")


# The OpenAPI formats openapi-core checks that jsonschema-rs does not know:
# `byte` through openapi-core's own check, `int32` and `int64` as the bounds
# `bound_integer` writes into the schema, since a format only sees strings.
OAS_FORMATS = {
    "byte": partial(OAS30ReadValidator.FORMAT_CHECKER.conforms, format="byte")
}
INTEGER_BOUNDS = {"int32": 1 << 31, "int64": 1 << 63}

METHODS = frozenset(
    {"delete", "get", "head", "options", "patch", "post", "put", "trace"}
)
SCHEMA_KEYWORDS = frozenset(
    {
        "additionalProperties",
        "contains",
        "contentSchema",
        "else",
        "if",
        "items",
        "not",
        "propertyNames",
        "then",
        "unevaluatedItems",
        "unevaluatedProperties",
    }
)
SCHEMA_LIST_KEYWORDS = frozenset({"allOf", "anyOf", "oneOf", "prefixItems"})
SCHEMA_MAP_KEYWORDS = frozenset(
    {"$defs", "definitions", "dependentSchemas", "patternProperties", "properties"}
)


def bound_integer(schema: dict[str, t.Any]) -> dict[str, t.Any]:
    """Turn an `int32` or `int64` format into the bounds it stands for."""
    bound = INTEGER_BOUNDS.get(schema.get("format", ""))
    if bound:
        schema["exclusiveMinimum"] = max(schema.get("exclusiveMinimum", ~bound), ~bound)
        schema["exclusiveMaximum"] = min(schema.get("exclusiveMaximum", bound), bound)
    return schema


def response_schemas(spec: SchemaPath) -> t.Iterator[SchemaPath]:
    """Yield the schema of every response media type in the spec's paths."""
    for path in spec.get("paths", {}):
        for method, operation in path.items():
            if method not in METHODS:
                continue
            for response in operation.get("responses", {}):
                for media_type in response.get("content", {}):
                    if "schema" in media_type:
                        yield media_type / "schema"


class FastResponseValidator:
    """Validate response bodies with jsonschema-rs instead of python-jsonschema.

    python-jsonschema walks a schema in Python, which on a large response
    takes hundreds of milliseconds and is most of what a list endpoint costs.
    jsonschema-rs does the same walk in Rust. The operation, status and media
    type are found the way openapi-core finds them, then the JSON body is
    checked against a validator compiled at startup for each response schema.
    Bodies of other media types and response headers are not validated.
    """

    def __init__(
        self,
        spec: SchemaPath,
        formats: dict[str, t.Callable[[t.Any], bool]] | None = None,
        deserializers: dict[str, t.Callable[[bytes], t.Any]] | None = None,
    ) -> None:
        self.formats = {**OAS_FORMATS, **(formats or {})}
        self.deserializers = deserializers or {}
        self.finder = APICallPathFinder(spec)
        self.base_uri = spec.base_uri
        self.registry = Registry(
            retrieve=SchemaRetriever(default_handlers, DRAFT202012)
        ).with_resource(spec.base_uri, DRAFT202012.create_resource(spec.read_value()))
        self.validators = {
            schema.parts: self.compile(schema) for schema in response_schemas(spec)
        }

    def iter_errors(
        self, request: PyramidOpenAPIRequest, response: PyramidOpenAPIResponse
    ) -> t.Iterator[Exception]:
        """Yield what is wrong with the response, nothing when it is valid."""
        try:
            operation = self.finder.find(
                request.method, urljoin(request.host_url, request.path_pattern)
            ).operation
            operation_response = ResponseFinder(operation / "responses").find(
                str(response.status_code)
            )
        except (PathError, ResponseFinderError) as error:
            yield error
            return
        if "content" not in operation_response:
            return
        try:
            mimetype, _, media_type = MediaTypeFinder(
                operation_response / "content"
            ).find(response.content_type)
        except MediaTypeNotFound as error:
            yield error
            return
        if "schema" in media_type:
            yield from self.validate(mimetype, media_type / "schema", response)

    def validate(
        self, mimetype: str, schema: SchemaPath, response: PyramidOpenAPIResponse
    ) -> t.Iterator[FastValidationError]:
        """Yield what is wrong with the body, read by a deserializer or as JSON."""
        deserialize = self.deserializers.get(mimetype)
        if deserialize is None:
            if not is_json(response.content_type):
                return
            deserialize = json.loads
        try:
            data = deserialize(response.data)
        except (ParseError, ValueError, TypeError, AttributeError) as error:
            yield FastValidationError(f"Response body is not {mimetype}: {error}")
            return
        try:
            errors = list(self.validators[schema.parts].iter_errors(data))
        except ValueError as error:
            yield FastValidationError(f"Response body is not JSON data: {error}")
            return
        for error in errors:
            path = list(error.instance_path)
            if isinstance(error.kind, jsonschema_rs.ValidationErrorKind.Required):
                path.append(error.kind.property)
            yield FastValidationError(error.message, path)

    def compile(self, schema: SchemaPath) -> jsonschema_rs.Draft202012Validator:
        """Compile the schema at `schema`, refusing one jsonschema-rs cannot take."""
        document = self.dereference(schema)
        if isinstance(document, bool):
            document = {} if document else {"not": {}}
        try:
            return jsonschema_rs.Draft202012Validator(
                document, formats=self.formats, validate_formats=True
            )
        except jsonschema_rs.ValidationError as error:
            raise ConfigurationError(
                f"Response schema {schema} cannot be compiled "
                f"with jsonschema-rs: {error.message}"
            ) from error

    def lookup(self, uri: str) -> t.Any:
        """Return the value the absolute `uri` names, reading each file once."""
        document, fragment = urldefrag(uri)
        retrieved = self.registry.get_or_retrieve(document)
        self.registry = retrieved.registry
        resolver = self.registry.resolver(base_uri=document)
        return resolver.lookup(f"#{fragment}").contents

    def locate(self, schema: SchemaPath) -> tuple[str, t.Any]:
        """Return the file `schema` is in and its value there, `$ref`s intact."""
        base_uri, value = self.base_uri, self.lookup(self.base_uri)
        for part in schema.parts:
            while isinstance(value, dict) and "$ref" in value:
                uri = urljoin(base_uri, value["$ref"])
                base_uri, value = urldefrag(uri).url, self.lookup(uri)
            value = value[part]
        return base_uri, value

    def dereference(self, schema: SchemaPath) -> dict[str, t.Any] | bool:
        """Copy the schema at `schema` into one document with every `$ref` resolved.

        References are followed wherever they lead, within the file or into
        another one. Each referenced schema becomes an entry under `$defs`, so
        a schema used in several places is compiled once and a recursive schema
        terminates. Only the keywords that hold subschemas are walked, so a
        `$ref` inside a literal value such as `const` or `default` is data, and
        the constraints beside a `$ref` are kept. A file's `$id` is left out,
        since every reference now points into this document, and a
        `$dynamicRef` is refused, since one document cannot keep the dynamic
        scope it needs.

        jsonschema_rs.dereference leaves a circular `$ref` pointing into the
        spec, where a lone subschema cannot follow it, and compiling the whole
        spec per response copies it into every validator: 4 MB each, 400 MB of
        RAM for a spec with 100 validators.
        """
        defs: dict[str, t.Any] = {}
        names: dict[str, str] = {}

        def walk(base_uri: str, value: t.Any) -> t.Any:
            if not isinstance(value, dict):
                return value
            out: dict[str, t.Any] = {}
            for key, child in value.items():
                if key == "$dynamicRef":
                    raise ConfigurationError(
                        f"`$dynamicRef` in {base_uri} is not supported by fast "
                        "response validation: it copies every referenced schema "
                        "into one document, where a dynamic scope cannot be kept."
                    )
                if key == "$ref":
                    uri = urljoin(base_uri, child)
                    if uri not in names:
                        tail = re.sub(
                            r"[^\w.-]", "_", uri.rsplit("/", 1)[-1], flags=re.ASCII
                        )
                        name = names[uri] = f"{len(names)}-{tail}"
                        defs[name] = None
                        defs[name] = walk(urldefrag(uri).url, self.lookup(uri))
                    out["$ref"] = f"#/$defs/{names[uri]}"
                elif key in SCHEMA_KEYWORDS:
                    out[key] = walk(base_uri, child)
                elif key in SCHEMA_LIST_KEYWORDS:
                    out[key] = [walk(base_uri, item) for item in child]
                elif key in SCHEMA_MAP_KEYWORDS:
                    out[key] = {k: walk(base_uri, item) for k, item in child.items()}
                else:
                    out[key] = child
            out.pop("$id", None)
            return bound_integer(out)

        root = walk(*self.locate(schema))
        return {**root, "$defs": {**root.get("$defs", {}), **defs}} if defs else root
