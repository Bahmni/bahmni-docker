# Bahmni Backup & Restore (S3)

The `backup` service in `bahmni-standard/docker-compose.yml` takes a daily backup of Bahmni at midnight (server local time), uploads it to S3, keeps the last 3 days, and can restore any backup from S3 or local storage.

All commands below are run from the `bahmni-standard` folder:

```bash
cd /opt/bahmni/bahmni-docker/bahmni-standard
```

## What is backed up

| Item | Source |
|---|---|
| OpenMRS database | `openmrsdb` (MySQL) |
| Reports database | `reportsdb` (MySQL) |
| OpenELIS, Odoo, Odoo 10, PACS databases | only when those services exist on this install (see below) |
| Patient images, patient documents, clinical forms, uploaded files, lab results, queued reports, configuration checksums | OpenMRS / Reports containers |
| Odoo filestore, DCM4CHEE archive | only when those services exist on this install |

Each backup is one archive, `bahmni-standard_<YYYY-MM-DD_HH-MM-SS>.tar.gz`. It holds a single folder in the layout `restore_bahmni_standard.sh` expects.

## Setup

1. Fill in the **Backup & S3 Storage** section of `bahmni-standard/.env`. See `.example.env` for dummy values.

   | Variable | Default | Purpose |
   |---|---|---|
   | `S3_BUCKET` | – (required) | Bucket to store backups in |
   | `S3_PREFIX` | `bahmni-standard` | Folder inside the bucket |
   | `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` | – | Leave empty to use an EC2 instance role (the instance's metadata hop limit must be at least 2) |
   | `AWS_DEFAULT_REGION` | – | Bucket region, e.g. `ap-south-1` |
   | `AWS_ENDPOINT_URL` | – | Only for S3-compatible storage (MinIO, Wasabi, …) |
   | `S3_STORAGE_CLASS` | `STANDARD` | S3 storage class |
   | `S3_SSE` | `AES256` | Server-side encryption (`AES256` or `aws:kms`) |
   | `BACKUP_CRON_SCHEDULE` | `0 0 * * *` | When to back up (cron format, in the server's local time zone) |
   | `BACKUP_RUN_ON_STARTUP` | `false` | Also back up when the container starts |
   | `BACKUP_S3_RETENTION_DAYS` | `3` | Days of backups kept in S3 |
   | `BACKUP_LOCAL_PATH` | `./backup-artifacts` | Host folder for local archives |
   | `BACKUP_LOCAL_RETENTION_DAYS` | `1` | Days kept locally (`0` = delete after upload) |
   | `RESTORE_SKIP_INITIALIZER_DOMAINS` | `ocl` | OpenMRS Initializer domains to skip on the first start after a restore (comma-separated, `all`, or empty for none). See [Restoring onto a server with different config](#restoring-onto-a-server-with-different-config) |
   | `BACKUP_MEM_LIMIT` / `BACKUP_CPUS` | `256m` / `0.5` | Resource caps for the backup container |

2. The AWS credentials need these permissions on the bucket: `s3:PutObject`, `s3:GetObject`, `s3:ListBucket` and `s3:DeleteObject`.

3. Make sure `COMPOSE_PROFILES` in `.env` contains `backup` (e.g. `COMPOSE_PROFILES=emr,backup`). Then build and start the container:

   ```bash
   sudo docker compose up -d --build backup
   ```

   After changing `.env`, run the same command again so the container picks up the new values.

## Backup commands

| Task | Command |
|---|---|
| Run a backup now | `sudo docker compose exec backup s3_backup.sh` |
| Follow backup logs | `sudo docker compose logs -f backup` |
| Show the schedule | `sudo docker compose exec backup cat /etc/crontabs/root` |
| List backups (S3 and local) | `sudo docker compose exec backup bahmni-restore list` |
| Download a backup by hand | `aws s3 cp s3://<bucket>/bahmni-standard/<archive>.tar.gz .` |

What a backup run does:
1. Runs `backup_bahmni_standard.sh`. MySQL dumps use `--single-transaction`, so tables are not locked.
   - A database whose container exists but is stopped is started for the dump and stopped again. For example, `reportsdb` holds restored data even when `reports` is not in `COMPOSE_PROFILES`. Databases of services never created on this install are skipped.
   - Files are copied from the app containers. If a container does not exist (for example `reports`) but its volume has files, they are copied from the volume instead. The `Unable to backup ... container is not created` error printed just before this can be ignored in that case.
2. Checks that the OpenMRS dump is complete. If it isn't, nothing is uploaded or deleted.
3. Compresses the backup and uploads it to `s3://<S3_BUCKET>/<S3_PREFIX>/`.
4. Only after a successful upload, deletes S3 backups older than `BACKUP_S3_RETENTION_DAYS` and local ones older than `BACKUP_LOCAL_RETENTION_DAYS`.

Only one backup or restore can run at a time.

## Restore commands

> **A restore replaces the current OpenMRS and Reports databases and patient files.** Bahmni is stopped while it runs, so plan a short maintenance window. A safety backup of the current state is taken first, unless you skip it.

| Task | Command |
|---|---|
| Restore the latest backup from S3 | `sudo docker compose exec backup bahmni-restore s3 latest --yes` |
| Restore the latest local backup | `sudo docker compose exec backup bahmni-restore local latest --yes` |
| Restore a specific S3 backup | `sudo docker compose exec backup bahmni-restore s3 bahmni-standard_2026-10-25_02-00-00.tar.gz --yes` |
| Restore from a full S3 path | `sudo docker compose exec backup bahmni-restore s3 s3://other-bucket/path/backup.tar.gz --yes` |
| Restore a specific local archive or folder | `sudo docker compose exec backup bahmni-restore local <name> --yes` |
| Check a backup without changing anything | `sudo docker compose exec backup bahmni-restore s3 latest --dry-run` |
| Undo the last restore | `sudo docker compose exec backup bahmni-restore local pre-restore/<pre-restore_...tar.gz> --yes --no-safety-backup` |

Options:

| Option | Meaning |
|---|---|
| `latest` (default) | Newest backup in S3 (by upload time) or in the local backup folder (by modification time) |
| `--yes` | Required to actually restore |
| `--dry-run` | Download/extract and verify the backup only |
| `--no-safety-backup` | Skip the pre-restore backup of the current state |

What a restore does:
1. Downloads or picks the backup and checks that the OpenMRS dump is complete. It refuses to continue otherwise.
2. Saves the current state to `backup-artifacts/pre-restore/pre-restore_<timestamp>.tar.gz`. The last 3 are kept.
3. Stops all Bahmni services except the databases.
4. Drops and re-imports the OpenMRS and Reports MySQL databases. If a database's service is not running (for example `reportsdb` when `reports` is not in `COMPOSE_PROFILES`), it is started for the restore and stopped again afterwards, so the data is in place when you enable it.
5. Replaces the contents of the file volumes with the backup's files.
6. Marks the config files of the domains in `RESTORE_SKIP_INITIALIZER_DOMAINS` as already loaded, so the OpenMRS Initializer does not load them into the restored database.
7. Starts the stopped services again. This happens even if the restore fails.

If anything in the backup could not be restored (for example a non-empty PostgreSQL database), the restore ends with a warning that lists it.

OpenMRS takes a few minutes to come back up after a restore.

### Restoring onto a server with different config

On startup, the OpenMRS Initializer loads every file in `masterdata/configuration` that has no matching checksum in the `configuration_checksums` volume. A restore puts back the checksums of the server that was backed up. If this server's config differs (another `bahmni/standard-config` version or a custom config), the Initializer loads the differences into the restored database on the next start, and OpenMRS does not respond until it finishes.

| `RESTORE_SKIP_INITIALIZER_DOMAINS` | Result |
|---|---|
| `ocl` (default) | Skips the CIEL concept dictionary import, which alone takes 30+ minutes. Other config differences are still loaded |
| `all` | Skips every domain: the restored database stays an exact copy of the backed-up server |
| empty | Loads all differences |

Skipped files are only marked as loaded. A later change to one of them is loaded as usual.

### Restoring a backup from another server or a manual backup

Copy the `.tar.gz` archive (keep the `.tar.gz` extension), or an extracted backup folder containing `openmrsdb_backup.sql`, into `bahmni-standard/backup-artifacts/`. Then run:

```bash
sudo docker compose exec backup bahmni-restore list
sudo docker compose exec backup bahmni-restore local <archive-or-folder-name> --yes
```

## Notes and limitations

- PostgreSQL databases (OpenELIS, Odoo, PACS) are restored only into **empty** databases, the same as `restore_bahmni_standard.sh`.
- The schedule and the backup file names use the server's local time zone, read from the host's `/etc/localtime`. The `TZ` setting in `.env` (used by the other Bahmni services) does not affect them. If you change the server's time zone, restart the container: `sudo docker compose up -d --force-recreate backup`.
- The container mounts the Docker socket so it can run dumps inside the database containers and stop or start services. Treat it as having root access to the host.
- `.env` is tracked by git. Do not commit real AWS credentials.
- For a fresh server, the original manual flow still works. See [the Bahmni docs](https://bahmni.atlassian.net/wiki/spaces/BAH/pages/3222601729/Performing+a+Backup+Restore+of+Container+Data+Files+docker) and `../../bahmni-standard/restore_bahmni_standard.sh`.

## Troubleshooting

| Symptom | Fix |
|---|---|
| `S3_BUCKET is not set` | Fill in `.env`, then `sudo docker compose up -d backup` |
| `Unable to locate credentials` | Set the AWS keys in `.env`, or attach an instance role (metadata hop limit ≥ 2) |
| `OpenMRS database dump is missing or incomplete` | Check that `openmrsdb` is running and `MYSQL_ROOT_PASSWORD` in `.env` is correct |
| `A backup or restore is already running` | Wait for it to finish (`sudo docker compose logs -f backup`) |
| Services not back up after a restore | `sudo docker compose up -d` |
| `No local backups found` although the file is in `backup-artifacts/` | The archive must end in `.tar.gz` (a download may drop the `.gz`): rename it |
| OpenMRS takes very long to start after a restore, logs show `openconceptlab` / Initializer imports | The backed-up server had different config; see [Restoring onto a server with different config](#restoring-onto-a-server-with-different-config) |
