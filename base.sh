#!/bin/bash

install_virtual_box_specifics(){
    sed -i "s/^.*requiretty/#Defaults requiretty/" /etc/sudoers
    yum -y install gcc make gcc-c++ kernel-devel-`uname -r` perl
}

setup_repos(){
echo "# Enable to use MySQL 5.6
[mysql56-community]
name=MySQL 5.6 Community Server
baseurl=http://repo.mysql.com/yum/mysql-5.6-community/el/6/x86_64
enabled=1
gpgcheck=0
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-mysql" > /etc/yum.repos.d/mysql56.repo

    yum install -y wget
    sudo wget https://bintray.com/bahmni/rpm/rpm -O /etc/yum.repos.d/bintray-bahmni-rpm.repo
    wget https://dl.fedoraproject.org/pub/epel/epel-release-latest-6.noarch.rpm -O epel-release-latest-6.noarch.rpm
    rpm -Uvh epel-release-latest-6.noarch.rpm
    yum -y -x 'bahmni*' -x 'openmrs' -x 'mysql-community*' update
}

install_oracle_jre(){
    #Optional - Ensure that jre is installed
    wget --no-cookies --no-check-certificate --header "Cookie: gpw_e24=http%3A%2F%2Fwww.oracle.com%2F; oraclelicense=accept-securebackup-cookie" "http://download.oracle.com/otn-pub/java/jdk/7u79-b15/jre-7u79-linux-x64.rpm" -O jre-7u79-linux-x64.rpm
    yum localinstall -y jre-7u79-linux-x64.rpm
}

install_mysql(){
    yum remove -y mysql-libs
    yum clean all
    yum install -y mysql-community-server
    service mysqld start
    mysqladmin -u root password password
}

restore_mysql_database(){
    #Optional Step
    rm -rf mysql_backup.sql.gz mysql_backup.sql
    wget https://github.com/Bahmni/emr-functional-tests/blob/master/dbdump/mysql_backup.sql.gz?raw=true -O mysql_backup.sql.gz
    gzip -d mysql_backup.sql.gz
    mysql -uroot -ppassword < mysql_backup.sql
    echo "FLUSH PRIVILEGES" > flush.sql
    mysql -uroot -ppassword < flush.sql
}

install_pgsql(){
    wget http://yum.postgresql.org/9.2/redhat/rhel-6-x86_64/pgdg-centos92-9.2-7.noarch.rpm -O pgdg-centos92-9.2-7.noarch.rpm
    rpm -ivh pgdg-centos92-9.2-7.noarch.rpm
    yum install -y postgresql92-server
    service postgresql-9.2 initdb
    sed -i 's/peer/trust/g' /var/lib/pgsql/9.2/data/pg_hba.conf
    sed -i 's/ident/trust/g' /var/lib/pgsql/9.2/data/pg_hba.conf
    service postgresql-9.2 start
}

restore_pgsql_db(){
    wget https://github.com/Bahmni/emr-functional-tests/blob/master/dbdump/pgsql_backup.sql.gz?raw=true -O pgsql_backup.sql.gz
    gzip -d pgsql_backup.sql.gz
    psql -Upostgres < pgsql_backup.sql >/dev/null
}

install_bahmni(){
    yum install -y openmrs
    yum install -y bahmni-emr-$BAHMNI_VERSION bahmni-web-$BAHMNI_VERSION bahmni-reports-$BAHMNI_VERSION bahmni-lab-$BAHMNI_VERSION bahmni-lab-connect-$BAHMNI_VERSION bahmni-erp-$BAHMNI_VERSION bahmni-erp-connect-$BAHMNI_VERSION
}

config_services(){
    chkconfig mysqld on
    chkconfig postgresql-9.2 on
    chkconfig httpd on
    chkconfig openmrs on
    chkconfig openerp on
    chkconfig bahmni-lab on
    chkconfig bahmni-erp-connect on
    chkconfig bahmni-reports on
}

cleanup(){
    rm jre-7u79-linux-x64.rpm
    rm pgdg-centos92-9.2-7.noarch.rpm
    yum clean packages
}

if [[ -z $BAHMNI_VERSION ]]; then
    echo "The variable BAHMNI_VERSION is not set. Aborting installation. Please set this variable before executing the script."
    exit 1
fi

install_virtual_box_specifics
setup_repos
install_oracle_jre
install_mysql
restore_mysql_database
install_pgsql
restore_pgsql_db
install_bahmni
config_services
