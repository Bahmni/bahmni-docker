#!/bin/bash

# Set the backup folder path
backup_folder="."

# Get the current datetime
datetime=$(date +'%Y-%m-%d_%I-%M-%S-%p')

# Create the backup folder with the current datetime
backup_subfolder_full_path="$backup_folder/$datetime"
mkdir -p "$backup_subfolder_full_path"

# Set the backup file paths for OpenMRS and Reports
mkdir -p "$backup_subfolder_full_path/openmrs"
mkdir -p "$backup_subfolder_full_path/reports"

backup_subfolder_openmrs_full_path=$backup_subfolder_full_path/openmrs/openmrsdb_backup.sql
backup_subfolder_reports_full_path=$backup_subfolder_full_path/reports/reportsdb_backup.sql

# Set the docker containers names
openmrs_container="openmrsdb"
reports_container="reportsdb"
patient_documents_container="patient-documents"
patient_images_container="proxy"

# Set the username and password for openmrsdb
openmrsdb_username=openmrs-user
openmrsdb_password=password

# Set the username and password for reportsdb
reportsdb_username=reports-user
reportsdb_password=password

echo "Taking backup for OpenMRS"
# Export the openmrs database from the source container
docker exec $openmrs_container mysqldump -u $openmrsdb_username --password=$openmrsdb_password --routines openmrs > "$backup_subfolder_openmrs_full_path" --no-tablespaces

echo "Taking backup for Reports"
# Export the reports database from the source container
docker exec $reports_container mysqldump -u $reportsdb_username --password=$reportsdb_password --routines bahmni_reports > "$backup_subfolder_reports_full_path" --no-tablespaces

echo "Taking backup for Patient-Documents"
# Export the Patient document from the source container
docker cp -a $patient_documents_container:/usr/share/nginx/html/document_images "$backup_subfolder_full_path"

echo "Taking backup for Patient-Images"
# Export the Patient images from the source container
docker cp -a $patient_images_container:/home/bahmni/patient_images "$backup_subfolder_full_path"

