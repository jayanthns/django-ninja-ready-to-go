#!/bin/bash

set -e

host=""
user="$POSTGRES_USER"
dbname="$POSTGRES_DB"
schema="$DB_SCHEMA"

# Wait for PostgreSQL to be available
until PGPASSWORD=$POSTGRES_PASSWORD psql -h "$host" -U "$user" -d "$dbname" -c '\q'; do
  >&2 echo "Postgres is unavailable - sleeping"
  sleep 1
done

>&2 echo "Postgres is up - executing schema creation"

# Check if the schema exists and is not "public"
schema_exists=$(PGPASSWORD=$POSTGRES_PASSWORD psql -h "$host" -U "$user" -d "$dbname" -t -c "SELECT schema_name FROM information_schema.schemata WHERE schema_name = '$schema';")

if [[ "$schema_exists" != "$schema" && "$schema" != "public" ]]; then
  # Create schema if it doesn't exist and is not public
  PGPASSWORD=$POSTGRES_PASSWORD psql -h "$host" -U "$user" -d "$dbname" -c "CREATE SCHEMA IF NOT EXISTS $schema;"
  >&2 echo "Schema $schema created successfully"
else
  >&2 echo "Schema $schema already exists or it's the public schema. Skipping creation."
fi
