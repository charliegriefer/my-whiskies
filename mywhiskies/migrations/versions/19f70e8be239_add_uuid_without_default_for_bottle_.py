"""Remove default UUID for Bottle table ID

Revision ID: 19f70e8be239
Revises: 1a4eb1e3f498
Create Date: 2025-01-31 03:16:19.994827

"""

import sqlalchemy as sa
from alembic import op

# Revision identifiers, used by Alembic.
revision = "19f70e8be239"
down_revision = "1a4eb1e3f498"
branch_labels = None
depends_on = None


def upgrade():
    # Modify the `id` column in the `bottle` table to remove the default UUID
    with op.batch_alter_table("bottle", schema=None) as batch_op:
        batch_op.alter_column(
            "id",
            existing_type=sa.String(36),
            nullable=False,
            server_default=None,  # Explicitly remove the default
        )


def downgrade():
    # Restore the original column without setting a `server_default`
    with op.batch_alter_table("bottle", schema=None) as batch_op:
        batch_op.alter_column(
            "id",
            existing_type=sa.String(36),
            nullable=False,
        )
