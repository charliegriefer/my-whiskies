"""
Script to identify and optionally delete orphaned bottle images from S3.

Usage:
------
Dry Run (default - will NOT delete anything):
    PYTHONPATH=. FLASK_ENV=dev python scripts/clean_orphaned_bottle_images.py

Dry Run (production config):
    PYTHONPATH=. FLASK_ENV=production python scripts/clean_orphaned_bottle_images.py

Actual Deletion (nuke orphaned images):
    PYTHONPATH=. FLASK_ENV=dev python scripts/clean_orphaned_bottle_images.py --nuke

Actual Deletion (production config):
    PYTHONPATH=. FLASK_ENV=production python scripts/clean_orphaned_bottle_images.py --nuke

Environment Selection:
----------------------
The script uses FLASK_ENV to determine which configuration to use:
- FLASK_ENV=dev → uses DevConfig
- FLASK_ENV=production → uses ProdConfig

Note:
-----
- FLASK_ENV is deprecated in Flask 2.3+. Consider migrating to FLASK_DEBUG or FLASK_CONFIG in the future.
"""
import argparse
import os
import re

import boto3
from flask import Flask

from config import DevConfig, ProdConfig
from mywhiskies.extensions import db
from mywhiskies.models.bottle import Bottle
from mywhiskies.services.bottle.image import get_s3_config


def create_app():
    app = Flask(__name__)
    app.config.from_object(
        ProdConfig if os.getenv("FLASK_ENV") == "production" else DevConfig
    )
    db.init_app(app)
    return app


def clean_orphaned_images(app, dry_run=True):
    with app.app_context():
        bucket, prefix, _ = get_s3_config()
        valid_ids = {str(b.id) for b in db.session.execute(db.select(Bottle)).scalars()}

        s3 = boto3.client("s3")
        paginator = s3.get_paginator("list_objects_v2")
        orphaned_keys = []

        pattern = re.compile(rf"^{prefix}/([a-f0-9\-]+)_[123]\.png$", re.IGNORECASE)

        for page in paginator.paginate(Bucket=bucket, Prefix=prefix + "/"):
            for obj in page.get("Contents", []):
                key = obj["Key"]
                match = pattern.match(key)
                if match:
                    bottle_id = match.group(1)
                    if bottle_id not in valid_ids:
                        print(f"Orphaned image found: {key}")
                        orphaned_keys.append({"Key": key})

        if dry_run:
            print(
                f"\nDry run complete. {len(orphaned_keys)} orphaned images would be deleted."
            )
        else:
            for i in range(0, len(orphaned_keys), 1000):
                batch = orphaned_keys[i: i + 1000]
                print(f"Deleting {len(batch)} orphaned keys...")
                s3.delete_objects(Bucket=bucket, Delete={"Objects": batch})


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Clean orphaned bottle images from S3."
    )
    parser.add_argument(
        "--nuke", action="store_true", help="Actually delete orphaned images."
    )
    args = parser.parse_args()

    app = create_app()
    clean_orphaned_images(app, dry_run=not args.nuke)
