"""Tests for response validation with jsonschema-rs."""

from collections.abc import Iterator
from jsonschema_path import SchemaPath
from jsonschema_path.retrievers import SchemaRetriever
from pathlib import Path
from pyramid import testing
from pyramid.config import Configurator
from pyramid.exceptions import ConfigurationError
from pyramid.httpexceptions import HTTPNotFound
from pyramid.response import Response
from pyramid.router import Router
from pyramid_openapi3.fast import FastResponseValidator
from pyramid_openapi3.tests.utils import DummyStartResponse
from xml.etree.ElementTree import fromstring

import json
import pytest
import sys
import typing as t
import yaml

SPEC = b"""
openapi: '3.1.0'
info:
  version: '1.0.0'
  title: Foo API
paths:
  /items/{id}:
    parameters:
      - name: id
        in: path
        required: true
        schema:
          type: string
    get:
      responses:
        '200':
          description: An item
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Item'
        '204':
          description: Nothing
  /page:
    get:
      responses:
        '200':
          description: A page
          content:
            text/html:
              schema:
                type: string
components:
  schemas:
    Item:
      type: object
      required:
        - id
        - when
      properties:
        id:
          type: string
        when:
          type: string
          format: date
        tag:
          type: string
          format: tagged
      unevaluatedProperties: false
"""

SPEC_30 = SPEC.replace(b"3.1.0", b"3.0.0").replace(
    b"      unevaluatedProperties: false\n", b""
)
ITEM = {"id": "1", "when": "2026-11-10"}
FAST = {"pyramid_openapi3.fast_response_validation": "true"}


def spec_for(schema: str, media: str = "application/json") -> bytes:
    """Write a spec whose one operation, GET /x, serves `schema` as `media`."""
    return f"""
openapi: '3.1.0'
info:
  version: '1.0.0'
  title: Foo API
paths:
  /x:
    get:
      responses:
        '200':
          description: Anything
          content:
            '{media}':
              schema: {schema}
""".encode()


def serve(
    config: Configurator, body: bytes, content_type: str = "application/json"
) -> tuple[str, bytes]:
    """Serve `body` from /x and return the status line and body of a GET."""
    config.add_route("x", "/x")
    config.add_view(
        lambda *_: Response(body=body, content_type=content_type, charset=None),
        route_name="x",
        openapi=True,
    )
    return call(config, "/x")


def call(config: Configurator, path: str) -> tuple[str, bytes]:
    """Run a GET through the router and return the status line and body."""
    environ = {
        "wsgi.url_scheme": "http",
        "SERVER_NAME": "localhost",
        "SERVER_PORT": "8080",
        "REQUEST_METHOD": "GET",
        "PATH_INFO": path,
        "HTTP_ACCEPT": "application/json",
    }
    start_response = DummyStartResponse()
    body = Router(config.registry)(environ, start_response)
    return start_response.status, b"".join(body)


def errors(body: bytes) -> list[dict[str, str]]:
    """Read the validation errors a 500 body carries."""
    return json.loads(body)


@pytest.fixture
def config(write_spec: t.Callable[..., str]) -> Iterator[Configurator]:
    """Configure an app with fast response validation on."""
    settings = {"pyramid_openapi3.fast_response_validation": "true"}
    with testing.testConfig(settings=settings) as config:
        config.include("pyramid_openapi3")
        config.pyramid_openapi3_add_formatter("tagged", lambda v: v.startswith("#"))
        config.pyramid_openapi3_spec(write_spec(SPEC))
        config.add_route("item", "/items/{id}")
        config.add_route("page", "/page")
        yield config


def add_item_view(config: Configurator, result: t.Any, **kw: t.Any) -> None:
    """Serve `result` from /items/{id} as JSON unless `kw` says otherwise."""
    config.add_view(
        lambda *_: result,
        route_name="item",
        openapi=True,
        **({"renderer": "json"} | kw),
    )


def test_valid_response_passes(config: Configurator) -> None:
    """A body that matches the schema goes through untouched."""
    add_item_view(config, ITEM)
    status, body = call(config, "/items/1")
    assert status == "200 OK"
    assert json.loads(body) == ITEM


