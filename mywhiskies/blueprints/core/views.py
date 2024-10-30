import time

from flask import Blueprint, make_response, render_template, request
from flask_login import current_user
from sqlalchemy import select
from sqlalchemy.sql.expression import func

from mywhiskies.blueprints.bottle.models import Bottle
from mywhiskies.blueprints.distillery.models import Distillery
from mywhiskies.blueprints.user.models import User
from mywhiskies.extensions import db

core = Blueprint("core", __name__, template_folder="templates")


@core.route("/")
@core.route("/index", strict_slashes=False)
def index():
    user_count = db.session.execute(
        select(func.count(User.id)).where(User.email_confirmed == 1)
    ).scalar()
    distillery_count = db.session.execute(
        select(func.count(Distillery.name.distinct()))
    ).scalar()
    bottle_count = db.session.execute(select(func.count(Bottle.id))).scalar()
    pic_count = db.session.execute(select(func.sum(Bottle.image_count))).scalar()
    bottle_type_counts = db.session.execute(
        select(Bottle.type, func.count(Bottle.type))
        .group_by(Bottle.type)
        .order_by(func.count(Bottle.type).desc())
    ).all()

    return render_template(
        "core/index.html",
        title="My Whiskies Online",
        has_datatable=True,
        user_count=user_count,
        distillery_count=distillery_count,
        bottle_count=bottle_count,
        pic_count=pic_count,
        bottle_type_counts=bottle_type_counts,
    )


@core.route("/<string:username>", endpoint="home")
def home(username: str):
    cookie_exists = request.cookies.get("my-whiskies-user", None)
    if current_user.is_authenticated:
        user = current_user
        is_my_home = current_user.username.lower() == username.lower()
    else:
        user = db.one_or_404(db.select(User).filter_by(username=username))
        is_my_home = False
    live_bottles = [bottle for bottle in user.bottles if bottle.date_killed is None]
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


@core.route("/terms")
def terms():
    return render_template("core/tos.html")


@core.route("/privacy")
def privacy():
    return render_template("core/tos_privacy.html")


@core.route("/cookies")
def cookies():
    return render_template("core/tos_cookies.html")
