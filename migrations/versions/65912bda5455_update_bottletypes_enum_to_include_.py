"""Update BottleTypes enum to include American Single Malt

Revision ID: 65912bda5455
Revises: 2510be709ec4
Create Date: 2024-12-29 05:48:01.967451

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "65912bda5455"
down_revision = "2510be709ec4"
branch_labels = None
depends_on = None


def upgrade():
    # Modify the ENUM type to include the new value
    op.execute(
        "alter table bottle modify column `type` ENUM('AMERICAN_SINGLE_MALT', 'AMERICAN_WHISKEY', 'BOURBON', 'CANADIAN_WHISKEY', 'IRISH_WHISKEY', 'RYE', 'SCOTCH', 'TENNESSEE_WHISKEY', 'WORLD_WHISKEY', 'OTHER') not null;"
    )


def downgrade():
    # Revert the ENUM type to its previous state
    op.execute(
        "alter table bottle modify column `type` ENUM('AMERICAN_WHISKEY', 'BOURBON', 'CANADIAN_WHISKEY', 'IRISH_WHISKEY', 'RYE', 'SCOTCH', 'TENNESSEE_WHISKEY', 'WORLD_WHISKEY', 'OTHER') not null;"
    )
