#!/usr/bin/make -f

USER    ?= alexa
HOME    ?= /srv/alexa
SHELL	= /bin/bash

install:
	install -m 700 -o $(USER) -d $(HOME)/data
	#install -m 755 -o root src/manage.py $(HOME)
	python3 -m venv --without-pip $(HOME)/venv # without pip due to pyvenv bug: [1]
	(source $(HOME)/venv/bin/activate; \
	curl https://bootstrap.pypa.io/get-pip.py | python3; \
	pip3 install -r ./requirements.txt)
	cp -r src/alexacloud $(HOME)
	chown -R $(USER):root $(HOME)/alexacloud
	install -m 644 -o root ./webserver/uwsgi/alexa.ini /etc/uwsgi/apps-enabled/
	install -m 644 -o root ./webserver/nginx/alexa     /etc/nginx/sites-enabled/
	# Set up cronjob to delete old files
	(crontab -l 2>/dev/null; echo "*/30 * * * * $(HOME)/venv/bin/python $(HOME)/alexacloud/clean.py") | crontab -
	

# [1] http://stackoverflow.com/questions/26215790/venv-doesnt-create-activate-script-python3
