"""add bottle image table

Revision ID: 1a4eb1e3f498
Revises: 6c7916b59f10
Create Date: 2025-01-30 02:33:25.673374

"""

import re
import uuid
from datetime import datetime

import boto3
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic
revision = "1a4eb1e3f498"
down_revision = "6c7916b59f10"
branch_labels = None
depends_on = None


def upgrade():
    # Create bottle_image table
    op.create_table(
        "bottle_image",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("bottle_id", sa.String(36), sa.ForeignKey("bottle.id")),
        sa.Column("sequence", sa.Integer, nullable=False),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.UniqueConstraint("bottle_id", "sequence", name="_bottle_sequence_uc"),
    )

    # Process existing S3 images
    s3 = boto3.client("s3", region_name="us-west-1")
    bucket = "my-whiskies-pics"
    key_prefix = "dev"

    try:
        response = s3.list_objects_v2(Bucket=bucket, Prefix=f"{key_prefix}/")
        if "Contents" not in response:
            return

        # Map existing images to new table
        conn = op.get_bind()
        for obj in response["Contents"]:
            if match := re.match(rf"{key_prefix}/([a-f0-9-]+)_(\d+)\.png", obj["Key"]):
                bottle_id, sequence = match.groups()

                # Skip if bottle doesn't exist
                if not conn.execute(
                    sa.text("SELECT 1 FROM bottle WHERE id = :bottle_id"),
                    {"bottle_id": bottle_id},
                ).scalar():
                    continue

                conn.execute(
                    sa.text(
                        "INSERT INTO bottle_image (id, bottle_id, sequence, created_at) "
                        "VALUES (:id, :bottle_id, :sequence, :created_at)"
                    ),
                    {
                        "id": str(uuid.uuid4()),
                        "bottle_id": bottle_id,
                        "sequence": int(sequence),
                        "created_at": datetime.utcnow(),
                    },
                )
    except Exception:
        raise

    # Remove deprecated column
    op.drop_column("bottle", "image_count")


def downgrade():
    # Add image_count column back
    op.add_column(
        "bottle",
        sa.Column("image_count", sa.Integer, nullable=False, server_default="0"),
    )

    # Populate image_count from bottle_image records
    conn = op.get_bind()
    conn.execute(
        sa.text(
            "UPDATE bottle b SET image_count = "
            "(SELECT COUNT(*) FROM bottle_image bi WHERE bi.bottle_id = b.id)"
        )
    )

    # Drop bottle_image table
    op.drop_table("bottle_image")
