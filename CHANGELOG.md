## Changelog

For future releases, see <https://github.com/Pylons/pyramid_openapi3/releases>

---

0.17.1 (2024-03-11)
-------------------

* Fix `multipart/form-data` support, refs #225.
  [am-on]


0.17.0 (2024-03-08)
-------------------

* Update the supported version of Python to 3.12, Pyramid to 2.0.2.
  Drop support for Python 3.8.
  [zupo]

* Update the supported version of `openapi-core` to 0.19.0, refs #220.
  Drop support for all older versions of `openapi-core`.
  [miketheman, Wim-De-Clercq, zupo]

* Update Swagger UI version to 4.18.3, refs #210.
  [kskarthik]

* Add support for specifying the protocol and port for getting the openapi3
  spec file, fixes running behind a reverse proxy, refs #176.
  [vpet98, zupo]


0.16.0 (2023-03-22)
-------------------

* Add support for setting a prefix for auto-generated routes.
  [zupo]


0.15.0 (2022-12-11)
-------------------

* Update Swagger UI version to 4.15.3, refs #185.
  [kskarthik]

* Upgrade `openapi-core dependency` to `0.16`, refs #173.

  [BREAKING CHANGE] `request.openapi_validated.parameters` will now be
  a dataclass instead of a dict. For example: if you wanted to get a
  query parameter called `limit`:
   * before: `request.openapi_validated.parameters["query"]["limit"]`
   * after: `request.openapi_validated.parameters.query["limit"]`
  [damonhook]


0.14.3 (2022-11-29)
-------------------

* `request.openapi_validated` no longer breaks non-opeanpi views, refs #172.
  [grinspins, zupo]


0.14.2 (2022-11-17)
-------------------

* Remove openapi-schema-validator as a dependency, as it is already pulled in
  by openapi-core.
  [zupo]


0.14.1 (2022-11-17)
-------------------

* Cleanup and modernization of dev env, added support for Python 3.10 and 3.11.
  [zupo]


0.14 (2022-05-05)
-----------------

* Upgrade Swagger UI to latest version to get security fixes missing in
  the old release.
  [am-on]


0.13 (2021-06-13)
-----------------

* Add support for Pyramid 2.0 refs #133, #142.
  [lkuchenb, zupo]


0.12 (2021-06-07)
-----------------

* Basic support for multipart requests, refs #122.
  [Wim-De-Clercq]

* Automatic route registration via `x-pyramid-route-name` extension, refs #46.
  [gjo]

* Support for Python 3.9, refs #115.
  [stevepiercy, zupo]

* Cleanup old relative OpenAPI server URL workaround. Drop support for
  `openapi-core 0.13.1`, refs #127, #129, #131.
  [sevanteri, zupo]

* Fix `KeyError` when having multiple routes for a single path, refs #118.
  [damonhook]


0.11 (2021-02-15)
-----------------

* Allow setting permission for explorer and spec view.
  [sweh]

* Allow multiple OpenApis in one pyramid application.
  [sweh]

* Fix for route validation when used with pyramid route_prefix_context.
  [damonhook]


0.10.2 (2020-10-27)
------------------

* Support for endpoint validation of prefixed routes.
  [zupo]


0.10.1 (2020-10-26)
------------------

* Support disabling of endpoint validation via INI files.
  [zupo]


0.10.0 (2020-10-26)
------------------

* Allow relative file `$ref` links in OpenApi spec, refs #93.
  [damonhook]

* Validate that all endpoints in the spec have a registered route, refs #21.
  [phrfpeixoto]


0.9.0 (2020-08-16)
------------------

* Add support for openapi-core 0.13.4.
  [sjiekak]

* Add the ability to toggle request/response validation independently through
  registry settings.
  [damonhook]


0.8.3 (2020-06-21)
------------------

* Brown-bag release.
  [zupo]


0.8.2 (2020-06-21)
------------------

* Raise a warning when a bad API spec causes validation errors to be discarded.
  [matthewwilkes]

* Fix `custom_formatters` support in latest openapi-core 0.13.3.
  [simondale00]

* Declare a minimal supported version of openapi-core.
  [zupo]


0.8.1 (2020-05-03)
------------------

* Fix extract_errors to support lists, refs #75.
  [zupo]


0.8.0 (2020-04-20)
------------------

* Log Response validation errors as errors, instead of warnings.
  [zupo]

* Log Request validation errors as warnings, instead of infos.
  [zupo]


0.7.0 (2020-04-03)
------------------

* Better support for handling apps mounted at subpaths.
  [mmerickel]

* Pass the response into the response validation exception to support use-cases
  where we can return the response but log the errors.
  [mmerickel]

* Reload development server also when YAML file changes.
  [mmerickel]


0.6.0 (2020-03-19)
------------------

* Better support for custom formatters and a test showcasing how to use them.
  [zupo]


0.5.2 (2020-03-16)
------------------

* Bad JWT tokens should result in 401 instead of 400.
  [zupo]


0.5.1 (2020-03-13)
------------------

* Fix a regression with relative `servers` entries in `openapi.yaml`.
  Refs https://github.com/p1c2u/openapi-core/issues/218.
  [zupo]


0.5.0 (2020-03-07)
------------------

* [BREAKING CHANGE] Move `openapi_validation_error` from `examples/todoapp`
  into the main package so it becomes a first-class citizen and people can use
  it without copy/pasting. If you need custom JSON rendering, you can provide
  your own `extract_errors` function via `pyramid_openapi3_extract_errors`
  config setting.
  [zupo]

* Upgrade `openapi-core` to `0.13.x` which brings a complete rewrite of the
  validation mechanism that is now based on `jsonschema` library. This
  manifests as different validation error messages.

  [BREAKING CHANGE] By default, `openapi-core` no longer creates models
  from validated data, but returns `dict`s. More info on
  https://github.com/p1c2u/openapi-core/issues/205
  [zupo]


0.4.1 (2019-10-22)
------------------

* Pin openapi-core dependency to a sub 0.12.0 version, to avoid
  regressions with validation. Details on
  https://github.com/p1c2u/openapi-core/issues/160
  [zupo]


0.4.0 (2019-08-05)
------------------

* Fix handling parameters in Headers and Cookies. [gweis]

* Introduce RequestValidationError and ResponseValidationError exceptions
  in favor of pyramid_openapi3_validation_error_view directive.
  [gweis]


0.3.0 (2019-05-22)
------------------

* Added type hints. [zupo]
* Added additional references to other packages covering the same problem-space. [zupo]
* Moved repo to Pylons GitHub organization. [stevepiercy, zupo]
* Added a more built-out TODO-app example. [zupo]


0.2.8 (2019-04-17)
------------------

* Fix for double-registering views. [zupo]
* Added a single-file example. [zupo]


0.2.7 (2019-04-14)
------------------

* Tweaking the release process. [zupo]


0.2.6 (2019-04-14)
------------------

* Added a bunch of tests. [zupo]


0.2.5 (2019-04-08)
------------------

* Automatic releases via CircleCI. [zupo]


0.1.0 (2019-04-08)
------------------

* Initial release. [zupo]
