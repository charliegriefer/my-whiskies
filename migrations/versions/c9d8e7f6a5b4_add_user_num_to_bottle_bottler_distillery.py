"""Add user_num to bottle, bottler, and distillery tables

Revision ID: c9d8e7f6a5b4
Revises: a1b2c3d4e5f6
Create Date: 2026-03-30 00:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "c9d8e7f6a5b4"
down_revision = "a1b2c3d4e5f6"
branch_labels = None
depends_on = None


def upgrade():
    # Add nullable user_num columns
    op.add_column("bottle", sa.Column("user_num", sa.Integer(), nullable=True))
    op.add_column("bottler", sa.Column("user_num", sa.Integer(), nullable=True))
    op.add_column("distillery", sa.Column("user_num", sa.Integer(), nullable=True))

    # Backfill: assign sequential numbers per user ordered by date_created
    op.execute("""
        UPDATE bottle b
        JOIN (
            SELECT id, ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY date_created) AS rn
            FROM bottle
        ) ranked ON b.id = ranked.id
        SET b.user_num = ranked.rn
    """)
    op.execute("""
        UPDATE bottler b
        JOIN (
            SELECT id, ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY id) AS rn
            FROM bottler
        ) ranked ON b.id = ranked.id
        SET b.user_num = ranked.rn
    """)
    op.execute("""
        UPDATE distillery d
        JOIN (
            SELECT id, ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY id) AS rn
            FROM distillery
        ) ranked ON d.id = ranked.id
        SET d.user_num = ranked.rn
    """)

    # Make NOT NULL
    op.execute("ALTER TABLE bottle MODIFY COLUMN user_num INT NOT NULL")
    op.execute("ALTER TABLE bottler MODIFY COLUMN user_num INT NOT NULL")
    op.execute("ALTER TABLE distillery MODIFY COLUMN user_num INT NOT NULL")

    op.create_unique_constraint("uq_bottle_user_num", "bottle", ["user_id", "user_num"])
    op.create_unique_constraint("uq_bottler_user_num", "bottler", ["user_id", "user_num"])
    op.create_unique_constraint("uq_distillery_user_num", "distillery", ["user_id", "user_num"])


def downgrade():
    op.drop_constraint("uq_bottle_user_num", "bottle", type_="unique")
    op.drop_constraint("uq_bottler_user_num", "bottler", type_="unique")
    op.drop_constraint("uq_distillery_user_num", "distillery", type_="unique")

    op.drop_column("bottle", "user_num")
    op.drop_column("bottler", "user_num")
    op.drop_column("distillery", "user_num")
