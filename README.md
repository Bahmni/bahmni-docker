### Starting the MySQL container
Set values for MYSQL\_ROOT\_PASSWORD and MYSQL\_PASSWORD when starting
the MySQL container. Both passwords are needed for the database initialisation.

```
export MYSQL_ROOT_PASSWORD=Admin123
export MYSQL_PASSWORD=User456
docker-compose up
```

### Accessing the MySQL database from your host
Run this command to access the OpenMRS MySQL database from a terminal on your host machine:

```
mysql -h localhost -P 3306 --protocol=tcp -u <username> -p
```
