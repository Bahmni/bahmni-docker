#!/bin/sh

case $@ in
    init)
        docker run -d -p 443:443 -p 8080:8080 -p 8069:8069 -p 8081:8081 --name bahmni jaswanth/bahmni-docker
        ;;
    init-dev)
        docker run -d -p 127.0.0.1:443:443 -p 127.0.0.1:3306:3306 -p 127.0.0.1:5432:5432 -p 127.0.0.1:8080:8080 -p 127.0.0.1:8069:8069 -p 127.0.0.1:8081:8081 -p 127.0.0.1:8000:8000 \
        --name bahmni -v ~/bahmni-code:/bahmni-code:ro jaswanth/bahmni-docker
        ;;
    start)
        docker start bahmni
        ;;
    status)
        docker ps -f name=bahmni --format "{{.Names}} | {{.Status}}"
        ;;
    stop)
        docker stop bahmni
        ;;
    destroy)
        docker rm -f bahmni
        ;;
    *)
        echo "Invalid option";
        echo "Available options : init, init-dev, start, status, stop, destroy";
        ;;
esac