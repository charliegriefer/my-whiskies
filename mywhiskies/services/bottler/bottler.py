from flask import flash, make_response, render_template
from flask.wrappers import Response
from werkzeug.local import LocalProxy

from mywhiskies.blueprints.bottler.forms import BottlerAddForm, BottlerEditForm
from mywhiskies.blueprints.bottler.models import Bottler
from mywhiskies.blueprints.user.models import User
from mywhiskies.extensions import db
from mywhiskies.services import utils


def list_bottlers(user: User, current_user: User) -> Response:
    response = make_response(
        render_template(
            "bottler/bottler_list.html",
            title=f"{user.username}'s Whiskies: Bottlers",
            has_datatable=True,
            is_my_list=utils.is_my_list(user.username, current_user),
            user=user,
            dt_list_length=50,
        )
    )
    return response


def add_bottler(form: BottlerAddForm, user: User) -> None:
    bottler_in = Bottler(user_id=user.id)
    form.populate_obj(bottler_in)
    db.session.add(bottler_in)
    db.session.commit()
    flash(f'"{bottler_in.name}" has been successfully added.', "success")


def edit_bottler(form: BottlerEditForm, bottler: Bottler) -> None:
    form.populate_obj(bottler)
    db.session.commit()
    flash(f'"{bottler.name}" has been successfully updated.', "success")


def delete_bottler(user: User, bottler_id: str) -> None:
    user_bottlers = [b.id for b in user.bottlers]
    if bottler_id not in user_bottlers:
        flash("There was an issue deleting this bottler.", "danger")
        return

    bottler = db.get_or_404(Bottler, bottler_id)
    if bottler.bottles:
        flash(
            f'Cannot delete "{bottler.name}", it has bottles associated.',
            "danger",
        )
    else:
        db.session.delete(bottler)
        db.session.commit()
        flash(f'"{bottler.name}" has been successfully deleted.', "success")


def get_bottler_detail(
    bottler: Bottler, request: LocalProxy, current_user: User
) -> Response:
    return utils.prep_datatables(bottler, current_user, request)

    # bottler = db.get_or_404(Bottler, bottler_id)
    # bottles = bottler.bottles
    # live_bottles = [bottle for bottle in bottles if bottle.date_killed is None]
    # if request.method == "POST" and bool(int(request.form.get("random_toggle"))):
    #     bottles_to_list = [random.choice(live_bottles)] if live_bottles else []
    #     has_killed_bottles = False
    # else:
    #     bottles_to_list = bottles
    #     has_killed_bottles = any(b.date_killed for b in bottles)

    # context = {
    #     "title": f"{bottler.user.username}'s Whiskies: {bottler.name}",
    #     "has_datatable": True,
    #     "user": bottler.user,
    #     "is_my_list": utils.is_my_list(bottler.user.username, current_user),
    #     "bottler": bottler,
    #     "bottles": bottles_to_list,
    #     "live_bottles": live_bottles,
    #     "has_killed_bottles": has_killed_bottles,
    #     "dt_list_length": request.cookies.get("dt-list-length", "50"),
    # }

    # return context
