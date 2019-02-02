#!/usr/bin/env python3

from setuptools import setup

setup(name="mockdock",
    version="0.1.0",
    package_dir={"": "src"},
    packages=["mockdock"],
    description="",
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
