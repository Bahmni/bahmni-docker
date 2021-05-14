### Starting the MySQL container
Set values for MYSQL\_ROOT\_PASSWORD and MYSQL\_PASSWORD when starting
the MySQL container. Both passwords are needed for the database initialisation.

```
export MYSQL_ROOT_PASSWORD=Admin123
export MYSQL_PASSWORD=User456
docker-compose up
```
