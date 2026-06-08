#!/usr/bin/env python3
"""Migrate data from local MySQL to PostgreSQL (RDS).

Usage on EC2:
    python3 scripts/migrate_mysql_to_pg.py <pg_password>

Prerequisites:
    1. flask db upgrade (run with PostgreSQL DATABASE_URL set) to create schema
    2. pip install psycopg2-binary (already in pyproject.toml)
"""
import sys

import MySQLdb
import MySQLdb.cursors
import psycopg2
import psycopg2.extras

MYSQL_HOST = "localhost"
MYSQL_USER = "charlie"
MYSQL_DB = "my-whiskies"

PG_HOST = "my-whiskies-db.cajbdipwrxli.us-west-1.rds.amazonaws.com"
PG_PORT = 5432
PG_DB = "mywhiskies"
PG_USER = "postgres"

# MySQL stores booleans as TINYINT(1); PostgreSQL needs actual bool values
BOOL_COLS = {
    "user": {"email_confirmed", "is_active", "is_pro", "is_private", "is_deleted"},
    "bottle": {"is_private", "is_single_barrel"},
}

# Insert order respects FK dependencies
TABLES = [
    "user",
    "user_login",
    "passkey_credential",
    "distillery",
    "bottler",
    "barrel_picker",
    "bottle",
    "bottle_image",
    "bottle_distillery",
]


def migrate(pg_password: str) -> None:
    mysql = MySQLdb.connect(host=MYSQL_HOST, user=MYSQL_USER, db=MYSQL_DB)
    pg = psycopg2.connect(
        host=PG_HOST,
        port=PG_PORT,
        dbname=PG_DB,
        user=PG_USER,
        password=pg_password,
        sslmode="require",
    )
    pg.autocommit = False

    my_cur = mysql.cursor(MySQLdb.cursors.DictCursor)
    pg_cur = pg.cursor()

    for table in TABLES:
        print(f"  {table}...", end=" ", flush=True)

        my_cur.execute(f"SELECT * FROM `{table}`")
        rows = my_cur.fetchall()

        if not rows:
            print("(empty)")
            continue

        cols = list(rows[0].keys())
        bool_set = BOOL_COLS.get(table, set())
        quoted = f'"{table}"'
        col_list = ", ".join(f'"{c}"' for c in cols)
        placeholders = ", ".join(["%s"] * len(cols))
        sql = f"INSERT INTO {quoted} ({col_list}) VALUES ({placeholders})"

        for row in rows:
            values = []
            for col, val in row.items():
                if col in bool_set and val is not None:
                    val = bool(val)
                elif isinstance(val, (bytes, bytearray)):
                    val = psycopg2.Binary(bytes(val))
                values.append(val)
            pg_cur.execute(sql, values)

        pg.commit()
        print(f"{len(rows)} rows")

    my_cur.close()
    pg_cur.close()
    mysql.close()
    pg.close()
    print("\nDone.")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 migrate_mysql_to_pg.py <pg_password>")
        sys.exit(1)
    print("Starting migration...\n")
    migrate(sys.argv[1])
