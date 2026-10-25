#!/bin/bash
# Restores Bahmni from a backup made by s3_backup.sh (or backup_bahmni_standard.sh).
#
# Usage:
#   bahmni-restore list
#   bahmni-restore s3    [latest|<archive name>|s3://bucket/key] --yes [--no-safety-backup] [--dry-run]
#   bahmni-restore local [latest|<archive name or folder in the backup folder>] --yes [--no-safety-backup] [--dry-run]
#
# Unlike restore_bahmni_standard.sh (which only fills empty databases/volumes on a fresh install),
# this REPLACES the current MySQL databases and file volumes with the backup contents.
set -uo pipefail

# crond starts jobs with an empty environment: restore the one saved by entrypoint.sh
[ -z "${BAHMNI_COMPOSE_DIR:-}" ] && [ -f /etc/backup.env ] && source /etc/backup.env

BAHMNI_COMPOSE_DIR="${BAHMNI_COMPOSE_DIR:?BAHMNI_COMPOSE_DIR is required}"
BAHMNI_BACKUP_SCRIPT="${BAHMNI_BACKUP_SCRIPT:-./backup_bahmni_standard.sh}"
BACKUP_NAME_PREFIX="${BACKUP_NAME_PREFIX:-bahmni}"
BACKUP_ROOT_FOLDER="${BACKUP_ROOT_FOLDER:-/backups}"
BAHMNI_DOCKER_ENV_FILE=.env
WORK_DIR="${BACKUP_ROOT_FOLDER}/.restore-work"
SAFETY_DIR="${BACKUP_ROOT_FOLDER}/pre-restore"
SAFETY_KEEP=3

# Database services never stopped during a restore (they are the restore targets)
DB_SERVICES="openmrsdb reportsdb openelisdb odoodb odoo-10-db pacsdb metabasedb martdb"

# OpenMRS Initializer config (read-only) and the checksums it uses to decide which files are already loaded
INITIALIZER_CONFIG_DIR=/mounts/bahmni-config/masterdata/configuration
INITIALIZER_CHECKSUM_DIR=/mounts/configuration_checksums

function log_error() { echo -e "\033[31mERROR - $(date +'%F %T') - $1\033[0m" >&2; }
function log_warning() { echo -e "\033[33mWARN - $(date +'%F %T') - $1\033[0m"; }
function log_info() { echo "INFO - $(date +'%F %T') - $1"; }
function die() { log_error "$1"; exit 1; }

source /usr/local/bin/db_services.sh

function usage() {
    sed -n '4,7p' "$0" | sed 's/^# \{0,1\}//'
    exit 1
}

for var in AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY AWS_SESSION_TOKEN AWS_DEFAULT_REGION AWS_ENDPOINT_URL; do
    [ -z "${!var:-}" ] && unset "$var"
done
S3_PREFIX="${S3_PREFIX:-bahmni}"
S3_PREFIX="${S3_PREFIX%/}"

cd "$BAHMNI_COMPOSE_DIR"
source "$BAHMNI_DOCKER_ENV_FILE"

function require_s3() {
    [ -n "${S3_BUCKET:-}" ] || die "S3_BUCKET is not set. Configure the Backup & S3 Storage section in .env"
}

# --- Listing / selecting backups -------------------------------------------------------

function list_s3() {
    aws s3api list-objects-v2 --bucket "$S3_BUCKET" --prefix "${S3_PREFIX}/${BACKUP_NAME_PREFIX}_" \
        --query 'sort_by(Contents || `[]`, &LastModified)[].[LastModified, Size, Key]' --output text
}

# Local candidates: archives and extracted backup folders directly inside the backup folder
function list_local() {
    find "$BACKUP_ROOT_FOLDER" -mindepth 1 -maxdepth 1 \( -name '*.tar.gz' -o -type d \) \
        ! -name '.restore-work' ! -name 'pre-restore' -printf '%TY-%Tm-%Td %TH:%TM\t%f\n' | sort
}

