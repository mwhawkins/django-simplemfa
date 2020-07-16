import setuptools
from setuptools import setup

from os import path
this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(name="django-simplemfa",
    version="0.1",
    author="Michael Hawkins",
    author_email="mhawkins@netizen.net",
    description="An implementation of basic multi-factor authentication (MFA) for django projects",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/mwhawkins/django-simplemfa",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',)
