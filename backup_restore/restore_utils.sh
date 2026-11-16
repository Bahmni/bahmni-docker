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

RESTORE_SKIPPED=()

function start_container() {
    local service_name=$1
    log_info "Starting $service_name Container"
    docker compose --env-file ${BAHMNI_DOCKER_ENV_FILE} up -d $service_name
}

# Polls over TCP so the temporary server the official mysql/postgres entrypoints
# run during first-time init (socket only, networking off) is not mistaken for ready.
function wait_for_db() {
    local db_type=$1
    local db_username=$2
    local db_password=$3
    local db_service_name=$4
    local timeout_seconds=${DB_READY_TIMEOUT_SECONDS:-600}
    local waited=0

    log_info "Waiting for $db_service_name to accept connections (timeout ${timeout_seconds}s)"
    while true; do
        if [[ $db_type == "mysql" ]]; then
            docker compose --env-file ${BAHMNI_DOCKER_ENV_FILE} exec -T $db_service_name mysql -h 127.0.0.1 --protocol=TCP -u $db_username --password=$db_password -e "SELECT 1" >/dev/null 2>&1 && return 0
        elif [[ $db_type == "postgres" ]]; then
            docker compose --env-file ${BAHMNI_DOCKER_ENV_FILE} exec -T $db_service_name pg_isready -h 127.0.0.1 -U $db_username >/dev/null 2>&1 && return 0
        fi
        if [ $waited -ge $timeout_seconds ]; then
            log_error "$db_service_name did not become ready within ${timeout_seconds}s"
            return 1
        fi
        sleep 5
        waited=$((waited + 5))
    done
}

function print_restore_summary() {
    if [ ${#RESTORE_SKIPPED[@]} -gt 0 ]; then
        log_error "Restore incomplete. Skipped: ${RESTORE_SKIPPED[*]}"
        log_error "Targets that already hold data are never overwritten: reset them first (run-bahmni.sh option 8) and re-run the restore."
        return 1
    fi
    log_info "Restore completed."
}

# Restored files are copied as root; hand them back to the user the service runs as.
function fix_volume_owner() {
    local service_name=$1
    local path=$2
    local owner=$3
    log_info "Setting owner of $path in $service_name to $owner"
    docker compose --env-file ${BAHMNI_DOCKER_ENV_FILE} run --rm --no-deps -T -u root --entrypoint chown $service_name -R $owner $path \
        || log_warning "Could not set owner of $path in $service_name; fix it manually if the service cannot write there."
}

function restore_volumes() {
    log_info "Starting File System Restore..."
    if ! docker compose --env-file ${BAHMNI_DOCKER_ENV_FILE} run --rm restore_volumes; then
        RESTORE_SKIPPED+=("file-system volumes (see log above)")
    fi
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
        if ! wait_for_db $db_type $db_username $db_password $db_service_name; then
            RESTORE_SKIPPED+=("$db_name (database not ready)")
            return
        fi
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
            RESTORE_SKIPPED+=("$db_name")
        fi
    else
        log_warning "DB backup file for $db_name not found at ${db_backup_file_path}. Skipping restore"
    fi
}
