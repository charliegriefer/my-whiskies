import re

import boto3
import click
from flask import current_app
from flask.cli import with_appcontext

from mywhiskies.extensions import db
from mywhiskies.models import Bottle
from mywhiskies.services.user.cleanup import delete_inactive_users, warn_inactive_users


@click.command("cleanup-inactive-users")
@with_appcontext
def cleanup_inactive_users_command():
    """Warn inactive users and delete those past the grace period."""
    base_url = current_app.config.get("BASE_URL", "https://my-whiskies.online")
    with current_app.test_request_context(base_url=base_url):
        warned = warn_inactive_users()
        deleted = delete_inactive_users()
    current_app.logger.info(f"Inactive user cleanup complete: {warned} warned, {deleted} deleted.")
    click.echo(f"Warned: {warned}  Deleted: {deleted}")


@click.command("audit-orphaned-images")
@click.option("--delete", is_flag=True, default=False, help="Delete orphaned images from S3.")
@with_appcontext
def audit_orphaned_images_command(delete):
    """Report (and optionally delete) S3 images with no matching bottle in the DB."""
    bucket = current_app.config["BOTTLE_IMAGE_S3_BUCKET"]
    prefixes = [
        current_app.config["BOTTLE_IMAGE_S3_KEY"],
        current_app.config["BOTTLE_IMAGE_FULL_S3_KEY"],
    ]

    valid_ids = {str(row[0]) for row in db.session.execute(db.select(Bottle.id)).all()}

    s3 = boto3.client("s3")
    pattern = re.compile(r"^[^/]+/([^_]+)_")

    orphans = []
    for prefix in prefixes:
        paginator = s3.get_paginator("list_objects_v2")
        for page in paginator.paginate(Bucket=bucket, Prefix=f"{prefix}/"):
            for obj in page.get("Contents", []):
                key = obj["Key"]
                m = pattern.match(key)
                if m and m.group(1) not in valid_ids:
                    orphans.append(key)

    if not orphans:
        click.echo("No orphaned images found.")
        return

    click.echo(f"Found {len(orphans)} orphaned image(s):")
    for key in orphans:
        click.echo(f"  {key}")

    if delete:
        click.echo("\nDeleting...")
        for key in orphans:
            s3.delete_object(Bucket=bucket, Key=key)
            click.echo(f"  Deleted: {key}")
        click.echo(f"\nDeleted {len(orphans)} orphaned image(s).")
    else:
        click.echo("\nRun with --delete to remove them.")
