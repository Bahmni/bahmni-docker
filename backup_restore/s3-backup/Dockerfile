# Lightweight scheduler that runs the existing Bahmni backup script and ships the result to S3,
# plus `bahmni-restore` to restore the latest (or a chosen) backup from S3 or local storage.
# DB dumps run inside the DB containers (via `docker compose exec`), so client/server versions always match.
FROM docker:29-cli

RUN apk add --no-cache bash aws-cli tzdata coreutils findutils tar gzip util-linux-misc

# Keep the AWS CLI's memory footprint small (default is 10 parallel 8MB parts)
COPY aws-config /etc/aws/config
ENV AWS_CONFIG_FILE=/etc/aws/config

COPY entrypoint.sh s3_backup.sh s3_restore.sh db_services.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/entrypoint.sh /usr/local/bin/s3_backup.sh /usr/local/bin/s3_restore.sh \
    && ln -s /usr/local/bin/s3_restore.sh /usr/local/bin/bahmni-restore

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
CMD ["cron"]
