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

function is_file_exists() {
    if [[ -f $1 ]]; then
        echo 1
    else
        echo 0
    fi
}

function is_directory_exists() {
  if [[ -d $1 ]]; then
    return 0
  else
    return 1
  fi
}

function is_directory_empty() {
  if [[ -z "$(ls -A $1)" ]]; then
    return 0
  else
    return 1
  fi
}

function is_mysql_db_empty() {
    local db_name=$1
    local db_username=$2
    local db_password=$3
    local db_service_name=$4

    local table_count=$(docker compose --env-file ${BAHMNI_DOCKER_ENV_FILE} exec $db_service_name mysql -N -s -u $db_username --password=$db_password $db_name -e "SELECT COUNT(DISTINCT table_name) FROM information_schema.columns WHERE table_schema = '${db_name}'")
    if [ $table_count -eq 0 ]; then
        echo 1
    else
        echo 0
    fi
}

function is_psql_db_empty() {
    local db_name=$1
    local db_username=$2
    local db_password=$3
    local db_service_name=$4
    local schema_name="public"

    if [ $db_service_name == "openelisdb" ]; then
        schema_name="clinlims"
    fi

    local table_count=$(docker compose --env-file ${BAHMNI_DOCKER_ENV_FILE} exec $db_service_name psql -U $db_username -d $db_name -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = '${schema_name}'")
    if [ $table_count -eq 0 ]; then
        echo 1
    else
        echo 0
    fi
}

function is_db_empty() {
    local db_type=$1
    local db_name=$2
    local db_username=$3
    local db_password=$4
    local db_service_name=$5

    if [[ $db_type == "mysql" ]]; then
        is_mysql_db_empty $db_name $db_username $db_password $db_service_name
    elif [[ $db_type == "postgres" ]]; then
        is_psql_db_empty $db_name $db_username $db_password $db_service_name
    fi
}

function run_sql(){
    local db_type=$1
    local db_name=$2
    local db_username=$3
    local db_password=$4
    local db_service_name=$5
    local sql_query=$6

    if [[ $db_type == "mysql" ]]; then
        docker compose --env-file ${BAHMNI_DOCKER_ENV_FILE} exec -T $db_service_name mysql -u $db_username --password=$db_password $db_name -e "$sql_query"
    elif [[ $db_type == "postgres" ]]; then
        docker compose --env-file ${BAHMNI_DOCKER_ENV_FILE} exec -T $db_service_name psql -U $db_username -d $db_name -c "$sql_query"
    fi
}

function start_container() {
    local service_name=$1
    log_info "Starting $service_name Container"
    docker compose --env-file ${BAHMNI_DOCKER_ENV_FILE} up -d $service_name
    log_info "Waiting for $service_name container to initialise"
    sleep 60
}

function restore_db() {
    local db_type=$1
    local db_name=$2
    local db_username=$3
    local db_password=$4
    local db_service_name=$5
    local db_backup_file_path=$6

    log_info "Initializing ${db_type} Restore for database: $db_name"
    if [[ $(is_file_exists ${db_backup_file_path}) -eq 1 ]]; then
        start_container $db_service_name
        if [[ $(is_db_empty $db_type $db_name $db_username $db_password $db_service_name) -eq 1 ]]; then

            if [[ $db_type == "mysql" ]]; then
                log_info "Starting MySQL Restore for database: $db_name"
                docker compose --env-file ${BAHMNI_DOCKER_ENV_FILE} exec -T $db_service_name mysql -u $db_username --password=$db_password $db_name < $db_backup_file_path
            elif [[ $db_type == "postgres" ]]; then
                log_info "Starting Postgres Restore for database: $db_name"
                docker compose --env-file ${BAHMNI_DOCKER_ENV_FILE} exec -T $db_service_name psql -U $db_username -d $db_name -q -f - < $db_backup_file_path
            fi

        else
            log_error "Database $db_name is not empty. Skipping restore"
        fi
    else
        log_warning "DB backup file for $db_name not found at ${db_backup_file_path}. Skipping restore"
    fi
}
