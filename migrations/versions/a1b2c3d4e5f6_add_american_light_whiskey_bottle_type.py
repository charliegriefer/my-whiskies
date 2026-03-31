"""Add American Light Whiskey bottle type

Revision ID: a1b2c3d4e5f6
Revises: de2d54c2ccab
Create Date: 2026-03-30 00:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "a1b2c3d4e5f6"
down_revision = "de2d54c2ccab"
branch_labels = None
depends_on = None


def upgrade():
    # Modify the ENUM type to include the new value
    op.execute(
        "alter table bottle modify column `type` ENUM('AMERICAN_LIGHT_WHISKEY', 'AMERICAN_SINGLE_MALT', 'AMERICAN_WHISKEY', 'BOURBON', 'CANADIAN_WHISKEY', 'IRISH_WHISKEY', 'RYE', 'SCOTCH', 'TENNESSEE_WHISKEY', 'WORLD_WHISKEY', 'OTHER') not null;"
    )


def downgrade():
    # Revert the ENUM type to its previous state
    op.execute(
        "alter table bottle modify column `type` ENUM('AMERICAN_SINGLE_MALT', 'AMERICAN_WHISKEY', 'BOURBON', 'CANADIAN_WHISKEY', 'IRISH_WHISKEY', 'RYE', 'SCOTCH', 'TENNESSEE_WHISKEY', 'WORLD_WHISKEY', 'OTHER') not null;"
    )
