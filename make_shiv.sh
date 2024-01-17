#!/bin/bash

PROJ=/home/jon/proj/aims

cd $PROJ
python3 -m venv venv-shiv
source venv-shiv/bin/activate
pip install shiv
pip install wheel
shiv -c aimsgui -o aimsgui.pyw -p "/usr/bin/env python3" $PROJ
deactivate
rm -r venv-shiv
