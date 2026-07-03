FROM mysql:8.0.44-debian

COPY 00-load-timezones.sh /docker-entrypoint-initdb.d/
COPY schemas.sql /docker-entrypoint-initdb.d/