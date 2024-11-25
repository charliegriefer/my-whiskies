"""Add is_private column to bottle table

Revision ID: b86e11264893
Revises: fb1cec87b5fe
Create Date: 2024-11-20 03:06:32.883017

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b86e11264893'
down_revision = 'fb1cec87b5fe'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('bottle', schema=None) as batch_op:
        batch_op.add_column(sa.Column('is_private', sa.Boolean(), server_default=sa.text('false'), nullable=False))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('bottle', schema=None) as batch_op:
        batch_op.drop_column('is_private')

    # ### end Alembic commands ###