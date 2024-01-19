#!/usr/bin/bash

PROJ_DIR=$(dirname "$0")
ZIPFILE="deploy.zip"
FUNCTIONID=aims-roster-data-extraction

cd $PROJ_DIR
source venv/bin/activate
mkdir package
pip install --target package .
cd package
zip -r ../$ZIPFILE .
cd ..
zip $ZIPFILE lambda_function.py
aws lambda update-function-code \
    --region "eu-west-2" \
    --function-name  "$FUNCTIONID" \
    --zip-file "fileb://${PROJ_DIR}/${ZIPFILE}"
rm -r package
rm $ZIPFILE
