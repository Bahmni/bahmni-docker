#!/bin/bash

function log_error() {
    local message=$1
    echo -e "\033[31mERROR - ${message}\033[0m"
}

function log_warning() {
    local message=$1
    echo -e "\033[33mWARN - ${message}\033[0m"
}

function log_info() {
    local message=$1
    echo "INFO - ${message}"
}

function is_compose_container_running() {
    local service_name=$1
    if [ -z $(docker compose ps -q $service_name) ] || [ -z $(docker ps -q --no-trunc | grep $(docker compose ps -q $service_name)) ]; then
        echo 0
    else
        echo 1
    fi
}

function is_compose_container_present() {
    local service_name=$1
    if [ -z $(docker compose ps -a -q $service_name) ]; then
        echo 0
    else
        echo 1
    fi
}

function backup_db() {
    local db_type=$1
    local db_name=$2
    local db_username=$3
    local db_password=$4
    local db_service_name=$5
    local backup_file_path=$6
    if [[ $(is_compose_container_running $db_service_name) -eq 1 ]]; then
        if [[ $db_type == "mysql" ]]; then
            docker compose --env-file ${BAHMNI_DOCKER_ENV_FILE} exec $db_service_name mysqldump -u $db_username --password=$db_password --routines $db_name --no-tablespaces >"$backup_file_path"
        elif [[ $db_type == "postgres" ]]; then
            docker compose --env-file ${BAHMNI_DOCKER_ENV_FILE} exec $db_service_name pg_dump -U $db_username -d $db_name -F p -b -v >"$backup_file_path"
        fi
    else
        log_error "Unable to backup for $db_name database as $db_service_name container is not running"
    fi

}

function backup_container_file_system() {
    local service_name=$1
    local container_file_path=$2
    local backup_file_path=$3
    if [[ $(is_compose_container_present $service_name) -eq 1 ]]; then
        docker compose cp -a "$service_name:$container_file_path" "$backup_file_path"
    else
        log_error "Unable to backup for $container_file_path files as $service_name container is not created"
    fi
}
