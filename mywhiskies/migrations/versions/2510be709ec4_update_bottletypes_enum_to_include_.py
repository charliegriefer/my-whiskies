"""Update BottleTypes enum to include Tennessee Whiskey

Revision ID: 2510be709ec4
Revises: ae075b14c2b8
Create Date: 2024-12-23 04:13:05.502766

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "2510be709ec4"
down_revision = "ae075b14c2b8"
branch_labels = None
depends_on = None


def upgrade():
    # Modify the ENUM type to include the new value
    op.execute(
        "alter table bottle modify column `type` ENUM('AMERICAN_WHISKEY', 'BOURBON', 'CANADIAN_WHISKEY', 'IRISH_WHISKEY', 'RYE', 'SCOTCH', 'TENNESSEE_WHISKEY', 'WORLD_WHISKEY', 'OTHER') not null;"
    )


def downgrade():
    # Revert the ENUM type to its previous state
    op.execute(
        "alter table bottle modify column `type` ENUM('american_whiskey', 'bourbon', 'canadian_whiskey', 'irish_whiskey', 'rye', 'scotch', 'world_whiskey', 'other') not null;"
    )
