# Backup Script:
## This bash script takes backups of the OpenMRS and Reports databases using mysqldump and copies Patient Documents and Images from their respective Docker containers to a backup directory.

## Usage

1. Open a terminal and navigate to the directory where the script is located.
2. Open the script file (backup.sh) in a text editor and customize the configuration variables according to your setup:
    backup_folder: Specify the path to the folder where you want to store the backups. By default, it is set to the current directory.
    openmrs_container: Set the name of the Docker container for the OpenMRS database.
    reports_container: Set the name of the Docker container for the Reports database.
    patient_documents_container: Set the name of the Docker container for Patient Documents.
    patient_images_container: Set the name of the Docker container for Patient Images.
    openmrsdb_username: Set the username for the OpenMRS database.
    openmrsdb_password: Set the password for the OpenMRS database.
    reportsdb_username: Set the username for the Reports database.
    reportsdb_password: Set the password for the Reports database.
3. Save the changes to the script file.
4. In the terminal, navigate to the directory where the script is located.
5. Make the script executable:
    chmod +x backup.sh
6. Run the script by executing the following command:
    ./backup.sh

The script will start taking backups of the specified components and save them in the designated backup folder.
After the script finishes running, you will find the backup files and directories in the backup folder.

# Database and File Restoration Script:
## This Bash script is designed to restore databases and files.

## Usage

1. Make the script executable:
   chmod +x restore.sh
2. Run the script with the following command:
    ./restore.sh <path_to_restore_folder> [--silent]
   - `<path_to_restore_folder>`: The path to the folder containing the backup files for restoration.
   - `--silent` (optional): If specified, the script will run in silent mode and skip restoration without user confirmation if any required folders are missing.

## Backup Folder Structure

The script expects the backup folder to have the following structure:

```
<restore_folder>/
├── openmrs/
│   └── openmrsdb_backup.sql
├── reports/
│   └── reportsdb_backup.sql
├── document_images/
│   └── (patient document images)
└── patient_images/
    └── (patient images)
```

- The `openmrs/` folder should contain the `openmrsdb_backup.sql` file, which is the backup of the OpenMRS database.
- The `reports/` folder should contain the `reportsdb_backup.sql` file, which is the backup of the Reports database.
- The `document_images/` folder should contain the backup of patient document images.
- The `patient_images/` folder should contain the backup of patient images.

## Example Usage

```./restore.sh /path/to/restore/folder --silent```

This command restores the OpenMRS database, Reports database, patient documents, and patient images from the specified restore folder in silent mode. No user confirmation is required if any of the required folders are missing.

```./restore.sh /path/to/restore/folder```

This command restores the databases and files from the specified restore folder. If any of the required folders are missing, the script prompts the user for confirmation to continue the restoration process.

## Note
- Update the Docker container names, usernames, and passwords in the script according to your system configuration.
- Make sure to have appropriate permissions to execute the script and access the required files and folders.
