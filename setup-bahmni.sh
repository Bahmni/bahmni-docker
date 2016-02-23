#!/bin/sh

docker run -d -p 127.0.0.1:443:443 -p 127.0.0.1:3306:3306 -p 127.0.0.1:5432:5432 -p 127.0.0.1:8080:8080 -p 127.0.0.1:8069:8069 -p 127.0.0.1:8081:8081 -p 127.0.0.1:8000:8000 --name bahmni-rpm \
-v ~/bahmni-code:/bahmni-code:ro jaswanth/bahmni-docker
