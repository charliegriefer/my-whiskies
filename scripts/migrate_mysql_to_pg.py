#!/usr/bin/env python3
"""Migrate data from local MySQL to PostgreSQL.

Usage:
    # Local (no passwords needed if MySQL has no password):
    python3 scripts/migrate_mysql_to_pg.py

    # RDS (pg_password required):
    python3 scripts/migrate_mysql_to_pg.py --pg-password <pw> [--mysql-password <pw>]
    python3 scripts/migrate_mysql_to_pg.py --rds

Prerequisites:
    1. Create the schema first: python3 -c "from mywhiskies.app import create_app; ..."
    2. flask db stamp head
"""

import argparse

import MySQLdb
import MySQLdb.cursors
import psycopg2
import psycopg2.extras

MYSQL_HOST = "localhost"
MYSQL_USER = "charlie"
MYSQL_DB = "my-whiskies"

PG_HOST_LOCAL = "localhost"
PG_HOST_RDS = "my-whiskies-db.cajbdipwrxli.us-west-1.rds.amazonaws.com"
PG_PORT = 5432
PG_DB = "mywhiskies"
PG_USER_LOCAL = None  # uses OS user
PG_USER_RDS = "postgres"

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


def migrate(
    pg_host: str,
    pg_user: str | None,
    pg_password: str,
    pg_sslmode: str,
    mysql_password: str = "",
    mysql_user: str = MYSQL_USER,
) -> None:
    mysql = MySQLdb.connect(host=MYSQL_HOST, user=mysql_user, passwd=mysql_password, db=MYSQL_DB)
    pg_kwargs = dict(host=pg_host, port=PG_PORT, dbname=PG_DB, sslmode=pg_sslmode)
    if pg_user:
        pg_kwargs["user"] = pg_user
    if pg_password:
        pg_kwargs["password"] = pg_password
    pg = psycopg2.connect(**pg_kwargs)
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
    parser = argparse.ArgumentParser()
    parser.add_argument("--rds", action="store_true", help="Target RDS instead of local PostgreSQL")
    parser.add_argument("--pg-password", default="", help="PostgreSQL password (required for RDS)")
    parser.add_argument("--mysql-user", default=MYSQL_USER, help=f"MySQL username (default: {MYSQL_USER})")
    parser.add_argument("--mysql-password", default="", help="MySQL password if set")
    args = parser.parse_args()

    if args.rds:
        pg_host, pg_user, pg_sslmode = PG_HOST_RDS, PG_USER_RDS, "require"
    else:
        pg_host, pg_user, pg_sslmode = PG_HOST_LOCAL, PG_USER_LOCAL, "disable"

    print("Starting migration...\n")
    migrate(pg_host, pg_user, args.pg_password, pg_sslmode, args.mysql_password, args.mysql_user)
