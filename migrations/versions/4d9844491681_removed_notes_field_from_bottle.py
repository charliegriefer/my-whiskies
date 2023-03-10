"""Removed notes field from bottle

Revision ID: 4d9844491681
Revises: 09251ee1c984
Create Date: 2023-02-11 16:18:34.673887

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '4d9844491681'
down_revision = '09251ee1c984'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('bottle', schema=None) as batch_op:
        batch_op.drop_column('notes')

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('bottle', schema=None) as batch_op:
        batch_op.add_column(sa.Column('notes', mysql.TEXT(), nullable=True))

    # ### end Alembic commands ###
