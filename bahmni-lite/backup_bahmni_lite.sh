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

# Retention policy: Remove folders with dates in their name older than 7 days
log_info "Applying retention policy for backup folders..."
find "$BACKUP_ROOT_FOLDER" -maxdepth 1 -type d -name "20*" -mtime +7 -exec rm -rf {} \;
log_info "Removed dated folders older than 7 days."

# Check and clean subfolders (e.g., clinical_forms, configuration_checksums, etc.)
log_info "Applying retention policy for files in static subfolders..."
static_folders=("clinical_forms" "configuration_checksums" "document_images" "patient_images" "uploaded-files" "uploaded_results" "reports")

for folder in "${static_folders[@]}"; do
  folder_path="$BACKUP_ROOT_FOLDER/$folder"
  if [ -d "$folder_path" ]; then
    log_info "Cleaning up files older than 7 days in $folder_path..."
    find "$folder_path" -type f -mtime +7 -exec rm -f {} \;
  else
    log_info "Folder $folder_path does not exist. Skipping..."
  fi
done

log_info "Retention policy applied to all folders."

# Backup database and files
openmrs_db_backup_file_path=$backup_subfolder_path/openmrsdb_backup.sql
reports_db_backup_file_path=$backup_subfolder_path/reportsdb_backup.sql

openmrs_service_name="openmrs"
reports_service_name="reports"
openmrs_db_service_name="openmrsdb"
reports_db_service_name="reportsdb"

log_info "Taking backup for OpenMRS Database"
backup_db "mysql" $OPENMRS_DB_NAME $OPENMRS_DB_USERNAME $OPENMRS_DB_PASSWORD $openmrs_db_service_name $openmrs_db_backup_file_path

log_info "Taking backup for Reports Database"
backup_db "mysql" $REPORTS_DB_NAME $REPORTS_DB_USERNAME $REPORTS_DB_PASSWORD $reports_db_service_name $reports_db_backup_file_path

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

log_info "Backup process completed successfully."
