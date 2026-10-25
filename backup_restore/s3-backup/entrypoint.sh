#!/bin/bash
set -euo pipefail

# busybox crond does not pass the container environment to jobs, so snapshot it for the job to source
function save_environment() {
    export -p >/etc/backup.env
    chmod 600 /etc/backup.env
}

case "${1:-cron}" in
cron)
    save_environment
    schedule="${BACKUP_CRON_SCHEDULE:-0 2 * * *}"
    echo "${schedule} /usr/local/bin/s3_backup.sh >/proc/1/fd/1 2>/proc/1/fd/2" >/etc/crontabs/root
    echo "INFO - Bahmni S3 backup scheduled: '${schedule}' (server local time: $(date +'%Z, UTC%z'))"
    [ -z "${S3_BUCKET:-}" ] && echo -e "\033[33mWARN - S3_BUCKET is not set in .env; scheduled backups will fail until it is configured\033[0m"
    if [ "${BACKUP_RUN_ON_STARTUP:-false}" == "true" ]; then
        /usr/local/bin/s3_backup.sh || true
    fi
    exec crond -f -d 8
    ;;
backup | now)
    exec /usr/local/bin/s3_backup.sh
    ;;
restore)
    shift
    exec /usr/local/bin/s3_restore.sh "$@"
    ;;
*)
    exec "$@"
    ;;
esac
