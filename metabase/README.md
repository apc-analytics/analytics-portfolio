# Metabase — Local Setup

Runs Metabase Open Source in Docker, connecting to `db_portfolio` as a data
source. Metabase's own app data (dashboards, users, saved questions) is
stored in a local Docker volume via H2 — it does not need its own Postgres
database.

## Start Metabase
```
cd metabase
docker compose up -d
```
Open http://localhost:3000 and walk through first-run setup:

1. Create an admin account.
2. Add a database → PostgreSQL:
   - Host: `host.docker.internal` (Docker's bridge back to the host machine — `localhost` from inside the container refers to the container itself, not Windows)
   - Port: `5432`
   - Database name: `db_portfolio`
   - Username: `postgres`
   - Password: (your Postgres password)

## Stop Metabase
```
docker compose down
```

Dashboards and saved questions persist in the `metabase-data` volume between
restarts (only removed with `docker compose down -v`).