"""Increase length of URL field for bottle

Revision ID: 78044ef0c540
Revises: d7a2212a501d
Create Date: 2024-02-09 16:54:29.717152

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '78044ef0c540'
down_revision = 'd7a2212a501d'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('bottle', schema=None) as batch_op:
        batch_op.alter_column('url',
               existing_type=mysql.VARCHAR(length=64),
               type_=sa.String(length=140),
               existing_nullable=True)

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('bottle', schema=None) as batch_op:
        batch_op.alter_column('url',
               existing_type=sa.String(length=140),
               type_=mysql.VARCHAR(length=64),
               existing_nullable=True)

    # ### end Alembic commands ###
