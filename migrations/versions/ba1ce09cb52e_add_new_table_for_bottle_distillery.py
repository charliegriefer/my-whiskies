"""Add new table for bottle/distillery

Revision ID: ba1ce09cb52e
Revises: 78044ef0c540
Create Date: 2024-06-27 17:16:47.988767

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table


# revision identifiers, used by Alembic.
revision = 'ba1ce09cb52e'
down_revision = '78044ef0c540'
branch_labels = None
depends_on = None


def upgrade():
    # create the bottle_distillery table
    op.create_table('bottle_distillery',
        sa.Column('bottle_id', sa.String(length=36), nullable=False),
        sa.Column('distillery_id', sa.String(length=36), nullable=False),
        sa.ForeignKeyConstraint(['bottle_id'], ['bottle.id'], ),
        sa.ForeignKeyConstraint(['distillery_id'], ['distillery.id'], ),
        sa.PrimaryKeyConstraint('bottle_id', 'distillery_id')
    )

    bottle_data = sa.table("bottle",
        sa.Column("id", sa.String(length=36)),
        sa.Column("distillery_id", sa.String(length=36))
    )
    bd = sa.table("bottle_distillery",
        sa.Column("bottle_id", sa.String(length=36)),
        sa.Column("distillery_id", sa.String(length=36))
    )

    conn = op.get_bind()
    res = conn.execute(sa.select(bottle_data.c.id, bottle_data.c.distillery_id))

    for (bottle_id, distillery_id) in res.fetchall():
        conn.execute(sa.insert(bd).values(bottle_id=bottle_id, distillery_id=distillery_id))

    op.drop_constraint("bottle_ibfk_1", "bottle", type_="foreignkey")
    op.drop_column("bottle", "distillery_id")


def downgrade():
    # add the distillery_id column back to the bottle table
    # op.add_column("bottle", sa.Column("distillery_id", sa.String(length=36), nullable=False))

    # # populate the distillery_id column from the join table (assuming only one distillery per bottle for downgrade)
    # jt = sa.table('bottle_distillery',
    #     sa.Column('bottle_id', sa.Integer),
    #     sa.Column('distillery_id', sa.Integer)
    # )

    # conn = op.get_bind()
    # res = conn.execute(sa.select(jt.c.bottle_id, jt.c.distillery_id).distinct(jt.c.bottle_id))

    # for (bottle_id, distillery_id) in res.fetchall():
    #     update_stmt = sa.update(bottle).where(bottle.c.id == bottle_id).values(distillery_id=distillery_id)
    #     conn.execute(update_stmt)

    # op.add_constraint("bottle_ibfk_1", "bottle", type_="foreignkey")

    # drop the join table
    op.drop_table('bottle_distillery')
