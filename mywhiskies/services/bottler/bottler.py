from typing import Dict, List, Optional

from flask import current_app, flash

from mywhiskies.extensions import db
from mywhiskies.forms.bottler import BottlerAddForm, BottlerEditForm
from mywhiskies.models import Bottler, User

_SORT_FNS = {
    "name": lambda b: b.name.lower(),
    "bottles": lambda b: len(b.bottles),
    "location": lambda b: f"{b.region_1 or ''} {b.region_2 or ''}".lower(),
}


def list_bottlers(
    user: User,
    is_my_list: bool,
    q: str = "",
    sort: str = "name",
    direction: str = "asc",
    page: int = 1,
    per_page: int = 25,
) -> Dict:
    bottlers = list(user.bottlers)

    if q:
        bottlers = [b for b in bottlers if q.lower() in b.name.lower()]

    total = len(bottlers)
    bottlers.sort(key=_SORT_FNS.get(sort, _SORT_FNS["name"]), reverse=(direction == "desc"))

    total_pages = max(1, (total + per_page - 1) // per_page)
    page = min(page, total_pages)
    offset = (page - 1) * per_page

    return {
        "bottlers": bottlers[offset : offset + per_page],
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": total_pages,
    }


def add_bottler(form: BottlerAddForm, user: User) -> None:
    bottler_in = Bottler(user_id=user.id)
    form.populate_obj(bottler_in)
    db.session.add(bottler_in)
    db.session.commit()
    current_app.logger.info(
        f"{user.username} added bottler {bottler_in.name} successfully."
    )
    flash(f'"{bottler_in.name}" has been successfully added.', "success")


def edit_bottler(form: BottlerEditForm, bottler: Bottler) -> None:
    form.populate_obj(bottler)
    db.session.commit()
    current_app.logger.info(
        f"{bottler.user.username} edited bottler {bottler.name} successfully."
    )
    flash(f'"{bottler.name}" has been successfully updated.', "success")


def delete_bottler(user: User, bottler: Bottler) -> None:
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
        current_app.logger.info(
            f"{user.username} deleted bottle {bottler.name} successfully."
        )
        flash(f'"{bottler.name}" has been successfully deleted.', "success")


