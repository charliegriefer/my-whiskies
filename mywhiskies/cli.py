import click
from flask import current_app
from flask.cli import with_appcontext

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
