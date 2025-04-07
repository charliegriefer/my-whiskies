"""
Utility script to populate the bottle_image table from existing S3 images.
Run this script to fix missing bottle image records in production.

Usage:
    flask shell
    exec(open('populate_bottle_images.py').read())
"""

import re
import uuid
from datetime import datetime

import boto3
from flask import current_app

from mywhiskies.blueprints.bottle.models import Bottle, BottleImage
from mywhiskies.extensions import db

# Get S3 configuration from app config
s3_bucket = current_app.config["BOTTLE_IMAGE_S3_BUCKET"]
s3_key_prefix = current_app.config["BOTTLE_IMAGE_S3_KEY"]
print(f"Using S3 bucket: {s3_bucket}")
print(f"Using S3 key prefix: {s3_key_prefix}")

# For production, we need to use the prod/ prefix
if s3_key_prefix == "dev":
    print("Development environment detected.")
else:
    # Use prod/ prefix for production
    s3_key_prefix = "prod"
    print(f"Production environment detected, using prefix: {s3_key_prefix}")

# Connect to S3
s3 = boto3.client("s3")

# Check current state
existing_images = db.session.query(BottleImage).count()
print(f"Current bottle_image records: {existing_images}")

# List objects in S3
try:
    print(f"Listing objects in s3://{s3_bucket}/{s3_key_prefix}/")
    response = s3.list_objects_v2(Bucket=s3_bucket, Prefix=f"{s3_key_prefix}/")

    if "Contents" not in response:
        print("No objects found in S3 bucket with specified prefix")
    else:
        print(f"Found {len(response['Contents'])} objects")

        # Count of images processed
        processed = 0
        errors = 0

        # Process each object
        for obj in response["Contents"]:
            try:
                # Parse bottle ID and sequence from key
                if match := re.match(
                    rf"{s3_key_prefix}/([a-f0-9-]+)_(\d+)\.png", obj["Key"]
                ):
                    bottle_id, sequence = match.groups()

                    # Check if bottle exists
                    bottle = db.session.query(Bottle).filter_by(id=bottle_id).first()
                    if not bottle:
                        print(
                            f"  - Skipping {obj['Key']}: Bottle {bottle_id} not found"
                        )
                        continue

                    # Check if record already exists
                    existing = (
                        db.session.query(BottleImage)
                        .filter_by(bottle_id=bottle_id, sequence=int(sequence))
                        .first()
                    )

                    if existing:
                        print(f"  - Record already exists for {obj['Key']}")
                        continue

                    # Create new record
                    db.session.add(
                        BottleImage(
                            id=str(uuid.uuid4()),
                            bottle_id=bottle_id,
                            sequence=int(sequence),
                            created_at=datetime.utcnow(),
                        )
                    )
                    processed += 1

                    # Commit in batches of 10
                    if processed % 10 == 0:
                        db.session.commit()
                        print(f"  - Processed {processed} images so far")
            except Exception as e:
                print(f"  - Error processing {obj['Key']}: {str(e)}")
                errors += 1

        # Final commit
        db.session.commit()

        # Final stats
        print(f"Processed {processed} images with {errors} errors")
        print(
            f"Current bottle_image records after import: {db.session.query(BottleImage).count()}"
        )
except Exception as e:
    print(f"Error: {str(e)}")
    # Rollback if needed
    db.session.rollback()
