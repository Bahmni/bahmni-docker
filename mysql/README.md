### Building the MySQL image
```
docker build . -t bahmni/mysql
```

### Starting the MySQL container
Specify values for MYSQL\_ROOT\_PASSWORD and OPENMRS\_DB\_PASSWORD when starting
the MySQL container. Both passwords are needed for the database initialisation.

```
docker run \
  -e MYSQL_ROOT_PASSWORD=Admin123 -e OPENMRS_DB_PASSWORD=User456 \
  -d bahmni/mysql:latest \
  --character-set-server=utf8mb4 --collation-server=utf8mb4_unicode_ci
```
