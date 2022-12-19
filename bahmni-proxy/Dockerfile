FROM httpd:2.4-alpine

RUN apk add curl
COPY scripts/get_client_side_logging.sh /tmp/get_client_side_logging.sh
RUN sh /tmp/get_client_side_logging.sh && rm /tmp/get_client_side_logging.sh
COPY resources/bahmni-proxy.conf /usr/local/apache2/conf/
RUN echo "Include conf/bahmni-proxy.conf" >> /usr/local/apache2/conf/httpd.conf
COPY resources/index.html /usr/local/apache2/htdocs/index.html
COPY resources/systemdate.sh /usr/local/apache2/cgi-bin/systemdate
COPY resources/bahmni-logo.png /usr/local/apache2/htdocs/bahmni-logo.png
COPY resources/favicon.png /usr/local/apache2/htdocs/favicon.png
COPY resources/maintenance.html /usr/local/apache2/htdocs/maintenance.html
COPY resources/unauthorized.html /usr/local/apache2/htdocs/unauthorized.html
COPY resources/internalError.html /usr/local/apache2/htdocs/internalError.html
COPY resources/style.css /usr/local/apache2/htdocs/style.css
COPY resources/src.jpeg /usr/local/apache2/htdocs/src.jpeg
RUN mkdir /var/cache/mod_proxy
	
RUN apk add --update openssl && \
    rm -rf /var/cache/apk/*
RUN cd /etc/ &&\
    mkdir tls &&\
    cd tls &&\
    openssl req -new -newkey rsa:4096 -days 365 -nodes -x509 -subj "/C=US/ST=Denial/L=Springfield/O=Dis/CN=localhost" -keyout key.pem  -out cert.pem


RUN apk add --no-cache --virtual .build-deps \
		apr-dev \
		apr-util-dev \
		gcc \
        libc-dev \
		apache2-dev \
		apache2-utils \
		py-pip \
		tar \
        python3-dev \
        libffi-dev

RUN python3 -m venv /opt/certbot/ &&\
        /opt/certbot/bin/pip install certbot &&\
        ln -s /opt/certbot/bin/certbot /usr/bin/certbot

RUN mkdir -p /var/log/client-side-logs/ &&\
	touch /var/log/client-side-logs/client-side.log &&\
	chmod 777 /var/log/client-side-logs/client-side.log &&\
	ln -s /usr/local/apache2/htdocs/client_side_logging /usr/lib/python3*/site-packages/ 

RUN pip install Flask pyyaml==5.4.1 mod_wsgi

# Rename and move mod_wsgi module to apache2 modules
RUN mv /usr/lib/python*/site-packages/mod_wsgi/server/mod_wsgi-*.so /usr/local/apache2/modules/mod_wsgi.so
