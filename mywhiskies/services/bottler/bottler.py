from flask import flash, request
from flask.wrappers import Response

from mywhiskies.blueprints.bottler.forms import BottlerAddForm, BottlerEditForm
from mywhiskies.blueprints.bottler.models import Bottler
from mywhiskies.blueprints.user.models import User
from mywhiskies.extensions import db
from mywhiskies.services import utils


def list_bottlers(
    user: User, current_user: User, request: request, entity_type: str
) -> Response:
    return utils.prep_datatable_entities(user, current_user, request, entity_type)


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
    bottler = db.get_or_404(Bottler, bottler_id)
    if bottler.user.id != user.id:
        flash("There was an issue deleting this bottler.", "danger")
        return

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
    bottler: Bottler, request: request, current_user: User
) -> Response:
    return utils.prep_datatable_bottles(bottler, current_user, request)
