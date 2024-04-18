#!/bin/bash

source "../backup_restore/restore_utils.sh"

BAHMNI_DOCKER_ENV_FILE=.env
source ${BAHMNI_DOCKER_ENV_FILE}

if [ $# -ne 1 ]
then
log_error "Missing input for restore-artifacts-path."
echo "Usage: ./restore_bahmni_lite.sh <restore-artifacts-path>"
exit 1
fi

if ! is_directory_exists "$1" || is_directory_empty "$1" ; then
log_error "Invalid restore-artifacts-path: $1 Directory does not exist or is empty."   
exit 1
fi

export RESTORE_ARTIFACTS_PATH=$1


# Database Container names
openmrs_db_service_name="openmrsdb"
reports_db_service_name="reportsdb"
crater_db_service_name="craterdb"
crater_atomfeed_db_service_name="crater-atomfeed-db"

# Database Backup file paths
openmrs_db_backup_file_path="${RESTORE_ARTIFACTS_PATH}/openmrsdb_backup.sql"
reports_db_backup_file_path="${RESTORE_ARTIFACTS_PATH}/reportsdb_backup.sql"
crater_db_backup_file_path="${RESTORE_ARTIFACTS_PATH}/craterdb_backup.sql"
crater_atomfeed_db_backup_file_path="${RESTORE_ARTIFACTS_PATH}/crateratomfeeddb_backup.sql"


log_info "Starting Database Restore..."

restore_db "mysql" $OPENMRS_DB_NAME $OPENMRS_DB_USERNAME $OPENMRS_DB_PASSWORD $openmrs_db_service_name $openmrs_db_backup_file_path

restore_db "mysql" $REPORTS_DB_NAME $REPORTS_DB_USERNAME $REPORTS_DB_PASSWORD $reports_db_service_name $reports_db_backup_file_path

restore_db "mysql" $CRATER_DB_DATABASE $CRATER_DB_USERNAME $CRATER_DB_PASSWORD $crater_db_service_name $crater_db_backup_file_path

restore_db "mysql" $CRATER_ATOMFEED_DB_NAME $CRATER_ATOMFEED_DB_USERNAME $CRATER_ATOMFEED_DB_PASSWORD $crater_atomfeed_db_service_name $crater_atomfeed_db_backup_file_path

log_info "Starting File System Restore..."
docker compose --env-file ${BAHMNI_DOCKER_ENV_FILE} up restore_volumes
docker compose --env-file ${BAHMNI_DOCKER_ENV_FILE} rm -f restore_volumes
