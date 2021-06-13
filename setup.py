"""A setuptools based setup module.

See:
https://packaging.python.org/en/latest/distributing.html
https://github.com/pypa/sampleproject
"""

from io import open
from setuptools import find_packages
from setuptools import setup
from setuptools.command.install import install

import os
import sys

here = os.path.abspath(os.path.dirname(__file__))

# Get the long description from the README file
with open(os.path.join(here, "README.md"), encoding="utf-8") as f:
    long_description = f.read()

with open(os.path.join(here, "CHANGELOG.md"), encoding="utf-8") as f:
    long_description += "\n\n" + f.read()


VERSION = "0.13"


class VerifyVersionCommand(install):
    """Custom command to verify that the git tag matches our version.

    Taken from https://circleci.com/blog/continuously-deploying-python-packages-to-pypi-with-circleci/
    """

    description = "verify that the git tag matches our version"

    def run(self):  # noqa: D102
        tag = os.getenv("CIRCLE_TAG")

        if tag != VERSION:
            info = "Git tag: {0} does not match the version of this app: {1}".format(
                tag, VERSION
            )
            sys.exit(info)


setup(
    name="pyramid_openapi3",
    version=VERSION,
    description="Pyramid addon for OpenAPI3 validation",
    long_description=long_description,
    license="MIT",
    long_description_content_type="text/markdown",
    url="https://github.com/Pylons/pyramid_openapi3",
    author="niteo.co",
    author_email="info@niteo.co",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Framework :: Pyramid",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
    ],
    keywords="pyramid openapi3 openapi rest restful",
    packages=find_packages(exclude=["tests"]),
    include_package_data=True,
    install_requires=[
        "openapi-core>=0.13.4,<0.14",
        "openapi-spec-validator",
        "pyramid>=1.10.7",
    ],
    cmdclass={"verify": VerifyVersionCommand},
)
