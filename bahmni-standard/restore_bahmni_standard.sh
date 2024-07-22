#!/bin/bash

source "../backup_restore/restore_utils.sh"

BAHMNI_DOCKER_ENV_FILE=.env
source ${BAHMNI_DOCKER_ENV_FILE}

if [ $# -ne 1 ]
then
log_error "Missing input for restore-artifacts-path."
echo "Usage: ./restore_bahmni_standard.sh <restore-artifacts-path>"
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
openelis_db_service_name="openelisdb"
odoo_db_service_name="odoodb"
odoo_10_db_service_name="odoo-10-db"
dcm4chee_db_service_name="pacsdb"
pacs_integration_db_service_name="pacsdb"

# Database Backup file paths
openmrs_db_backup_file_path="${RESTORE_ARTIFACTS_PATH}/openmrsdb_backup.sql"
reports_db_backup_file_path="${RESTORE_ARTIFACTS_PATH}/reportsdb_backup.sql"
openelis_db_backup_file_path="${RESTORE_ARTIFACTS_PATH}/openelisdb_backup.sql"
odoo_db_backup_file_path="${RESTORE_ARTIFACTS_PATH}/odoodb_backup.sql"
odoo_10_db_backup_file_path="${RESTORE_ARTIFACTS_PATH}/odoo_10_db_backup.sql"
dcm4chee_db_backup_file_path="${RESTORE_ARTIFACTS_PATH}/dcm4cheedb_backup.sql"
pacs_integration_db_backup_file_path="${RESTORE_ARTIFACTS_PATH}/pacs_integrationdb_backup.sql"


log_info "Starting Database Restore..."

restore_db "mysql" $OPENMRS_DB_NAME root $MYSQL_ROOT_PASSWORD $openmrs_db_service_name $openmrs_db_backup_file_path

restore_db "mysql" $REPORTS_DB_NAME root $MYSQL_ROOT_PASSWORD $reports_db_service_name $reports_db_backup_file_path

restore_db "postgres" "clinlims" $OPENELIS_DB_USER $OPENELIS_DB_PASSWORD $openelis_db_service_name $openelis_db_backup_file_path

restore_db "postgres" $ODOO_DB_NAME $ODOO_DB_USER $ODOO_DB_PASSWORD $odoo_db_service_name $odoo_db_backup_file_path

restore_db "postgres" $ODOO_10_DB_NAME $ODOO_10_DB_USER $ODOO_10_DB_PASSWORD $odoo_10_db_service_name $odoo_10_db_backup_file_path

restore_db "postgres" $DCM4CHEE_DB_NAME $DCM4CHEE_DB_USERNAME $DCM4CHEE_DB_PASSWORD $dcm4chee_db_service_name $dcm4chee_db_backup_file_path

restore_db "postgres" $PACS_INTEGRATION_DB_NAME $PACS_INTEGRATION_DB_USERNAME $PACS_INTEGRATION_DB_PASSWORD $pacs_integration_db_service_name $pacs_integration_db_backup_file_path

log_info "Starting File System Restore..."
docker compose --env-file ${BAHMNI_DOCKER_ENV_FILE} up restore_volumes
docker compose --env-file ${BAHMNI_DOCKER_ENV_FILE} rm -f restore_volumes
