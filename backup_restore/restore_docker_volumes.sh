#!/bin/bash
function is_directory_exists() {
  if [[ -d $1 ]]; then
    return 0
  else
    return 1
  fi
}
function is_directory_empty() {
  if [[ -z "$(ls -A $1)" ]]; then
    return 0
  else
    return 1
  fi
}

function log_error() {
    local message=$1
    echo -e "\033[31mERROR - ${message}\033[0m"
}

function log_warning() {
    local message=$1
    echo -e "\033[33mWARN - ${message}\033[0m"
}

function log_info() {
    local message=$1
    echo "INFO - ${message}"
}


function copy_from_restore_to_mount(){
  source=$1
  destination=$2
  artifact_name=$(echo "$source" | awk -F "/" '{print $3}')
  volume_mount_name=$(echo "$destination" | awk -F "/" '{print $3}')
  if is_directory_exists "$source" && ! is_directory_empty "$source" ; then
    if is_directory_empty "$destination"; then
      log_info "Copying $source to $destination"
      cp -r "$source"/* "$destination"
    else
      log_warning "Destination volume mount $volume_mount_name is not empty. So skipping restore for $artifact_name into $volume_mount_name."
    fi
  else
    log_error "Source directory for $artifact_name does not exist or is empty. So skipping restore for $artifact_name."
  fi
}

log_info "Starting File System Restore into volume mounts...."
copy_from_restore_to_mount /restore-artifacts/patient_images /mounts/bahmni-patient-images
copy_from_restore_to_mount /restore-artifacts/document_images /mounts/bahmni-document-images
copy_from_restore_to_mount /restore-artifacts/clinical_forms /mounts/bahmni-clinical-forms
copy_from_restore_to_mount /restore-artifacts/configuration_checksums /mounts/configuration_checksums
copy_from_restore_to_mount /restore-artifacts/uploaded_results /mounts/bahmni-lab-results
copy_from_restore_to_mount /restore-artifacts/reports /mounts/bahmni-queued-reports
copy_from_restore_to_mount /restore-artifacts/uploaded-files /mounts/bahmni-uploaded-files
copy_from_restore_to_mount /restore-artifacts/dcm4chee_archive /mounts/dcm4chee-archive

log_info -e "File System Restore completed."
