"""Add canadian_whiskey to types

Revision ID: 38e90bd9bc7b
Revises: d7a2212a501d
Create Date: 2023-10-09 12:01:24.759419

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '38e90bd9bc7b'
down_revision = 'd7a2212a501d'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('untitled_table_6')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('untitled_table_6',
    sa.Column('id', mysql.CHAR(length=1), nullable=True),
    sa.Column('year', mysql.INTEGER(), autoincrement=False, nullable=True),
    mysql_collate='utf8mb4_0900_ai_ci',
    mysql_default_charset='utf8mb4',
    mysql_engine='InnoDB'
    )
    # ### end Alembic commands ###