@pytest.mark.parametrize(
    ("item", "error"),
    [
        (
            {"id": "1"},
            {
                "exception": "FastValidationError",
                "message": '"when" is a required property',
                "field": "when",
            },
        ),
        (
            {**ITEM, "id": 5},
            {
                "exception": "FastValidationError",
                "message": '5 is not of type "string"',
                "field": "id",
            },
        ),
        (
            {**ITEM, "extra": 1},
            {
                "exception": "FastValidationError",
                "message": "Unevaluated properties are not allowed ('extra' was unexpected)",
            },
        ),
        (
            {**ITEM, "when": "yesterday"},
            {
                "exception": "FastValidationError",
                "message": '"yesterday" is not a "date"',
                "field": "when",
            },
        ),
        (
            {**ITEM, "tag": "untagged"},
            {
                "exception": "FastValidationError",
                "message": '"untagged" is not a "tagged"',
                "field": "tag",
            },
        ),
    ],
)
def test_invalid_response_is_a_500(
    config: Configurator, item: dict[str, t.Any], error: dict[str, str]
) -> None:
    """A body off the schema, in type, shape or format, is a server error."""
    add_item_view(config, item)
    status, body = call(config, "/items/1")
    assert status == "500 Internal Server Error"
    assert errors(body) == [error]


def test_custom_format_passes(config: Configurator) -> None:
    """A registered formatter decides its format."""
    add_item_view(config, {**ITEM, "tag": "#ok"})
    status, _ = call(config, "/items/1")
    assert status == "200 OK"


def test_response_without_content_passes(config: Configurator) -> None:
    """A status the spec gives no body for needs none."""
    add_item_view(config, Response(status=204), renderer=None)
    status, _ = call(config, "/items/1")
    assert status == "204 No Content"


def test_non_json_body_is_not_validated(config: Configurator) -> None:
    """Only JSON bodies are checked; other media types pass as they are."""
    config.add_view(
        lambda *_: Response("<p>anything</p>", content_type="text/html"),
        route_name="page",
        openapi=True,
    )
    status, _ = call(config, "/page")
    assert status == "200 OK"


def test_json_content_type_is_matched_in_any_case(
    write_spec: t.Callable[..., str],
) -> None:
    """A media type is case-insensitive, so `Application/JSON` is still JSON."""
    with testing.testConfig(settings=FAST) as config:
        config.include("pyramid_openapi3")
        config.pyramid_openapi3_spec(
            write_spec(spec_for("{type: object, properties: {id: {type: string}}}"))
        )
        status, body = serve(config, b'{"id": 5}', content_type="Application/JSON")
    assert status == "500 Internal Server Error"
    assert errors(body) == [
        {
            "exception": "FastValidationError",
            "message": '5 is not of type "string"',
            "field": "id",
        }
    ]


def test_undeclared_status_is_a_500(config: Configurator) -> None:
    """A status the operation does not declare is reported like openapi-core does."""
    add_item_view(config, HTTPNotFound(), renderer=None)
    status, body = call(config, "/items/1")
    assert status == "500 Internal Server Error"
    assert errors(body) == [
        {
            "exception": "ResponseNotFound",
            "message": "Unknown response http status: 404",
        }
    ]


def test_undeclared_media_type_is_a_500(config: Configurator) -> None:
    """A media type the response does not declare is reported."""
    add_item_view(config, Response("1", content_type="text/plain"), renderer=None)
    status, body = call(config, "/items/1")
    assert status == "500 Internal Server Error"
    assert errors(body) == [
        {
            "exception": "MediaTypeNotFound",
            "message": "Content for the following mimetype not found: text/plain. "
            "Valid mimetypes: ['application/json']",
        }
    ]


def test_broken_json_body_is_a_500(config: Configurator) -> None:
    """A JSON response that is not JSON is reported."""
    add_item_view(
        config, Response(body=b"{", content_type="application/json"), renderer=None
    )
    status, body = call(config, "/items/1")
    assert status == "500 Internal Server Error"
    assert errors(body) == [
        {
            "exception": "FastValidationError",
            "message": "Response body is not application/json: Expecting property "
            "name enclosed in double quotes: line 1 column 2 (char 1)",
        }
    ]


def test_validators_are_compiled_at_startup(config: Configurator) -> None:
    """Every response media type with a schema gets its validator before a request."""
    validator = config.registry.settings["pyramid_openapi3"]["response_validator"]
    assert [parts[1:5] + parts[6:7] for parts in validator.validators] == [
        ("/items/{id}", "get", "responses", "200", "application/json"),
        ("/page", "get", "responses", "200", "text/html"),
    ]


