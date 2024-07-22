#!/bin/bash

BAHMNI_DOCKER_ENV_FILE=.env

source ../backup_restore/backup_utils.sh
source ${BAHMNI_DOCKER_ENV_FILE}

# Set the backup folder path
BACKUP_ROOT_FOLDER="./backup-artifacts"

# Get the current datetime
datetime=$(date +'%Y-%m-%d_%H-%M-%S')

# Create the backup folder with the current datetime
backup_subfolder_path="$BACKUP_ROOT_FOLDER/$datetime"
mkdir -p "$backup_subfolder_path"

log_info "Saving backup to $backup_subfolder_path..."


openmrs_db_backup_file_path=$backup_subfolder_path/openmrsdb_backup.sql
reports_db_backup_file_path=$backup_subfolder_path/reportsdb_backup.sql
openelis_db_backup_file_path=$backup_subfolder_path/openelisdb_backup.sql
odoo_db_backup_file_path=$backup_subfolder_path/odoodb_backup.sql
odoo_10_db_backup_file_path=$backup_subfolder_path/odoo_10_db_backup.sql
dcm4chee_db_backup_file_path=$backup_subfolder_path/dcm4cheedb_backup.sql
pacs_integration_db_backup_file_path=$backup_subfolder_path/pacs_integrationdb_backup.sql


openmrs_service_name="openmrs"
reports_service_name="reports"
dcm4chee_service_name="dcm4chee"
openmrs_db_service_name="openmrsdb"
reports_db_service_name="reportsdb"
openelis_db_service_name="openelisdb"
odoo_service_name="odoo"
odoo_db_service_name="odoodb"
odoo_10_db_service_name="odoo-10-db"
dcm4chee_db_service_name="pacsdb"
pacs_integration_db_service_name="pacsdb"

log_info "Taking backup for OpenMRS Database"
backup_db "mysql" $OPENMRS_DB_NAME $OPENMRS_DB_USERNAME $OPENMRS_DB_PASSWORD $openmrs_db_service_name $openmrs_db_backup_file_path

log_info "Taking backup for Reports Database"
backup_db "mysql" $REPORTS_DB_NAME $REPORTS_DB_USERNAME $REPORTS_DB_PASSWORD $reports_db_service_name $reports_db_backup_file_path

log_info "Taking backup for OpenELIS Database"
backup_db "postgres" "clinlims" $OPENELIS_DB_USER $OPENELIS_DB_PASSWORD $openelis_db_service_name $openelis_db_backup_file_path

log_info "Taking backup for Odoo Database"
backup_db "postgres" $ODOO_DB_NAME $ODOO_DB_USER $ODOO_DB_PASSWORD $odoo_db_service_name $odoo_db_backup_file_path

log_info "Taking backup for Odoo 10 Database"
backup_db "postgres" $ODOO_10_DB_NAME $ODOO_10_DB_USER $ODOO_10_DB_PASSWORD $odoo_10_db_service_name $odoo_10_db_backup_file_path

log_info "Taking backup for DCM4CHEE Database"
backup_db "postgres" $DCM4CHEE_DB_NAME $DCM4CHEE_DB_USERNAME $DCM4CHEE_DB_PASSWORD $dcm4chee_db_service_name $dcm4chee_db_backup_file_path

log_info "Taking backup for PACS Integration Database"
backup_db "postgres" $PACS_INTEGRATION_DB_NAME $PACS_INTEGRATION_DB_USERNAME $PACS_INTEGRATION_DB_PASSWORD $pacs_integration_db_service_name $pacs_integration_db_backup_file_path


log_info "Taking backup for Patient-Documents"
backup_container_file_system $openmrs_service_name "/home/bahmni/document_images" "$BACKUP_ROOT_FOLDER"

log_info "Taking backup for Uploaded-Results"
backup_container_file_system $openmrs_service_name "/home/bahmni/uploaded_results" "$BACKUP_ROOT_FOLDER"

log_info "Taking backup for Uploaded-Files"
backup_container_file_system $openmrs_service_name "/home/bahmni/uploaded-files" "$BACKUP_ROOT_FOLDER"

log_info "Taking backup for Patient-Images"
backup_container_file_system $openmrs_service_name "/home/bahmni/patient_images" "$BACKUP_ROOT_FOLDER"

log_info "Taking backup for Clinical-Forms"
backup_container_file_system $openmrs_service_name "/home/bahmni/clinical_forms" "$BACKUP_ROOT_FOLDER"

log_info "Taking backup for Configuration Checksums"
backup_container_file_system $openmrs_service_name "/openmrs/data/configuration_checksums" "$BACKUP_ROOT_FOLDER"

log_info "Taking backup for Queued Reports results"
backup_container_file_system $reports_service_name "/home/bahmni/reports" "$BACKUP_ROOT_FOLDER"

log_info "Taking backup for Odoo Files"
backup_container_file_system $odoo_service_name "/var/lib/odoo/filestore" "$BACKUP_ROOT_FOLDER"

log_info "Taking backup for DCM4CHEE Archive"
backup_container_file_system $dcm4chee_service_name "/var/lib/bahmni/dcm4chee/server/default/archive/." "$BACKUP_ROOT_FOLDER/dcm4chee_archive"

