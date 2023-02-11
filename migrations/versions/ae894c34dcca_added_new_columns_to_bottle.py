"""Added new columns to bottle

Revision ID: ae894c34dcca
Revises: 3649eef66fce
Create Date: 2023-02-04 21:28:46.835431

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ae894c34dcca'
down_revision = '3649eef66fce'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('bottle', schema=None) as batch_op:
        batch_op.add_column(sa.Column('url', sa.String(length=64), nullable=True))
        batch_op.add_column(sa.Column('cost', sa.Float(), nullable=True))
        batch_op.add_column(sa.Column('date_purchased', sa.DateTime(), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('bottle', schema=None) as batch_op:
        batch_op.drop_column('date_purchased')
        batch_op.drop_column('cost')
        batch_op.drop_column('url')

    # ### end Alembic commands ###
