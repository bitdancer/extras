import os
from setuptools import setup

here = os.path.abspath(os.path.dirname(__file__))

with open(os.path.join(here, 'README.rst')) as f:
    long_description = f.read()

setup(
    name='parameterizable_tests',
    version='0.5.0',
    description="unittest parameterization for stdlib tests",
    long_description=long_description,
    url='https://github.com/bitdancer/extras/parameterizable_tests',
    author='R. David Murray',
    author_email='rdmurray@bitdance.com',
    license='MIT',
    classifiers=[
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        ],
    keywords='testing',
    py_modules=['parameterizable_tests'],
    )