def test_schema_jsonschema_rs_cannot_compile_is_refused(
    write_spec: t.Callable[..., str],
) -> None:
    """A pattern in Python-only syntax fails at startup, not on the first response."""
    with testing.testConfig(settings=FAST) as config:
        config.include("pyramid_openapi3")
        with pytest.raises(ConfigurationError) as info:
            config.pyramid_openapi3_spec(
                write_spec(spec_for(r"{type: string, pattern: 'a\Z'}"))
            )
    assert str(info.value) == (
        "Response schema paths#/x#get#responses#200#content#application/json#schema "
        'cannot be compiled with jsonschema-rs: "a\\\\Z" is not a "regex"'
    )


def test_dereference_inlines_shared_and_recursive_schemas() -> None:
    """Every `$ref` target lands in `$defs` once, cycles included."""
    spec = SchemaPath.from_dict(
        {
            "root": {"$ref": "#/defs/Tree"},
            "defs": {
                "Tree": {
                    "type": "object",
                    "properties": {
                        "name": {"$ref": "#/defs/Name"},
                        "alias": {"$ref": "#/defs/Name"},
                        "children": {"type": "array", "items": {"$ref": "#/defs/Tree"}},
                    },
                },
                "Name": {"type": "string"},
            },
        }
    )
    assert FastResponseValidator(spec).dereference(spec / "root") == {
        "$ref": "#/$defs/0-Tree",
        "$defs": {
            "0-Tree": {
                "type": "object",
                "properties": {
                    "name": {"$ref": "#/$defs/1-Name"},
                    "alias": {"$ref": "#/$defs/1-Name"},
                    "children": {"type": "array", "items": {"$ref": "#/$defs/0-Tree"}},
                },
            },
            "1-Name": {"type": "string"},
        },
    }


def test_dereference_keeps_constraints_beside_a_reference() -> None:
    """A `$ref` with siblings keeps them, the way JSON Schema 2020-12 reads them."""
    spec = SchemaPath.from_dict(
        {
            "root": {"$ref": "#/defs/Code", "maxLength": 3, "description": "Short"},
            "defs": {"Code": {"type": "string"}},
        }
    )
    assert FastResponseValidator(spec).dereference(spec / "root") == {
        "$ref": "#/$defs/0-Code",
        "maxLength": 3,
        "description": "Short",
        "$defs": {"0-Code": {"type": "string"}},
    }


@pytest.mark.parametrize("schema", [True, False])
def test_dereference_accepts_boolean_schemas(schema: bool) -> None:
    """`true` and `false` are schemas too, at the root and inside another."""
    spec = SchemaPath.from_dict(
        {"root": schema, "nested": {"allOf": [schema], "properties": {"a": schema}}}
    )
    assert FastResponseValidator(spec).dereference(spec / "root") is schema
    assert FastResponseValidator(spec).dereference(spec / "nested") == {
        "allOf": [schema],
        "properties": {"a": schema},
    }


@pytest.mark.parametrize(
    ("schema", "status"), [("true", "200 OK"), ("false", "500 Internal Server Error")]
)
def test_boolean_response_schema_is_compiled(
    write_spec: t.Callable[..., str], schema: str, status: str
) -> None:
    """A response whose whole schema is `true` or `false` validates as such."""
    with testing.testConfig(settings=FAST) as config:
        config.include("pyramid_openapi3")
        config.pyramid_openapi3_spec(write_spec(spec_for(schema)))
        assert serve(config, b"{}")[0] == status


def test_dereference_leaves_literal_values_alone() -> None:
    """A `$ref` key inside `const`, `enum` or `default` is data, not a reference.

    A property named after a keyword is still a schema, and still resolved.
    """
    spec = SchemaPath.from_dict(
        {
            "root": {
                "const": {"$ref": "literal"},
                "enum": [{"$ref": "literal"}],
                "default": {"$ref": "literal"},
                "examples": [{"$ref": "literal"}],
                "properties": {"default": {"$ref": "#/defs/Name"}},
            },
            "defs": {"Name": {"type": "string"}},
        }
    )
    assert FastResponseValidator(spec).dereference(spec / "root") == {
        "const": {"$ref": "literal"},
        "enum": [{"$ref": "literal"}],
        "default": {"$ref": "literal"},
        "examples": [{"$ref": "literal"}],
        "properties": {"default": {"$ref": "#/$defs/0-Name"}},
        "$defs": {"0-Name": {"type": "string"}},
    }


