#!/bin/bash

# Function to restore OpenMRS database
function restore_openmrs_database() {
  if [[ -d "$restore_folder/openmrs" ]]; then
    echo "Restoring OpenMRS database"
    docker exec -i "$openmrs_container" mysql -u $openmrsdb_username --password=$openmrsdb_password openmrs < "$openmrs_backup_file"
  else
    echo "Openmrs backup folder is missing. Thus, skipping OpenMRS restoration."
  fi
}

# Function to restore Reports database
function restore_reports_database() {
  if [[ -d "$restore_folder/reports" ]]; then
    echo "Restoring Reports database"
    docker exec -i "$reports_container" mysql -u $reportsdb_username --password=$reportsdb_password bahmni_reports < "$reports_backup_file"
  else
    echo "Reports backup folder is missing. Thus, skipping Reports restoration."
  fi
}

# Function to restore patient documents
function restore_patient_documents() {
  if [[ -d "$restore_folder/document_images" ]]; then
    echo "Restoring Patient Documents"
    docker cp -a "$restore_folder/document_images" "$patient_documents_container:/usr/share/nginx/html/"
  else
    echo "Document images backup folder is missing. Thus, skipping Document images restoration."
  fi
}

# Function to restore patient images
function restore_patient_images() {
  if [[ -d "$restore_folder/patient_images" ]]; then
    echo "Restoring Patient Images"
    docker cp -a "$restore_folder/patient_images" "$patient_images_container:/home/bahmni/"
  else
    echo "Patient Images backup folder is missing. Thus, skipping Patient images restoration."
  fi
}

# Function to check if required folders exist
function check_required_folders() {
  missing_folders=()

  if [[ ! -d "$restore_folder/openmrs" ]]; then
    missing_folders+=("OpenMRS")
  fi

  if [[ ! -d "$restore_folder/reports" ]]; then
    missing_folders+=("Reports")
  fi

  if [[ ! -d "$restore_folder/document_images" ]]; then
    missing_folders+=("Document-Images")
  fi

  if [[ ! -d "$restore_folder/patient_images" ]]; then
    missing_folders+=("Patient-Images")
  fi

  if [[ ${#missing_folders[@]} -gt 0 ]]; then
    echo "The following folders are missing: ${missing_folders[*]}"
    if [[ "$silent_mode" == true ]]; then
      echo "Skipping restoration due to silent mode."
      exit 1
    else
      while true; do
        read -p "Do you still want to continue? Press 1 for yes, 0 for no: " -n 1 user_input
        echo
        if [[ $user_input == 0 ]]; then
          exit 1
        elif [[ $user_input == 1 ]]; then
          break
        else
          echo "Invalid input. Please press 1 for yes, 0 for no"
        fi
      done
    fi
  fi
}

# Main script

# Get the path to restore from the command-line argument
restore_folder="$1"

# Check if --silent option is specified
if [[ "$2" == "--silent" ]]; then
  silent_mode=true
else
  silent_mode=false
fi

# Check if restore path is provided
if [[ -z "$restore_folder" ]]; then
  echo "Please provide a valid path to restore."
  exit 1
fi

# Check if the restore folder exists
if [[ ! -d "$restore_folder" ]]; then
  echo "Restore folder '$restore_folder' does not exist."
  exit 1
fi

echo "Restoring from folder: $restore_folder"

# Set the backup file paths for Openmrs and Reports
openmrs_backup_file="$restore_folder/openmrs/openmrsdb_backup.sql"
reports_backup_file="$restore_folder/reports/reportsdb_backup.sql"

# Set the Docker container names
openmrs_container="openmrsdb-restore"
reports_container="reportsdb-restore"
patient_documents_container="patient-documents-restore"
patient_images_container="proxy-restore"

# Set the username and password for openmrsdb
openmrsdb_username=openmrs-user
openmrsdb_password=password

# Set the username and password for reportsdb
reportsdb_username=reports-user
reportsdb_password=password

# Check if required folders exist unless in silent mode
check_required_folders

restore_openmrs_database

restore_reports_database

restore_patient_documents

restore_patient_images
