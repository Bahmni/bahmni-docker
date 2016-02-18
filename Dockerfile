FROM centos:6.6
MAINTAINER Bahmni Team <bahmni@thoughtworks.com>

ADD base.sh /tmp/base.sh

RUN chmod +x /tmp/base.sh
RUN /tmp/base.sh

RUN yum install -y supervisor
COPY supervisord.conf /etc/supervisord.conf

# Apache
EXPOSE 443

# Apps
EXPOSE 8080
EXPOSE 8069
EXPOSE 8081

# Apps debug
EXPOSE 8000
EXPOSE 8001
EXPOSE 8002
EXPOSE 8003
EXPOSE 8004

# Databases
EXPOSE 3306
EXPOSE 5432

CMD ["/usr/bin/supervisord"]