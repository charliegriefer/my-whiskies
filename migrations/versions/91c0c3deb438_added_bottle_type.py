"""added bottle type

Revision ID: 91c0c3deb438
Revises: ef7a774b4515
Create Date: 2023-02-03 22:04:55.583319

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '91c0c3deb438'
down_revision = 'ef7a774b4515'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('bottle', schema=None) as batch_op:
        batch_op.add_column(sa.Column('type', sa.Enum('scotch', 'bourbon', 'rye', 'american_whiskey', 'world_whiskey', 'other', name='bottletypes'), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('bottle', schema=None) as batch_op:
        batch_op.drop_column('type')

    # ### end Alembic commands ###