def test_openapi_30_spec_is_refused(write_spec: t.Callable[..., str]) -> None:
    """3.0 schemas are not JSON Schema, so they cannot be validated this way."""
    with testing.testConfig(settings=FAST) as config:
        config.include("pyramid_openapi3")
        with pytest.raises(ConfigurationError, match=r"needs an OpenAPI 3\.1 or newer"):
            config.pyramid_openapi3_spec(write_spec(SPEC_30))


def test_fast_validator_waits_while_response_validation_is_off(
    write_spec: t.Callable[..., str],
) -> None:
    """Response validation is switched per request, so the choice is not."""
    settings = {**FAST, "pyramid_openapi3.enable_response_validation": "false"}
    with testing.testConfig(settings=settings) as config:
        config.include("pyramid_openapi3")
        config.pyramid_openapi3_spec(write_spec(spec_for("{type: string}")))
        config.add_route("x", "/x")
        config.add_view(lambda *_: {}, route_name="x", renderer="json", openapi=True)
        assert call(config, "/x")[0] == "200 OK"
        config.registry.settings["pyramid_openapi3.enable_response_validation"] = True
        status, body = call(config, "/x")
    assert status == "500 Internal Server Error"
    assert errors(body) == [
        {"exception": "FastValidationError", "message": '{} is not of type "string"'}
    ]


