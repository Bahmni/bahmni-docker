#!/bin/sh

docker run -d -p 443:443 -p 8080:8080 -p 8069:8069 -p 8081:8081 -p 8000:8000 --name bahmni-rpm \
-v ~/bahmni-code:/bahmni-code:ro jaswanth/bahmni-docker