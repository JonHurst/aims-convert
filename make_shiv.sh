#!/bin/bash

PROJ=/home/jon/proj/aims
python -m venv venv
source venv/bin/activate
pip install $PROJ
shiv -c aimsgui -o aimsgui.pyw -p "/usr/bin/env python3" $PROJ
deactivate
rm -r venv
