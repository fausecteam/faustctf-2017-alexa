#!/usr/bin/env bash


## mysql setup ##
mysql -u root < setup.sql

## venv setup ##
python3 -m venv --without-pip .alexavenv
source .alexavenv/bin/activate
curl https://bootstrap.pypa.io/get-pip.py | python
deactivate
source .alexavenv/bin/activate

pip install -r requirements.txt

python manage.py migrate
