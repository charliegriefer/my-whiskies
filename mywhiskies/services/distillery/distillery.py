import json
import os

from flask import Flask, Request, current_app, flash
from flask.wrappers import Response
from sqlalchemy import insert

from mywhiskies.extensions import db
from mywhiskies.forms.distillery import DistilleryAddForm, DistilleryEditForm
from mywhiskies.models import Distillery, User
from mywhiskies.services import utils


def bulk_add_distillery(user: User, app: Flask) -> None:
    json_file = os.path.join(app.static_folder, "data", "base_distilleries.json")

    with open(json_file, mode="r", encoding="utf-8") as f:
        data = json.load(f)

        base_distilleries = data.get("distilleries")
        for distillery in base_distilleries:
            distillery["user_id"] = user.id

        db.session.execute(insert(Distillery), base_distilleries)
        db.session.commit()


def list_distilleries(
    user: User, current_user: User, req: Request, entity_type: str
) -> Response:
    return utils.prep_datatable_entities(user, current_user, req, entity_type)


def add_distillery(form: DistilleryAddForm, user: User) -> None:
    distillery_in = Distillery(user_id=user.id)
    form.populate_obj(distillery_in)
    db.session.add(distillery_in)
    db.session.commit()
    current_app.logger.info(
        f"{user.username} added distillery {distillery_in.name} successfully."
    )
    flash(f'Distillery "{distillery_in.name}" has been successfully added.', "success")


def edit_distillery(form: DistilleryEditForm, distillery: Distillery) -> None:
    form.populate_obj(distillery)
    db.session.add(distillery)
    db.session.commit()
    current_app.logger.info(
        f"{distillery.user.username} edited distillery {distillery.name} successfully."
    )
    flash(f'Distillery "{distillery.name}" has been successfully updated.', "success")


def delete_distillery(user: User, distillery_id: str) -> None:
    distillery = db.get_or_404(Distillery, distillery_id)
    if distillery.user.id != user.id:
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
        current_app.logger.info(
            f"{user.username} deleted distillery {distillery.name} successfully."
        )
        flash(
            f'Distillery "{distillery.name}" has been successfully deleted.', "success"
        )


def get_distillery_detail(
    distillery: Distillery, req: Request, current_user: User
) -> Response:
    return utils.prep_datatable_bottles(distillery, current_user, req)
