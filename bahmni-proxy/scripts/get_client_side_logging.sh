#!/bin/bash
set -xe

CLIENT_SIDE_LOGGING_PATH=/usr/local/apache2/htdocs/client_side_logging
CLIENT_SIDE_LOGGING_URL=https://raw.githubusercontent.com/Bahmni/client_side_logging/master
mkdir ${CLIENT_SIDE_LOGGING_PATH}

curl -o ${CLIENT_SIDE_LOGGING_PATH}/RotatingLogger.py ${CLIENT_SIDE_LOGGING_URL}/RotatingLogger.py
curl -o ${CLIENT_SIDE_LOGGING_PATH}/__init__.py ${CLIENT_SIDE_LOGGING_URL}/__init__.py
curl -o ${CLIENT_SIDE_LOGGING_PATH}/client_side_logging.py ${CLIENT_SIDE_LOGGING_URL}/client_side_logging.py
curl -o ${CLIENT_SIDE_LOGGING_PATH}/client_side_logging.wsgi ${CLIENT_SIDE_LOGGING_URL}/client_side_logging.wsgi
curl -o ${CLIENT_SIDE_LOGGING_PATH}/logging.yml ${CLIENT_SIDE_LOGGING_URL}/logging.yml
