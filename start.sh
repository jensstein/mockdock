#!/bin/sh

set -xe

source ENV/bin/activate
./src/mockdock/server.py