def test_missing_jsonschema_rs_is_refused(
    write_spec: t.Callable[..., str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """Turning the setting on without the extra installed says what to install."""
    monkeypatch.delitem(sys.modules, "pyramid_openapi3.fast", raising=False)
    monkeypatch.setitem(sys.modules, "jsonschema_rs", None)
    settings = {"pyramid_openapi3.fast_response_validation": "true"}
    with testing.testConfig(settings=settings) as config:
        config.include("pyramid_openapi3")
        with pytest.raises(
            ConfigurationError, match=r"install pyramid_openapi3\[fast\]"
        ):
            config.pyramid_openapi3_spec(write_spec(SPEC))


def test_other_import_errors_are_not_about_the_extra(
    write_spec: t.Callable[..., str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """A dependency that moved is reported as itself, not as a missing extra."""
    monkeypatch.delitem(sys.modules, "pyramid_openapi3.fast", raising=False)
    monkeypatch.setitem(
        sys.modules, "openapi_core.templating.media_types.exceptions", None
    )
    with testing.testConfig(settings=FAST) as config:
        config.include("pyramid_openapi3")
        with pytest.raises(ImportError, match=r"openapi_core\.templating"):
            config.pyramid_openapi3_spec(write_spec(SPEC))


def test_split_spec_resolves_references(write_spec: t.Callable[..., str]) -> None:
    """A spec directory's cross-file `$ref`s resolve against the root file."""
    root = b"""
openapi: '3.1.0'
info:
  version: '1.0.0'
  title: Foo API
paths:
  /items/{id}:
    $ref: 'paths.yaml#/item'
components:
  schemas:
    Item:
      $ref: 'schemas.yaml#/Item'
"""
    paths = b"""
item:
  get:
    parameters:
      - name: id
        in: path
        required: true
        schema:
          type: string
    responses:
      '200':
        description: An item
        content:
          application/json:
            schema:
              $ref: 'schemas.yaml#/Item'
"""
    schemas = b"""
Item:
  type: object
  required:
    - id
  properties:
    id:
      type: string
"""
    settings = {"pyramid_openapi3.fast_response_validation": "true"}
    with testing.testConfig(settings=settings) as config:
        config.include("pyramid_openapi3")
        write_spec(paths, "split/paths.yaml")
        write_spec(schemas, "split/schemas.yaml")
        config.pyramid_openapi3_spec_directory(write_spec(root, "split/openapi.yaml"))
        config.add_route("item", "/items/{id}")
        add_item_view(config, {"id": 5})
        status, body = call(config, "/items/1")
        assert status == "500 Internal Server Error"
        assert errors(body) == [
            {
                "exception": "FastValidationError",
                "message": '5 is not of type "string"',
                "field": "id",
            }
        ]


@pytest.mark.parametrize(
    "ref",
    [
        "schemas.yaml#/a~1b",
        "schemas.yaml#/My%20Item",
        "schemas.yaml#/Größe",
        "item.yaml#",
    ],
)
def test_split_spec_names_every_target(
    write_spec: t.Callable[..., str], ref: str
) -> None:
    """A target whose pointer or file name is no `$defs` key still resolves."""
    write_spec(
        "'a/b': {type: object}\n'My Item': {type: object}\n"
        "Größe: {type: object}".encode(),
        "split/schemas.yaml",
    )
    write_spec(b"{type: object}", "split/item.yaml")
    with testing.testConfig(settings=FAST) as config:
        config.include("pyramid_openapi3")
        config.pyramid_openapi3_spec_directory(
            write_spec(spec_for(f"{{$ref: '{ref}'}}"), "split/openapi.yaml")
        )
        status, body = serve(config, b"[]")
    assert status == "500 Internal Server Error"
    assert errors(body) == [
        {"exception": "FastValidationError", "message": '[] is not of type "object"'}
    ]


def test_split_spec_reads_each_file_once(
    write_spec: t.Callable[..., str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """Sibling references into one file read it once, each keeping its target."""
    schema = (
        "{type: object, properties: "
        "{a: {$ref: 'schemas.yaml#/A'}, b: {$ref: 'schemas.yaml#/B'}}}"
    )
    write_spec(b"A: {const: 1}\nB: {const: 2}", "split/schemas.yaml")
    path = Path(write_spec(spec_for(schema), "split/openapi.yaml"))
    spec = SchemaPath.from_dict(
        yaml.safe_load(path.read_bytes()), base_uri=path.as_uri()
    )
    reads: list[str] = []
    retrieve = SchemaRetriever.__call__
    monkeypatch.setattr(
        SchemaRetriever,
        "__call__",
        lambda self, uri: (reads.append(uri), retrieve(self, uri))[1],
    )
    [validator] = FastResponseValidator(spec).validators.values()
    assert reads == [(path.parent / "schemas.yaml").as_uri()]
    assert [
        (error.message, list(error.instance_path))
        for error in validator.iter_errors({"a": 1, "b": 1})
    ] == [("2 was expected", ["b"])]


def test_external_file_with_an_id_is_followed(
    write_spec: t.Callable[..., str],
) -> None:
    """A file's `$id` is left behind, so its rewritten references stay local."""
    write_spec(
        b'{"$id": "https://example.com/item.json", "type": "object", '
        b'"properties": {"x": {"$ref": "#/$defs/x"}}, '
        b'"$defs": {"x": {"type": "integer"}}}',
        "split/item.json",
    )
    with testing.testConfig(settings=FAST) as config:
        config.include("pyramid_openapi3")
        config.pyramid_openapi3_spec_directory(
            write_spec(spec_for("{$ref: 'item.json'}"), "split/openapi.yaml")
        )
        status, body = serve(config, b'{"x": "a"}')
    assert status == "500 Internal Server Error"
    assert errors(body) == [
        {
            "exception": "FastValidationError",
            "message": '"a" is not of type "integer"',
            "field": "x",
        }
    ]


def test_dynamic_reference_is_refused() -> None:
    """A `$dynamicRef` binds at validation time, which one flat document cannot do."""
    spec = SchemaPath.from_dict(
        {"root": {"items": {"$dynamicRef": "#T"}}}, base_uri="file:///spec.yaml"
    )
    with pytest.raises(ConfigurationError) as info:
        FastResponseValidator(spec).dereference(spec / "root")
    assert str(info.value) == (
        "`$dynamicRef` in file:///spec.yaml is not supported by fast response "
        "validation: it copies every referenced schema into one document, "
        "where a dynamic scope cannot be kept."
    )


def test_wildcard_media_type_still_reads_json(write_spec: t.Callable[..., str]) -> None:
    """Under a `*/*` content entry, a JSON response is read as JSON."""
    with testing.testConfig(settings=FAST) as config:
        config.include("pyramid_openapi3")
        config.pyramid_openapi3_spec(
            write_spec(spec_for("{type: object, required: [id]}", media="*/*"))
        )
        status, body = serve(config, b"{}")
    assert status == "500 Internal Server Error"
    assert errors(body) == [
        {
            "exception": "FastValidationError",
            "message": '"id" is a required property',
            "field": "id",
        }
    ]


def test_media_type_without_schema_passes(write_spec: t.Callable[..., str]) -> None:
    """A content entry that declares no schema accepts any body."""
    spec = spec_for("{type: object}").replace(b"schema: {type: object}", b"{}")
    with testing.testConfig(settings=FAST) as config:
        config.include("pyramid_openapi3")
        config.pyramid_openapi3_spec(write_spec(spec))
        status, _ = serve(config, b"[]")
    assert status == "200 OK"


def test_registered_deserializer_reads_the_body(
    write_spec: t.Callable[..., str],
) -> None:
    """A deserializer added for a media type turns its bodies into data."""
    media = "application/backwards+json"
    with testing.testConfig(settings=FAST) as config:
        config.include("pyramid_openapi3")
        config.pyramid_openapi3_add_deserializer(
            media, lambda body: json.loads(body[::-1])
        )
        config.pyramid_openapi3_spec(
            write_spec(spec_for("{type: object, required: [id]}", media=media))
        )
        status, _ = serve(config, b'{"id": 1}'[::-1], content_type=media)
    assert status == "200 OK"


def test_body_a_deserializer_cannot_read_is_a_500(
    write_spec: t.Callable[..., str],
) -> None:
    """A deserializer's parse error is reported, as openapi-core reports it."""
    media = "application/xml"
    with testing.testConfig(settings=FAST) as config:
        config.include("pyramid_openapi3")
        config.pyramid_openapi3_add_deserializer(media, fromstring)
        config.pyramid_openapi3_spec(
            write_spec(spec_for("{type: object}", media=media))
        )
        status, body = serve(config, b"<a><b></a>", content_type=media)
    assert status == "500 Internal Server Error"
    assert errors(body) == [
        {
            "exception": "FastValidationError",
            "message": "Response body is not application/xml: "
            "mismatched tag: line 1, column 8",
        }
    ]


@pytest.mark.parametrize(
    ("body", "message"),
    [
        (b"when: 2026-11-10", "Unsupported type: 'date'"),
        (b"1: a", "Dict key must be str or str enum. Got 'int'"),
    ],
)
def test_deserialized_data_that_is_not_json_is_a_500(
    write_spec: t.Callable[..., str], body: bytes, message: str
) -> None:
    """What a deserializer returns beyond JSON's types is reported, not raised."""
    media = "application/yaml"
    with testing.testConfig(settings=FAST) as config:
        config.include("pyramid_openapi3")
        config.pyramid_openapi3_add_deserializer(media, yaml.safe_load)
        config.pyramid_openapi3_spec(
            write_spec(
                spec_for(
                    "{type: object, properties: {when: {type: string}}}", media=media
                )
            )
        )
        status, body = serve(config, body, content_type=media)
    assert status == "500 Internal Server Error"
    assert errors(body) == [
        {
            "exception": "FastValidationError",
            "message": f"Response body is not JSON data: {message}",
        }
    ]


@pytest.mark.parametrize(
    ("schema", "body", "message"),
    [
        (
            "{type: integer, format: int32}",
            b"2147483648",
            "2147483648 is greater than or equal to the maximum of 2147483648",
        ),
        (
            "{type: integer, format: int64, exclusiveMinimum: 0}",
            b"-1",
            "-1 is less than or equal to the minimum of 0",
        ),
        (
            "{type: string, format: byte}",
            b'"not base64!!"',
            '"not base64!!" is not a "byte"',
        ),
    ],
)
def test_openapi_formats_are_checked(
    write_spec: t.Callable[..., str], schema: str, body: bytes, message: str
) -> None:
    """The formats openapi-core checks beyond JSON Schema's are checked here too."""
    with testing.testConfig(settings=FAST) as config:
        config.include("pyramid_openapi3")
        config.pyramid_openapi3_spec(write_spec(spec_for(schema)))
        status, response = serve(config, body)
    assert status == "500 Internal Server Error"
    assert errors(response) == [
        {"exception": "FastValidationError", "message": message}
    ]
