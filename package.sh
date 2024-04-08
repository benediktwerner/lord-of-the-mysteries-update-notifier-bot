#!/bin/sh

if [ "$1" = "dep" ]; then
    zip -r dependencies-layer.zip python
fi
zip deployment.zip lambda_function.py
