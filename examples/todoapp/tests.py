"""A couple of functional tests to showcase pyramid_openapi3 features."""

from webtest import TestApp

import app
import unittest


class TestHappyPath(unittest.TestCase):
    """A suite of tests that make "happy path" requests against the app."""

    def setUp(self):
        """Start up the app so that tests can send requests to it."""
        self.testapp = TestApp(app.app())

    def test_list_todos(self):
        """Root returns a list of TODOs."""
        res = self.testapp.get("/", status=200)
        self.assertEqual(
            res.json,
            [{"title": "Buy milk"}, {"title": "Buy eggs"}, {"title": "Make pankaces!"}],
        )

    def test_add_todo(self):
        """POSTing to root saves a TODO."""  # noqa: D403
        res = self.testapp.post_json("/", {"title": "Add marmalade"}, status=200)
        self.assertEqual(res.json, "Item added.")

        # clean up after the test by removing the "Add marmalade" item
        app.ITEMS.pop()


class TestBadRequests(TestHappyPath):
    """A suite of tests that showcase out-of-the-box handling of bad requests."""

    def test_empty_POST(self):
        """Get a nice validation error when sending an empty POST request."""
        res = self.testapp.post_json("/", {}, status=400)
        self.assertEqual(
            res.json,
            [
                {
                    "message": "Missing schema property: title",
                    "exception": "MissingSchemaProperty",
                    "field": "title",
                }
            ],
        )

    def test_title_too_long(self):
        """Get a nice validation error when title is too long."""
        res = self.testapp.post_json("/", {"title": "a" * 41}, status=400)
        self.assertEqual(
            res.json,
            [
                {
                    "message": "Invalid schema property title: Value is longer (41) than the maximum length of 40",
                    "exception": "InvalidSchemaProperty",
                    "field": "title",
                }
            ],
        )