function fetch_s3() {
    local selector=$1 key
    require_s3
    case "$selector" in
    latest)
        key=$(aws s3api list-objects-v2 --bucket "$S3_BUCKET" --prefix "${S3_PREFIX}/${BACKUP_NAME_PREFIX}_" \
            --query 'sort_by(Contents || `[]`, &LastModified)[-1].Key' --output text) || die "Could not list s3://${S3_BUCKET}/${S3_PREFIX}/"
        [ -z "$key" ] || [ "$key" == "None" ] && die "No backups found in s3://${S3_BUCKET}/${S3_PREFIX}/"
        ;;
    s3://*) key="${selector#s3://*/}"; S3_BUCKET="${selector#s3://}"; S3_BUCKET="${S3_BUCKET%%/*}" ;;
    */*) key="$selector" ;;
    *) key="${S3_PREFIX}/${selector}" ;;
    esac
    log_info "Downloading s3://${S3_BUCKET}/${key}"
    aws s3 cp "s3://${S3_BUCKET}/${key}" "$WORK_DIR/$(basename "$key")" --only-show-errors || die "Download failed"
    extract_archive "$WORK_DIR/$(basename "$key")"
}

function fetch_local() {
    local selector=$1 path
    if [ "$selector" == "latest" ]; then
        path=$(find "$BACKUP_ROOT_FOLDER" -mindepth 1 -maxdepth 1 \( -name '*.tar.gz' -o -type d \) \
            ! -name '.restore-work' ! -name 'pre-restore' -printf '%T@ %p\n' | sort -n | tail -n 1 | cut -d' ' -f2-)
        [ -n "$path" ] || die "No local backups found in the backup folder (BACKUP_LOCAL_PATH)"
    else
        path="${BACKUP_ROOT_FOLDER}/${selector#/backups/}"
        [ -e "$path" ] || die "Local backup '$selector' not found in the backup folder (BACKUP_LOCAL_PATH)"
    fi
    log_info "Using local backup $(basename "$path")"
    if [ -d "$path" ]; then
        RESTORE_DIR="$path"
    else
        extract_archive "$path"
    fi
}

function extract_archive() {
    local archive=$1
    log_info "Extracting $(basename "$archive")"
    mkdir -p "$WORK_DIR/extracted"
    nice -n 19 tar -C "$WORK_DIR/extracted" -xzf "$archive" || die "Failed to extract $archive"
    # Archives contain a single top-level <timestamp> folder
    RESTORE_DIR=$(find "$WORK_DIR/extracted" -mindepth 1 -maxdepth 1 -type d | head -n 1)
    [ -n "$RESTORE_DIR" ] || RESTORE_DIR="$WORK_DIR/extracted"
}

function verify_backup() {
    local dump="$RESTORE_DIR/openmrsdb_backup.sql"
    [ -s "$dump" ] || die "Backup has no OpenMRS database dump ($dump); refusing to restore"
    tail -n 1 "$dump" | grep -q "Dump completed" || die "OpenMRS dump in backup is incomplete; refusing to restore"
    log_info "Backup contents: $(cd "$RESTORE_DIR" && ls | tr '\n' ' ')"
}

# --- Safety snapshot ------------------------------------------------------------------

function safety_backup() {
    local ts=$(date +'%Y-%m-%d_%H-%M-%S')
    log_info "Taking a pre-restore safety backup of the current state"
    mkdir -p "$SAFETY_DIR"
    start_stopped_db_services
    BACKUP_ROOT_FOLDER="$SAFETY_DIR" BACKUP_TIMESTAMP="$ts" nice -n 19 bash "$BAHMNI_BACKUP_SCRIPT" >/dev/null
    backup_files_from_mounts "$SAFETY_DIR/$ts" || die "Safety backup failed to copy files; aborting restore"
    if ! tail -n 1 "$SAFETY_DIR/$ts/openmrsdb_backup.sql" 2>/dev/null | grep -q "Dump completed"; then
        rm -rf "${SAFETY_DIR:?}/$ts"
        die "Safety backup failed; aborting restore (use --no-safety-backup to skip)"
    fi
    nice -n 19 tar -C "$SAFETY_DIR" -czf "$SAFETY_DIR/pre-restore_${ts}.tar.gz" "$ts" && rm -rf "${SAFETY_DIR:?}/$ts"
    log_info "Safety backup saved as pre-restore/pre-restore_${ts}.tar.gz"
    ls -1t "$SAFETY_DIR"/pre-restore_*.tar.gz | tail -n +$((SAFETY_KEEP + 1)) | xargs -r rm -f
}

# --- Service handling -----------------------------------------------------------------

STOPPED_SERVICES=""

function stop_app_services() {
    local svc
    for svc in $(compose ps --status running --services); do
        [[ " $DB_SERVICES backup " == *" $svc "* ]] && continue
        STOPPED_SERVICES+="$svc "
    done
    if [ -n "$STOPPED_SERVICES" ]; then
        log_info "Stopping application services: $STOPPED_SERVICES"
        compose stop $STOPPED_SERVICES
    fi
}

function start_app_services() {
    if [ -n "$STOPPED_SERVICES" ]; then
        log_info "Starting application services: $STOPPED_SERVICES"
        compose start $STOPPED_SERVICES || log_error "Failed to restart some services; run 'docker compose up -d'"
        STOPPED_SERVICES=""
    fi
}

SKIPPED_ITEMS=""

function restore_mysql() {
    local db_name=$1 service=$2 dump=$3
    [ -s "$dump" ] || { log_info "No dump for $db_name in backup, skipping"; return 0; }
    # Started temporarily if not running, so its data is in place when the service is enabled later
    start_db_service "$service" || { log_error "Could not start $service"; return 1; }
    log_info "Restoring MySQL database $db_name (replacing current data)"
    compose exec -T "$service" mysql -u root --password="$MYSQL_ROOT_PASSWORD" \
        -e "DROP DATABASE IF EXISTS \`$db_name\`; CREATE DATABASE \`$db_name\`;" || return 1
    compose exec -T "$service" mysql -u root --password="$MYSQL_ROOT_PASSWORD" "$db_name" <"$dump" || return 1
    log_info "Restored $db_name"
}

# Postgres dumps are restored only into empty databases (same behaviour as restore_bahmni_standard.sh)
function restore_postgres() {
    local db_name=$1 db_user=$2 service=$3 dump=$4 schema=${5:-public} count
    [ -s "$dump" ] || return 0
    if ! is_service_running "$service"; then
        log_warning "$service is not running, skipping $db_name"
        SKIPPED_ITEMS+="$db_name "
        return 0
    fi
    count=$(compose exec -T "$service" psql -U "$db_user" -d "$db_name" -tA \
        -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = '${schema}'")
    if [ "${count:-1}" != "0" ]; then
        log_warning "Postgres database $db_name is not empty, skipping (only empty Postgres databases are restored)"
        SKIPPED_ITEMS+="$db_name "
        return 0
    fi
    log_info "Restoring Postgres database $db_name"
    compose exec -T "$service" psql -U "$db_user" -d "$db_name" -q -f - <"$dump"
}

function restore_files() {
    local mapping src dest
    while IFS= read -r mapping; do
        src="$RESTORE_DIR/${mapping%%:*}"
        dest="${mapping#*:}"
        [ -d "$src" ] || continue
        if [ ! -d "$dest" ]; then
            log_warning "Volume mount $dest missing, skipping ${mapping%%:*}"
            SKIPPED_ITEMS+="${mapping%%:*} "
            continue
        fi
        log_info "Restoring files ${mapping%%:*} -> $(basename "$dest")"
        find "$dest" -mindepth 1 -delete
        cp -a "$src"/. "$dest"/ || return 1
    done <<<"$FILE_MAPPINGS"
}

# The restored checksums describe the backed-up server's config. Files of this server's config without a matching
# checksum are loaded by the OpenMRS Initializer into the restored database on the next start (ocl/ alone imports
# the whole CIEL dictionary, blocking startup for 30+ minutes). Writing the current files' checksums for the domains
# in RESTORE_SKIP_INITIALIZER_DOMAINS marks them as already loaded. "all" skips every domain, empty skips none.
function skip_initializer_domains() {
    local domains=${RESTORE_SKIP_INITIALIZER_DOMAINS-ocl} domain file name count
    [ -n "$domains" ] || return 0
    if [ ! -d "$INITIALIZER_CONFIG_DIR" ]; then
        log_warning "Initializer config $INITIALIZER_CONFIG_DIR not mounted; not skipping domains: $domains"
        return 0
    fi
    [ "$domains" == "all" ] && domains=$(find "$INITIALIZER_CONFIG_DIR" -mindepth 1 -maxdepth 1 -type d -printf '%f\n')
    for domain in ${domains//,/ }; do
        [ -d "$INITIALIZER_CONFIG_DIR/$domain" ] || continue
        mkdir -p "$INITIALIZER_CHECKSUM_DIR/$domain" || return 1
        count=0
        for file in "$INITIALIZER_CONFIG_DIR/$domain"/*; do
            [ -f "$file" ] || continue
            name=$(basename "$file")
            # Same format as the Initializer: <domain>/<file name without extension>.checksum holding the MD5, no newline
            printf '%s' "$(md5sum <"$file" | cut -c1-32)" >"$INITIALIZER_CHECKSUM_DIR/$domain/${name%.*}.checksum" || return 1
            count=$((count + 1))
        done
        log_info "OpenMRS Initializer will skip '$domain' ($count file(s) marked as already loaded)"
    done
}

function cleanup() {
    stop_started_db_services
    start_app_services
    rm -rf "${WORK_DIR:?}"
}

# --- Main ---------------------------------------------------------------------------------

command=${1:-}
[ -n "$command" ] || usage
shift

if [ "$command" == "list" ]; then
    if [ -n "${S3_BUCKET:-}" ]; then
        echo "== S3: s3://${S3_BUCKET}/${S3_PREFIX}/"
        list_s3 || log_error "Could not list S3 backups"
    else
        echo "== S3: not configured (S3_BUCKET is empty)"
    fi
    echo "== Local: ${BACKUP_LOCAL_PATH:-./backup-artifacts}"
    list_local
    exit 0
fi

[[ "$command" == "s3" || "$command" == "local" ]] || usage
selector="latest"
confirmed=false
safety=true
dry_run=false
for arg in "$@"; do
    case "$arg" in
    --yes) confirmed=true ;;
    --no-safety-backup) safety=false ;;
    --dry-run) dry_run=true ;;
    -*) usage ;;
    *) selector="$arg" ;;
    esac
done

if ! $confirmed && ! $dry_run; then
    die "Restore REPLACES the current OpenMRS/Reports databases and patient files and stops Bahmni while it runs. Re-run with --yes to confirm (or --dry-run to only fetch and verify)."
fi

exec 9>/tmp/s3_backup.lock
flock -n 9 || die "A backup or restore is already running"

trap cleanup EXIT
trap 'exit 130' INT TERM
rm -rf "${WORK_DIR:?}" && mkdir -p "$WORK_DIR"
RESTORE_DIR=""

if [ "$command" == "s3" ]; then fetch_s3 "$selector"; else fetch_local "$selector"; fi
verify_backup

if $dry_run; then
    log_info "Dry run: backup fetched and verified, nothing was changed"
    exit 0
fi

$safety && safety_backup

stop_app_services
failed=0
restore_mysql "$OPENMRS_DB_NAME" openmrsdb "$RESTORE_DIR/openmrsdb_backup.sql" || { log_error "OpenMRS database restore failed"; failed=1; }
restore_mysql "$REPORTS_DB_NAME" reportsdb "$RESTORE_DIR/reportsdb_backup.sql" || { log_error "Reports database restore failed"; failed=1; }
restore_postgres clinlims "$OPENELIS_DB_USER" openelisdb "$RESTORE_DIR/openelisdb_backup.sql" clinlims || failed=1
restore_postgres "$ODOO_DB_NAME" "$ODOO_DB_USER" odoodb "$RESTORE_DIR/odoodb_backup.sql" || failed=1
restore_postgres "$ODOO_10_DB_NAME" "$ODOO_10_DB_USER" odoo-10-db "$RESTORE_DIR/odoo_10_db_backup.sql" || failed=1
restore_postgres "$DCM4CHEE_DB_NAME" "$DCM4CHEE_DB_USERNAME" pacsdb "$RESTORE_DIR/dcm4cheedb_backup.sql" || failed=1
restore_postgres "$PACS_INTEGRATION_DB_NAME" "$PACS_INTEGRATION_DB_USERNAME" pacsdb "$RESTORE_DIR/pacs_integrationdb_backup.sql" || failed=1
restore_files || { log_error "File restore failed"; failed=1; }
skip_initializer_domains || { log_error "Failed to mark Initializer domains as loaded"; failed=1; }
stop_started_db_services
start_app_services

if [ $failed -ne 0 ]; then
    die "Restore finished with errors. The pre-restore safety backup is in pre-restore/ (restore with: bahmni-restore local pre-restore/<file> --yes --no-safety-backup)"
fi
if [ -n "$SKIPPED_ITEMS" ]; then
    log_warning "Restore completed, but these were NOT restored (see warnings above): $SKIPPED_ITEMS"
else
    log_info "Restore completed successfully. OpenMRS may take a few minutes to come back up."
fi
