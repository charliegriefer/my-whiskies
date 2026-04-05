import json
import os
from typing import Dict

from flask import Flask, current_app, flash
from sqlalchemy import insert

from mywhiskies.extensions import db
from mywhiskies.forms.distillery import DistilleryAddForm, DistilleryEditForm
from mywhiskies.models import Distillery, User

_SORT_FNS = {
    "name": lambda d: d.name.lower(),
    "bottles": lambda d: len(d.bottles),
    "location": lambda d: f"{d.region_1 or ''} {d.region_2 or ''}".lower(),
}


def bulk_add_distillery(user: User, app: Flask) -> None:
    json_file = os.path.join(app.static_folder, "data", "base_distilleries.json")

    with open(json_file, mode="r", encoding="utf-8") as f:
        data = json.load(f)

        base_distilleries = data.get("distilleries")
        for i, distillery in enumerate(base_distilleries, 1):
            distillery["user_id"] = user.id
            distillery["user_num"] = i

        db.session.execute(insert(Distillery), base_distilleries)
        db.session.commit()


def list_distilleries(
    user: User,
    is_my_list: bool,
    q: str = "",
    sort: str = "name",
    direction: str = "asc",
    page: int = 1,
    per_page: int = 25,
) -> Dict:
    distilleries = list(user.distilleries)

    if q:
        distilleries = [d for d in distilleries if q.lower() in d.name.lower()]

    total = len(distilleries)
    distilleries.sort(
        key=_SORT_FNS.get(sort, _SORT_FNS["name"]), reverse=(direction == "desc")
    )

    total_pages = max(1, (total + per_page - 1) // per_page)
    page = min(page, total_pages)
    offset = (page - 1) * per_page

    return {
        "distilleries": distilleries[offset : offset + per_page],
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": total_pages,
    }


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


def delete_distillery(user: User, distillery: Distillery) -> None:
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


