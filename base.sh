#!/bin/bash

set -x

setup_repos(){
echo "# Enable to use MySQL 5.6
[mysql56-community]
name=MySQL 5.6 Community Server
baseurl=http://repo.mysql.com/yum/mysql-5.6-community/el/6/x86_64
enabled=1
gpgcheck=0
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-mysql" > /etc/yum.repos.d/mysql56.repo

    wget https://bintray.com/bahmni/rpm/rpm -O /etc/yum.repos.d/bintray-bahmni-rpm.repo
    sed -i "s#http://dl.bintray.com/bahmni/rpm#https://bahmni-repo.twhosted.com/rpm/bahmni#g" /etc/yum.repos.d/bintray-bahmni-rpm.repo
    wget https://dl.fedoraproject.org/pub/epel/epel-release-latest-6.noarch.rpm -O epel-release-latest-6.noarch.rpm
    rpm -Uvh epel-release-latest-6.noarch.rpm
    yum -y -x 'bahmni*' -x 'openmrs' -x 'mysql-community*' update
}

install_oracle_jre(){
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

install_pgsql(){
    wget http://yum.postgresql.org/9.2/redhat/rhel-6-x86_64/pgdg-centos92-9.2-7.noarch.rpm -O pgdg-centos92-9.2-7.noarch.rpm
    rpm -ivh pgdg-centos92-9.2-7.noarch.rpm
    yum install -y postgresql92-server
    service postgresql-9.2 initdb
    sed -i 's/peer/trust/g' /var/lib/pgsql/9.2/data/pg_hba.conf
    sed -i 's/ident/trust/g' /var/lib/pgsql/9.2/data/pg_hba.conf
    service postgresql-9.2 start
}

install_bahmni(){
    yum install -y bahmni-openmrs
    yum install -y bahmni-emr
    yum install -y bahmni-web
    yum install -y bahmni-certs
    yum install -y bahmni-reports
    yum install -y bahmni-lab
    yum install -y bahmni-lab-connect
    yum install -y bahmni-erp
    yum install -y bahmni-erp-connect
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
    rm mysql_backup.sql
    rm pgsql_backup.sql
    yum clean all
}

yum install -y wget
yum install -y sudo
yum install -y tar

sed -i -e "s/Defaults    requiretty.*/ #Defaults    requiretty/g" /etc/sudoers

setup_repos
install_oracle_jre
install_mysql
install_pgsql
install_bahmni
config_services
cleanup
