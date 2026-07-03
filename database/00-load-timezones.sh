#!/bin/bash
set -e

mysql_tzinfo_to_sql /usr/share/zoneinfo 2>/dev/null \
  | mysql --protocol=socket -uroot -p"${MYSQL_ROOT_PASSWORD}" mysql

echo "[init] MySQL timezone tables loaded."
