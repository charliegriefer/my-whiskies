import time

from flask import make_response, render_template, request
from flask_login import current_user

from mywhiskies.blueprints.core import core_bp
from mywhiskies.services.core.core import (
    get_index_counts,
    get_live_bottles_for_user,
    get_user_by_username,
)


@core_bp.route("/")
@core_bp.route("/index", strict_slashes=False)
def index():
    counts = get_index_counts()

    return render_template(
        "core/index.html",
        title="My Whiskies Online",
        has_datatable=True,
        user_count=counts.get("user_count", 0),
        distillery_count=counts.get("distillery_count", 0),
        bottle_count=counts.get("bottle_count", 0),
        pic_count=counts.get("pic_count", 0),
        bottle_type_counts=counts.get("bottle_type_counts", []),
    )


@core_bp.route("/<string:username>", endpoint="home")
def home(username: str):
    cookie_exists = request.cookies.get("my-whiskies-user", None)
    user = get_user_by_username(username)
    is_my_home = (
        current_user.is_authenticated
        and current_user.username.lower() == username.lower()
    )
    live_bottles = get_live_bottles_for_user(user)

    response = make_response(
        render_template(
            "core/home.html",
            title=f"{user.username}'s Whiskies",
            has_datatable=False,
            user=user,
            live_bottles=live_bottles,
            is_my_home=is_my_home,
            cookie_exists=cookie_exists,
        )
    )
    if not cookie_exists:
        response.set_cookie("my-whiskies-user", str(time.time()))
    return response


@core_bp.route("/terms")
def terms():
    return render_template("core/tos.html")


@core_bp.route("/privacy")
def privacy():
    return render_template("core/tos_privacy.html")


@core_bp.route("/cookies")
def cookies():
    return render_template("core/tos_cookies.html")
