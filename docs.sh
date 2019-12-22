#!/bin/sh

sphinx-apidoc -f  -o ./docs .
cd docs
make html
