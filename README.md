### Starting the MySQL container
Set environment values for MYSQL\_ROOT\_PASSWORD and OPENMRS\_DB\_PASSWORD when starting
the MySQL container. Both passwords are needed for the database initialisation.

```
export MYSQL_ROOT_PASSWORD=Admin123
export OPENMRS_DB_PASSWORD=User456
docker-compose up
```
