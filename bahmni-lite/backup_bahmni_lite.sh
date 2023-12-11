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
crater_db_backup_file_path=$backup_subfolder_path/craterdb_backup.sql
crater_atomfeed_db_backup_file_path=$backup_subfolder_path/crateratomfeeddb_backup.sql


openmrs_service_name="openmrs"
reports_service_name="reports"
openmrs_db_service_name="openmrsdb"
reports_db_service_name="reportsdb"
crater_db_service_name="craterdb"
crater_atomfeed_db_service_name="crater-atomfeed-db"

log_info "Taking backup for OpenMRS Database"
backup_db "mysql" $OPENMRS_DB_NAME $OPENMRS_DB_USERNAME $OPENMRS_DB_PASSWORD $openmrs_db_service_name $openmrs_db_backup_file_path

log_info "Taking backup for Reports Database"
backup_db "mysql" $REPORTS_DB_NAME $REPORTS_DB_USERNAME $REPORTS_DB_PASSWORD $reports_db_service_name $reports_db_backup_file_path

log_info "Taking backup for Crater Database"
backup_db "mysql" $CRATER_DB_DATABASE $CRATER_DB_USERNAME $CRATER_DB_PASSWORD $crater_db_service_name $crater_db_backup_file_path

log_info "Taking backup for Crater Atomfeed Database"
backup_db "mysql" $CRATER_ATOMFEED_DB_NAME $CRATER_ATOMFEED_DB_USERNAME $CRATER_ATOMFEED_DB_PASSWORD $crater_atomfeed_db_service_name $crater_atomfeed_db_backup_file_path

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

