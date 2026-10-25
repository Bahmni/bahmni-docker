#!/bin/bash
# Runs the existing Bahmni backup script, archives the result, uploads it to S3
# and prunes backups older than the configured retention (in S3 and locally).
set -uo pipefail

# crond starts jobs with an empty environment: restore the one saved by entrypoint.sh
[ -z "${BAHMNI_COMPOSE_DIR:-}" ] && [ -f /etc/backup.env ] && source /etc/backup.env

BAHMNI_COMPOSE_DIR="${BAHMNI_COMPOSE_DIR:?BAHMNI_COMPOSE_DIR is required}"
BAHMNI_BACKUP_SCRIPT="${BAHMNI_BACKUP_SCRIPT:-./backup_bahmni_standard.sh}"
BACKUP_NAME_PREFIX="${BACKUP_NAME_PREFIX:-bahmni}"
export BACKUP_ROOT_FOLDER="${BACKUP_ROOT_FOLDER:-/backups}"
S3_RETENTION_DAYS="${BACKUP_S3_RETENTION_DAYS:-3}"
LOCAL_RETENTION_DAYS="${BACKUP_LOCAL_RETENTION_DAYS:-1}"

function log_error() { echo -e "\033[31mERROR - $(date +'%F %T') - $1\033[0m" >&2; }
function log_info() { echo "INFO - $(date +'%F %T') - $1"; }

source /usr/local/bin/db_services.sh

# Empty values from .env would otherwise break the AWS CLI credential/endpoint resolution
for var in AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY AWS_SESSION_TOKEN AWS_DEFAULT_REGION AWS_ENDPOINT_URL; do
    [ -z "${!var:-}" ] && unset "$var"
done

if [ -z "${S3_BUCKET:-}" ]; then
    log_error "S3_BUCKET is not set. Configure the Backup & S3 Storage section in .env"
    exit 1
fi
S3_PREFIX="${S3_PREFIX:-bahmni}"
S3_PREFIX="${S3_PREFIX%/}"
s3_base="s3://${S3_BUCKET}/${S3_PREFIX}"

# Prevent overlapping runs
exec 9>/tmp/s3_backup.lock
if ! flock -n 9; then
    log_error "Another backup is already running, skipping"
    exit 1
fi

export BACKUP_TIMESTAMP=$(date +'%Y-%m-%d_%H-%M-%S')
backup_dir="${BACKUP_ROOT_FOLDER}/${BACKUP_TIMESTAMP}"
archive_name="${BACKUP_NAME_PREFIX}_${BACKUP_TIMESTAMP}.tar.gz"
archive_path="${BACKUP_ROOT_FOLDER}/${archive_name}"

trap 'stop_started_db_services; rm -rf "$backup_dir"' EXIT

log_info "Starting Bahmni backup ${BACKUP_TIMESTAMP}"
cd "$BAHMNI_COMPOSE_DIR"
# Stopped databases that still hold data (e.g. reportsdb restored while "reports" is not enabled) are included too
start_stopped_db_services
nice -n 19 bash "$BAHMNI_BACKUP_SCRIPT"
stop_started_db_services
if ! backup_files_from_mounts "$backup_dir"; then
    log_error "Failed to copy files from volumes; aborting upload and keeping existing backups"
    exit 1
fi

# The backup script only logs errors, so verify the critical OpenMRS dump before shipping anything
openmrs_dump="${backup_dir}/openmrsdb_backup.sql"
if [ ! -s "$openmrs_dump" ] || ! tail -n 1 "$openmrs_dump" | grep -q "Dump completed"; then
    log_error "OpenMRS database dump is missing or incomplete; aborting upload and keeping existing backups"
    exit 1
fi
# Drop empty dumps of services that are not enabled on this install
find "$backup_dir" -maxdepth 1 -name '*.sql' -size 0 -delete

log_info "Compressing backup to ${archive_path}"
if ! nice -n 19 ionice -c 3 tar -C "$BACKUP_ROOT_FOLDER" -czf "$archive_path" "$BACKUP_TIMESTAMP"; then
    log_error "Failed to create archive"
    rm -f "$archive_path"
    exit 1
fi
log_info "Archive size: $(du -h "$archive_path" | cut -f1)"

upload_args=(--only-show-errors)
[ -n "${S3_STORAGE_CLASS:-}" ] && upload_args+=(--storage-class "$S3_STORAGE_CLASS")
[ -n "${S3_SSE:-}" ] && upload_args+=(--sse "$S3_SSE")

log_info "Uploading to ${s3_base}/${archive_name}"
if ! nice -n 19 aws s3 cp "$archive_path" "${s3_base}/${archive_name}" "${upload_args[@]}"; then
    log_error "Upload to S3 failed; keeping local archive and existing S3 backups"
    exit 1
fi
log_info "Upload complete"

# Prune S3 only after a successful upload, so we never drop below the last good backups
cutoff=$(date -u -d "@$(($(date +%s) - S3_RETENTION_DAYS * 86400))" +'%Y-%m-%dT%H:%M:%S')
log_info "Removing S3 backups older than ${S3_RETENTION_DAYS} days (before ${cutoff}Z)"
old_keys=$(aws s3api list-objects-v2 --bucket "$S3_BUCKET" --prefix "${S3_PREFIX}/${BACKUP_NAME_PREFIX}_" \
    --query "Contents[?LastModified<'${cutoff}'].Key" --output text) || {
    log_error "Could not list S3 objects for retention cleanup"
    old_keys=""
}
for key in $old_keys; do
    [ "$key" == "None" ] && continue
    log_info "Deleting s3://${S3_BUCKET}/${key}"
    aws s3 rm "s3://${S3_BUCKET}/${key}" --only-show-errors || log_error "Failed to delete s3://${S3_BUCKET}/${key}"
done

# Local copies: 0 = remove right after upload, N = keep for N days
if [ "$LOCAL_RETENTION_DAYS" -le 0 ]; then
    rm -f "$archive_path"
else
    find "$BACKUP_ROOT_FOLDER" -maxdepth 1 -name "${BACKUP_NAME_PREFIX}_*.tar.gz" \
        -mmin +$((LOCAL_RETENTION_DAYS * 1440 - 60)) -print -delete
fi

log_info "Bahmni backup ${BACKUP_TIMESTAMP} finished successfully"
