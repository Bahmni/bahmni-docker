#!/bin/sh

case $@ in
    setup)
        docker run -d -p 443:443 -p 8050:8050 -p 8069:8069 -p 8052:8052 --name bahmni jaswanth/bahmni
        ;;
    setup-dev)
        docker run -d -p 443:443 -p 3306:3306 -p 5432:5432 -p 8050:8050 -p 8069:8069 -p 8052:8052 \
        --name bahmni -v ~/bahmni-code:/bahmni-code:ro jaswanth/bahmni
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
    delete)
        docker rm -f bahmni
        ;;
    shell)
        docker exec -it bahmni bash
        ;;
    link)
        docker exec -it bahmni /bahmni-code/openmrs-module-bahmniapps/scripts/docker-link.sh
        docker exec -it bahmni /bahmni-code/bahmni-core/scripts/docker-link.sh
        docker exec -it bahmni /bahmni-code/default-config/scripts/docker-link.sh
        ;;
    update)
        docker pull jaswanth/bahmni
        ;;
    *)
        echo "Invalid option";
        echo "Available options : setup, setup-dev, start, status, stop, delete, shell, link, update";
        ;;
esac
