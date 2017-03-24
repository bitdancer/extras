import os
from setuptools import setup

here = os.path.abspath(os.path.dirname(__file__))

with open(os.path.join(here, 'README.rst')) as f:
    long_description = f.read()

setup(
    name='aio_rest_server',
    version='0.5.0',
    description="Simple json REST server",
    long_description=long_description,
    classifiers=[
        'Programming Language :: Python :: 3.5',
        ],
    install_requires=['aiohttp<2'],
    py_modules=['aio_rest_server'],
    )
