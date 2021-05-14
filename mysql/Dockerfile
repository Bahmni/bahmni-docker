FROM mysql:5.7

RUN mkdir -p /openmrs/resources

COPY resources/initDB.sh /docker-entrypoint-initdb.d/initDB.sh
COPY resources/*.sql /openmrs/resources
