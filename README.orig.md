### Alexa service

# Requirements
* Python3 environment with Django
* Nginx web server

```
# Create virtual environment
$ virtualenv -p python3 alexa-venv
# Activate environment
$ source alexa-venv/bin/activate
# Install packages
$ pip install -r requirements.txt
# To leave virtual environment later
$ deactivate
```

# How to run the server
* For testing only: Inside the virtual environment run
`(alexa-venv)$ python manage.py runserver 80`
* In production: Have a look at the files in the webserver directory.

