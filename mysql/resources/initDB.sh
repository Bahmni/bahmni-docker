#!/bin/sh
set -e

load_configuration(){
  . /etc/openmrs/openmrs.conf
}

check_passwords(){
  if [[ -z "${MYSQL_ROOT_PASSWORD}" ]]; then
    echo "MYSQL_ROOT_PASSWORD must not be empty... Skipping database initialisation"
    exit 1;
  fi

  if [[ -z "${OPENMRS_DB_PASSWORD}" ]]; then
    echo "OPENMRS_DB_PASSWORD must not be empty... Skipping database initialisation"
    exit 1;
  fi
}

create_database(){
  local RESULT=`mysql -h $OPENMRS_DB_SERVER -u$MYSQL_ROOT_USER -p$MYSQL_ROOT_PASSWORD --skip-column-names -e "SHOW DATABASES LIKE 'openmrs'"`
  if [ "$RESULT" != "openmrs" ] ; then
    mysql -h $OPENMRS_DB_SERVER -u$MYSQL_ROOT_USER -p$MYSQL_ROOT_PASSWORD -e "CREATE DATABASE openmrs;"
    if [ "${IMPLEMENTATION_NAME:-default}" = "default" ]; then
      echo "openmrs database not found... Restoring a base dump suitable to work with default config"
      mysql -h $OPENMRS_DB_SERVER -u$MYSQL_ROOT_USER -p$MYSQL_ROOT_PASSWORD openmrs < /openmrs/scripts/openmrs_demo_dump.sql
    else
      echo "clean openmrs database will be created with no demo data"
      mysql -h $OPENMRS_DB_SERVER -u$MYSQL_ROOT_USER -p$MYSQL_ROOT_PASSWORD  < /openmrs/scripts/openmrs_clean_dump.sql
    fi
  fi

  echo "creating database user '$OPENMRS_DB_USER'"
  mysql -h $OPENMRS_DB_SERVER -u$MYSQL_ROOT_USER -p$MYSQL_ROOT_PASSWORD -e "CREATE USER '$OPENMRS_DB_USER'@'$OPENMRS_DB_SERVER' IDENTIFIED BY '*';
      GRANT ALL PRIVILEGES ON openmrs.* TO '$OPENMRS_DB_USER'@'$OPENMRS_DB_SERVER' identified by '$OPENMRS_DB_PASSWORD'  WITH GRANT OPTION;"
}

echo "initializing openmrs database"
load_configuration
check_passwords
create_database
