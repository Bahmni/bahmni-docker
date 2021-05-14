#!/bin/sh
set -e

create_database(){
  if [ "${BAHMNI_IMPLEMENTATION_NAME:-default}" = "default" ]; then
    echo "clean openmrs database will be created with demo data"
    mysql -h localhost -uroot -p$MYSQL_ROOT_PASSWORD $MYSQL_DATABASE < /openmrs/resources/openmrs_demo_dump.sql
  else
    echo "clean openmrs database will be created with no demo data"
    mysql -h localhost -uroot -p$MYSQL_ROOT_PASSWORD  < /openmrs/resources/openmrs_clean_dump.sql
  fi
}

echo "initializing openmrs database"
create_database
