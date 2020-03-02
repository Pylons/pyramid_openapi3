## Changelog

0.5.0-beta.3 (2020-03-02)
-------------------------

* Move `openapi_validation_error` from `examples/todoapp` into the main
  package so it becomes a first-class citizen and people can use it without
  copy/pasting. If you need custom JSON rendering, you can provide
  your own `extract_error` function via `pyramid_openapi3_extract_error`
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
