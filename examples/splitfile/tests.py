"""A couple of functional tests to showcase pyramid_openapi3 works with YAML spec split into multiple files."""

from unittest import mock
from webtest import TestApp

import app
import unittest


class TestHappyPath(unittest.TestCase):
    """A suite of tests that make "happy path" requests against the app."""

    def setUp(self) -> None:
        """Start up the app so that tests can send requests to it."""
        self.testapp = TestApp(app.app())

    def test_list_todos(self) -> None:
        """Root returns a list of TODOs."""
        res = self.testapp.get("/", status=200)
        self.assertEqual(
            res.json,
            [{"title": "Buy milk"}, {"title": "Buy eggs"}, {"title": "Make pankaces!"}],
        )

    def test_add_todo(self) -> None:
        """POSTing to root saves a TODO."""  # noqa: D403
        res = self.testapp.post_json("/", {"title": "Add marmalade"}, status=200)
        self.assertEqual(res.json, "Item added.")

        # clean up after the test by removing the "Add marmalade" item
        app.ITEMS.pop()


class TestBadRequests(TestHappyPath):
    """A suite of tests that showcase out-of-the-box handling of bad requests."""

    def test_empty_POST(self) -> None:
        """Get a nice validation error when sending an empty POST request."""
        res = self.testapp.post_json("/", {}, status=400)
        self.assertEqual(
            res.json,
            [
                {
                    "exception": "ValidationError",
                    "field": "title",
                    "message": "'title' is a required property",
                }
            ],
        )

    def test_title_too_long(self) -> None:
        """Get a nice validation error when title is too long."""
        res = self.testapp.post_json("/", {"title": "a" * 41}, status=400)
        self.assertEqual(
            res.json,
            [
                {
                    "exception": "ValidationError",
                    "field": "title",
                    "message": "'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa' is too long",
                }
            ],
        )


class TestBadResponses(TestHappyPath):
    """A suite of tests that showcase out-of-the-box handling of bad responses."""

    def test_bad_items(self) -> None:
        """Test bad output from view.

        If our view returns JSON that does not match openapi.yaml schema,
        then we should render a 500 error.
        """
        with mock.patch("app.ITEMS", ["foo", "bar"]):
            res = self.testapp.get("/", status=500)
        self.assertEqual(
            res.json,
            [
                {
                    "exception": "DataValidationError",
                    "message": "Failed to cast value to object type: foo",
                },
            ],
        )
