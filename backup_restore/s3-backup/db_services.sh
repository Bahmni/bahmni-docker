#!/bin/bash
# Helpers shared by s3_backup.sh and s3_restore.sh (sourced; run from BAHMNI_COMPOSE_DIR, callers define log_info/log_error).
#
# A database whose service is not running (e.g. reportsdb when "reports" is not in COMPOSE_PROFILES, but which holds
# restored data) is started temporarily so it is still backed up / restored, then stopped again.

BAHMNI_DOCKER_ENV_FILE="${BAHMNI_DOCKER_ENV_FILE:-.env}"

# Databases dumped by the backup script
BACKUP_DB_SERVICES="openmrsdb reportsdb openelisdb odoodb odoo-10-db pacsdb"

# backup folder -> volume mount inside this container (same mapping as restore_docker_volumes.sh)
FILE_MAPPINGS="patient_images:/mounts/bahmni-patient-images
document_images:/mounts/bahmni-document-images
clinical_forms:/mounts/bahmni-clinical-forms
configuration_checksums:/mounts/configuration_checksums
uploaded_results:/mounts/bahmni-lab-results
reports:/mounts/bahmni-queued-reports
uploaded-files:/mounts/bahmni-uploaded-files
dcm4chee_archive:/mounts/dcm4chee-archive"

STARTED_DB_SERVICES=""

function compose() { docker compose --env-file "$BAHMNI_DOCKER_ENV_FILE" "$@"; }

function is_service_running() {
    compose ps --status running --services 2>/dev/null | grep -qx "$1"
}

function db_container_exists() {
    [ -n "$(compose ps -a -q "$1" 2>/dev/null)" ]
}

# Starts a database service and waits until it accepts TCP connections (the temporary server MySQL/Postgres run
# while initialising a new data directory only listen on the socket, so a socket ping would succeed too early)
function start_db_service() {
    local service=$1 waited=0
    is_service_running "$service" && return 0
    log_info "$service is not running; starting it temporarily"
    compose up -d --no-deps --quiet-pull "$service" || return 1
    STARTED_DB_SERVICES+="$service "
    until compose exec -T "$service" sh -c 'if command -v mysqladmin >/dev/null; then
            mysqladmin ping -h 127.0.0.1 -u root --password="$MYSQL_ROOT_PASSWORD" --silent
        else
            pg_isready -q -h 127.0.0.1
        fi' >/dev/null 2>&1; do
        [ $waited -ge 300 ] && { log_error "$service did not become ready within 300s"; return 1; }
        sleep 5
        waited=$((waited + 5))
    done
}

# Starts the backed-up databases that have a container but are stopped. Services never created on this install
# (profile never enabled) are left alone.
function start_stopped_db_services() {
    local service
    for service in $BACKUP_DB_SERVICES; do
        is_service_running "$service" && continue
        db_container_exists "$service" || continue
        start_db_service "$service" || log_error "Could not start $service; its database will not be backed up"
    done
}

function stop_started_db_services() {
    if [ -n "$STARTED_DB_SERVICES" ]; then
        log_info "Stopping database services started temporarily: $STARTED_DB_SERVICES"
        compose stop $STARTED_DB_SERVICES
        STARTED_DB_SERVICES=""
    fi
}

# The backup script copies files out of the app containers. When a container does not exist (e.g. "reports" is not
# enabled) but its volume holds files (e.g. from a restore), copy them from this container's mount instead.
function backup_files_from_mounts() {
    local backup_dir=$1 mapping name src
    while IFS= read -r mapping; do
        name="${mapping%%:*}"
        src="${mapping#*:}"
        [ -e "$backup_dir/$name" ] && continue
        [ -d "$src" ] && [ -n "$(ls -A "$src")" ] || continue
        log_info "Taking backup for $name from its volume (container not present)"
        mkdir -p "$backup_dir/$name" && cp -a "$src"/. "$backup_dir/$name"/ || return 1
    done <<<"$FILE_MAPPINGS"
}
