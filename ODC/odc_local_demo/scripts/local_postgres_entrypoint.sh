#!/usr/bin/env bash
set -euo pipefail

POSTGRES_DB="${POSTGRES_DB:-postgres}"
POSTGRES_USER="${POSTGRES_USER:-postgres}"
POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-postgres}"
PGDATA="${PGDATA:-/var/lib/postgresql/data}"

PG_MAJOR="$(find /usr/lib/postgresql -mindepth 1 -maxdepth 1 -type d -printf '%f\n' | sort -V | tail -n 1)"
PG_BIN="/usr/lib/postgresql/${PG_MAJOR}/bin"

mkdir -p "${PGDATA}"
chown -R postgres:postgres "${PGDATA}"
chmod 700 "${PGDATA}"

if [ ! -s "${PGDATA}/PG_VERSION" ]; then
  runuser -u postgres -- "${PG_BIN}/initdb" \
    -D "${PGDATA}" \
    --auth-local=trust \
    --auth-host=scram-sha-256

  {
    echo "listen_addresses = '*'"
    echo "password_encryption = 'scram-sha-256'"
  } >> "${PGDATA}/postgresql.conf"

  echo "host all all all scram-sha-256" >> "${PGDATA}/pg_hba.conf"
fi

runuser -u postgres -- "${PG_BIN}/pg_ctl" -D "${PGDATA}" -w start

runuser -u postgres -- "${PG_BIN}/psql" --username postgres --dbname postgres -v ON_ERROR_STOP=1 <<-EOSQL
  DO \$\$
  BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = '${POSTGRES_USER}') THEN
      CREATE ROLE "${POSTGRES_USER}" LOGIN SUPERUSER PASSWORD '${POSTGRES_PASSWORD}';
    ELSE
      ALTER ROLE "${POSTGRES_USER}" WITH LOGIN SUPERUSER PASSWORD '${POSTGRES_PASSWORD}';
    END IF;
  END
  \$\$;

  SELECT 'CREATE DATABASE "${POSTGRES_DB}" OWNER "${POSTGRES_USER}"'
  WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = '${POSTGRES_DB}')\gexec
EOSQL

runuser -u postgres -- "${PG_BIN}/pg_ctl" -D "${PGDATA}" -m fast -w stop

exec runuser -u postgres -- "${PG_BIN}/postgres" -D "${PGDATA}"
