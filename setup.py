#!/usr/bin/env python3

from setuptools import setup

with open("README.md") as readme_fp:
    long_description = readme_fp.read()

setup(name="mockdock",
    version="0.8.1",
    package_dir={"": "src"},
    packages=["mockdock"],
    description="mockdock is a dns resolver and http server usable for testing containers",
    long_description=long_description,
    long_description_content_type="text/markdown",
    license="MIT",
    url="https://github.com/jensstein/mockdock",
    provides=["mockdock"],
    entry_points={
        "console_scripts": [
            "server = mockdock.server:main"
        ]
    },
    install_requires=[
        "conu"
    ],
    extras_require={
        "dev": [
            "mypy"
        ]
    }
)
