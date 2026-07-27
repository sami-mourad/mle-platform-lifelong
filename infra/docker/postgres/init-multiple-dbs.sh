#!/usr/bin/env bash
set -euo pipefail

create_db() {
  local db="$1"
  psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname postgres <<-EOSQL
    SELECT 'CREATE DATABASE ${db}'
    WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = '${db}')\gexec
EOSQL
}

create_db "${MLFLOW_DB:-mlflow}"
create_db "${DAGSTER_DB:-dagster}"
