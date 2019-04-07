"""A setuptools based setup module.

See:
https://packaging.python.org/en/latest/distributing.html
https://github.com/pypa/sampleproject
"""

from setuptools import setup, find_packages
from os import path
from io import open

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()


version = '0.1.0'

setup(
    name='pyramid_openapi3',
    version=version,
    description='Pyramid addon for OpenAPI3 validation',
    long_description=long_description,
    license='MIT',
    long_description_content_type='text/markdown',
    url='https://github.com/niteoweb/pyramid_openapi3',
    author='Niteo Gmbh',
    author_email='info@niteo.co',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Framework :: Pyramid',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ],
    keywords='pyramid openapi3 openapi rest restful',
    packages=find_packages(exclude=['tests']),
    package_data={
        'pyramid_openapi3': ['static/*.*'],
        '': ['LICENSE'],
    },
    install_requires=[
      'openapi-core',
      'openapi-spec-validator',
      'pyramid',
     ],
    setup_requires=["pytest-runner"],
    extras_require={
        'dev': ['coverage', 'pytest', 'tox'],
        'lint': ['black'],
    }
)
