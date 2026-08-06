"""
APC Wellness — raw data loader.

Loads the five generated CSVs (accounts.csv, members.csv, plans.csv,
subscriptions.csv, workouts.csv) into db_portfolio's raw_apc_wellness
schema.

Convention (matching raw_noaa_weather_us in db_weather): every column is
loaded as TEXT, with no type casting here — that's dbt staging's job.
This keeps the loader simple and safely rerunnable: each run drops and
recreates every table fresh from the CSVs.

Connection settings come from environment variables so no password ever
ends up in a committed file:
    PGHOST     (default: localhost)
    PGPORT     (default: 5432)
    PGDATABASE (default: db_portfolio)
    PGUSER     (default: postgres)
    PGPASSWORD (prompted for securely if not set)

Usage:
    python load_apc_wellness.py --data-dir "path\\to\\folder\\with\\the\\five\\csvs"

Requires: psycopg2-binary  (pip install psycopg2-binary)
"""

import argparse
import csv
import getpass
import os
from pathlib import Path

import psycopg2

SCHEMA = "raw_apc_wellness"

# table_name -> csv filename
TABLES = {
    "accounts": "accounts.csv",
    "members": "members.csv",
    "plans": "plans.csv",
    "subscriptions": "subscriptions.csv",
    "workouts": "workouts.csv",
    "orders": "orders.csv",
    "support_tickets": "support_tickets.csv",
    "campaigns": "campaigns.csv",
    "account_acquisition": "account_acquisition.csv",
}


def get_connection():
    return psycopg2.connect(
        host=os.environ.get("PGHOST", "localhost"),
        port=os.environ.get("PGPORT", "5432"),
        dbname=os.environ.get("PGDATABASE", "db_portfolio"),
        user=os.environ.get("PGUSER", "postgres"),
        password=os.environ.get("PGPASSWORD") or getpass.getpass("Postgres password: "),
    )


def read_header(csv_path: Path):
    with open(csv_path, newline="", encoding="utf-8") as f:
        return next(csv.reader(f))


def load_table(conn, table_name: str, csv_path: Path):
    columns = read_header(csv_path)
    column_defs = ", ".join(f'"{c}" TEXT' for c in columns)

    with conn.cursor() as cur:
        cur.execute(f'DROP TABLE IF EXISTS {SCHEMA}."{table_name}" CASCADE;')
        cur.execute(f'CREATE TABLE {SCHEMA}."{table_name}" ({column_defs});')
        with open(csv_path, "r", newline="", encoding="utf-8") as f:
            cur.copy_expert(
                f'COPY {SCHEMA}."{table_name}" FROM STDIN WITH CSV HEADER',
                f,
            )
        cur.execute(f'SELECT COUNT(*) FROM {SCHEMA}."{table_name}";')
        count = cur.fetchone()[0]
    conn.commit()
    print(f"  {table_name}: {count} rows loaded")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", required=True, help="Folder containing the five generated CSVs")
    args = parser.parse_args()
    data_dir = Path(args.data_dir)

    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute(f"CREATE SCHEMA IF NOT EXISTS {SCHEMA};")
    conn.commit()

    print(f"Loading into schema '{SCHEMA}':")
    for table_name, filename in TABLES.items():
        csv_path = data_dir / filename
        if not csv_path.exists():
            print(f"  SKIPPED {table_name}: {csv_path} not found")
            continue
        load_table(conn, table_name, csv_path)

    conn.close()
    print("Done.")


if __name__ == "__main__":
    main()