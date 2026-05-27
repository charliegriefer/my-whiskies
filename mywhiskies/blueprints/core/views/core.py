from flask import render_template
from flask_login import current_user

from mywhiskies.blueprints.core import core_bp
from mywhiskies.services.core.changelog import get_releases
from mywhiskies.services.core.core import get_index_counts


@core_bp.route("/")
@core_bp.route("/main")
def main():
    counts = get_index_counts()
    title = "My Whiskies Online"

    if current_user.is_authenticated:
        title += f": {current_user.username}'s Whiskies"

    return render_template(
        "core/main.html",
        title=title,
        user_count=counts.get("user_count", 0),
        distillery_count=counts.get("distillery_count", 0),
        bottle_count=counts.get("bottle_count", 0),
        pic_count=counts.get("pic_count", 0),
        bottle_type_counts=counts.get("bottle_type_counts", []),
    )


@core_bp.route("/terms")
def terms():
    return render_template("core/tos.html")


@core_bp.route("/privacy")
def privacy():
    return render_template("core/tos_privacy.html")


@core_bp.route("/cookies")
def cookies():
    return render_template("core/tos_cookies.html")


@core_bp.route("/changelog")
def changelog():
    return render_template(
        "core/changelog.html",
        title="My Whiskies Online: Changelog",
        releases=get_releases(),
    )
