"""Update relationships

Revision ID: 33101a6ed7be
Revises: 96f9ba30b7e5
Create Date: 2023-03-18 20:04:16.306659

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '33101a6ed7be'
down_revision = '96f9ba30b7e5'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('bottle', schema=None) as batch_op:
        batch_op.alter_column('type',
               existing_type=mysql.ENUM('scotch', 'irish_whiskey', 'bourbon', 'rye', 'american_whiskey', 'world_whiskey', 'other'),
               type_=sa.Enum('american_whiskey', 'bourbon', 'irish_whiskey', 'rye', 'scotch', 'world_whiskey', 'other', name='bottletypes'),
               existing_nullable=True)

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('bottle', schema=None) as batch_op:
        batch_op.alter_column('type',
               existing_type=sa.Enum('american_whiskey', 'bourbon', 'irish_whiskey', 'rye', 'scotch', 'world_whiskey', 'other', name='bottletypes'),
               type_=mysql.ENUM('scotch', 'irish_whiskey', 'bourbon', 'rye', 'american_whiskey', 'world_whiskey', 'other'),
               existing_nullable=True)

    # ### end Alembic commands ###
