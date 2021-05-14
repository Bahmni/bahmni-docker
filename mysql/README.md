### Building the MySQL image
```
docker build . -t bahmni/mysql
```

### Starting the MySQL container
Specify values for MYSQL\_ROOT\_PASSWORD, MYSQL\_DATABASE, MYSQL\_USER and
MYSQL\_PASSWORD when starting the MySQL container.
All environment variables are needed for the database initialisation.

```
docker run \
  -e MYSQL_ROOT_PASSWORD=Admin123 -e MYSQL_DATABASE=openmrs \
  -e MYSQL_USER=openmrs-user -e MYSQL_PASSWORD=User456 \
  -d bahmni/mysql:latest \
  --character-set-server=utf8mb4 --collation-server=utf8mb4_unicode_ci
```
