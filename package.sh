#!/bin/sh
cd dependencies
zip -r ../deployment.zip .
cd ..
zip deployment.zip lambda_function.py
