"""Template for environment-aware migrations

This template demonstrates how to make migrations environment-aware,
especially when dealing with S3 resources that might have different
prefixes in different environments.

Usage: Copy relevant code snippets from this template when creating new migrations.
"""

import os
import re

import boto3
import sqlalchemy as sa
from alembic import op
from flask import current_app


def get_environment_config():
    """Get environment-specific configuration."""
    # Determine environment
    # Try to get from environment variable first
    env = os.environ.get("FLASK_ENV", "development")

    # Alternative approach using current_app if available
    try:
        if current_app and current_app.config:
            env = current_app.config.get("ENV", env)
    except Exception:
        pass

    # Map environment to S3 key prefix
    s3_config = {
        "development": {
            "bucket": "my-whiskies-pics",
            "key_prefix": "dev",
        },
        "production": {
            "bucket": "my-whiskies-pics",
            "key_prefix": "prod",
        },
        # Add other environments as needed
    }

    # Return environment-specific configuration
    config = s3_config.get(env, s3_config["development"])

    # Log configuration for debugging
    print(f"Environment: {env}")
    print(f"Using S3 bucket: {config['bucket']}")
    print(f"Using key prefix: {config['key_prefix']}")

    return config


def example_s3_migration_upgrade():
    """Example of how to use environment configuration in a migration."""
    # Create a new table example
    op.create_table(
        "example_table",
        sa.Column("id", sa.String(36), primary_key=True),
        # Add other columns as needed
    )

    # Get environment-specific configuration
    config = get_environment_config()
    bucket = config["bucket"]
    key_prefix = config["key_prefix"]

    # Connect to S3
    s3 = boto3.client("s3")

    try:
        # List objects in S3
        response = s3.list_objects_v2(Bucket=bucket, Prefix=f"{key_prefix}/")
        if "Contents" not in response:
            print("No objects found in S3")
            return

        # Process objects
        print(f"Found {len(response['Contents'])} objects in S3")
        processed = 0

        # Example of binding to the database connection
        conn = op.get_bind()

        # Process each object
        for obj in response["Contents"]:
            try:
                # Example pattern matching
                if match := re.match(
                    rf"{key_prefix}/([a-f0-9-]+)_(\d+)\.png", obj["Key"]
                ):
                    item_id, sequence = match.groups()

                    # Example database operation
                    conn.execute(
                        sa.text("INSERT INTO example_table (id) VALUES (:id)"),
                        {"id": item_id},
                    )
                    processed += 1
            except Exception as e:
                print(f"Error processing {obj['Key']}: {e}")

        print(f"Processed {processed} objects")

    except Exception as e:
        print(f"Error accessing S3: {e}")
        raise
