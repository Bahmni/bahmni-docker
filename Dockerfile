FROM centos:6.6
MAINTAINER Bahmni Team <bahmni@thoughtworks.com>

ADD base.sh /tmp/base.sh

RUN chmod +x /tmp/base.sh
RUN /tmp/base.sh

RUN yum clean all; yum install -y supervisor
COPY supervisord.conf /etc/supervisord.conf

# Apache
EXPOSE 443

# OpenMRS
EXPOSE 8050

# OpenERP
EXPOSE 8069

#OpenELIS
EXPOSE 8052

# MySQL
EXPOSE 3306

# Postgresql
EXPOSE 5432

CMD ["/usr/bin/supervisord"]