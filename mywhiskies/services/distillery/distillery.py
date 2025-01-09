from flask import flash, request
from flask.wrappers import Response

from mywhiskies.blueprints.distillery.forms import DistilleryEditForm, DistilleryForm
from mywhiskies.blueprints.distillery.models import Distillery
from mywhiskies.blueprints.user.models import User
from mywhiskies.extensions import db
from mywhiskies.services import utils


def list_distilleries(
    user: User, current_user: User, request: request, entity_type: str
) -> Response:
    return utils.prep_datatable_entities(user, current_user, request, entity_type)


def add_distillery(form: DistilleryForm, user: User) -> None:
    distillery_in = Distillery(user_id=user.id)
    form.populate_obj(distillery_in)
    db.session.add(distillery_in)
    db.session.commit()
    flash(f'Distillery "{distillery_in.name}" has been successfully added.', "success")


def edit_distillery(form: DistilleryEditForm, distillery: Distillery) -> None:
    form.populate_obj(distillery)
    db.session.add(distillery)
    db.session.commit()
    flash(f'Distillery "{distillery.name}" has been successfully updated.', "success")


def delete_distillery(distillery_id: str, current_user: User) -> None:
    distillery = db.get_or_404(Distillery, distillery_id)

    if distillery.user.id != current_user.id:
        flash("There was an issue deleting this distillery.", "danger")
        return

    if distillery.bottles:
        flash(
            f'Cannot delete "{distillery.name}", it has bottles associated.',
            "danger",
        )
    else:
        db.session.delete(distillery)
        db.session.commit()
        flash(
            f'Distillery "{distillery.name}" has been successfully deleted.', "success"
        )


def get_distillery_detail(
    distillery: Distillery, request: request, current_user: User
) -> Response:
    return utils.prep_datatable_bottles(distillery, current_user, request)
