## Changelog

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
