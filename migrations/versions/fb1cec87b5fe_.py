"""empty message

Revision ID: fb1cec87b5fe
Revises: 95e171c46024
Create Date: 2024-11-19 10:17:28.922867

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "fb1cec87b5fe"
down_revision = "95e171c46024"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("bottle", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "is_private",
                sa.Boolean(),
                nullable=False,
                server_default=sa.sql.expression.false(),
            )
        )


def downgrade():
    with op.batch_alter_table("bottle", schema=None) as batch_op:
        batch_op.drop_column("is_private")
