"""Update some datatypes

Revision ID: 95e171c46024
Revises: ba1ce09cb52e
Create Date: 2024-08-24 17:39:53.762241

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = "95e171c46024"
down_revision = "ba1ce09cb52e"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table("bottle", schema=None) as batch_op:
        batch_op.alter_column(
            "type",
            existing_type=mysql.ENUM(
                "american_whiskey",
                "bourbon",
                "canadian_whiskey",
                "irish_whiskey",
                "rye",
                "scotch",
                "world_whiskey",
                "other",
            ),
            nullable=False,
        )
        batch_op.alter_column(
            "abv",
            existing_type=mysql.FLOAT(),
            type_=sa.Numeric(precision=6, scale=4),
            existing_nullable=True,
        )
        batch_op.alter_column(
            "stars",
            existing_type=mysql.FLOAT(),
            type_=sa.Numeric(precision=2, scale=1),
            existing_nullable=True,
        )
        batch_op.alter_column(
            "cost",
            existing_type=mysql.FLOAT(),
            type_=sa.Numeric(precision=8, scale=2),
            existing_nullable=True,
        )
        batch_op.alter_column(
            "image_count", existing_type=mysql.INTEGER(), nullable=False
        )

    with op.batch_alter_table("bottler", schema=None) as batch_op:
        batch_op.alter_column(
            "user_id", existing_type=mysql.VARCHAR(length=36), nullable=False
        )

    with op.batch_alter_table("distillery", schema=None) as batch_op:
        batch_op.alter_column(
            "user_id", existing_type=mysql.VARCHAR(length=36), nullable=False
        )

    with op.batch_alter_table("user", schema=None) as batch_op:
        batch_op.alter_column(
            "username", existing_type=mysql.VARCHAR(length=64), nullable=False
        )
        batch_op.alter_column(
            "email", existing_type=mysql.VARCHAR(length=120), nullable=False
        )
        batch_op.alter_column(
            "password_hash", existing_type=mysql.VARCHAR(length=128), nullable=False
        )

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table("user", schema=None) as batch_op:
        batch_op.alter_column(
            "password_hash", existing_type=mysql.VARCHAR(length=128), nullable=True
        )
        batch_op.alter_column(
            "email", existing_type=mysql.VARCHAR(length=120), nullable=True
        )
        batch_op.alter_column(
            "username", existing_type=mysql.VARCHAR(length=64), nullable=True
        )

    with op.batch_alter_table("distillery", schema=None) as batch_op:
        batch_op.alter_column(
            "user_id", existing_type=mysql.VARCHAR(length=36), nullable=True
        )

    with op.batch_alter_table("bottler", schema=None) as batch_op:
        batch_op.alter_column(
            "user_id", existing_type=mysql.VARCHAR(length=36), nullable=True
        )

    with op.batch_alter_table("bottle", schema=None) as batch_op:
        batch_op.alter_column(
            "image_count", existing_type=mysql.INTEGER(), nullable=True
        )
        batch_op.alter_column(
            "cost",
            existing_type=sa.Numeric(precision=8, scale=2),
            type_=mysql.FLOAT(),
            existing_nullable=True,
        )
        batch_op.alter_column(
            "stars",
            existing_type=sa.Numeric(precision=2, scale=1),
            type_=mysql.FLOAT(),
            existing_nullable=True,
        )
        batch_op.alter_column(
            "abv",
            existing_type=sa.Numeric(precision=6, scale=4),
            type_=mysql.FLOAT(),
            existing_nullable=True,
        )
        batch_op.alter_column(
            "type",
            existing_type=mysql.ENUM(
                "american_whiskey",
                "bourbon",
                "canadian_whiskey",
                "irish_whiskey",
                "rye",
                "scotch",
                "world_whiskey",
                "other",
            ),
            nullable=True,
        )

    # ### end Alembic commands ###
