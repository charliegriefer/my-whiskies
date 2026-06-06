from typing import Dict, Tuple

from flask import current_app

from mywhiskies.extensions import db
from mywhiskies.forms.barrel_picker import BarrelPickerAddForm, BarrelPickerEditForm
from mywhiskies.models import BarrelPicker, User

_SORT_FNS = {
    "name": lambda p: p.name.lower(),
    "bottles": lambda p: len(p.bottles),
}


def list_barrel_pickers(
    user: User,
    is_my_list: bool = False,
    q: str = "",
    sort: str = "name",
    direction: str = "asc",
    page: int = 1,
    per_page: int = 25,
) -> Dict:
    pickers = list(user.barrel_pickers)
    if q:
        pickers = [p for p in pickers if q.lower() in p.name.lower()]
    total = len(pickers)
    pickers.sort(key=_SORT_FNS.get(sort, _SORT_FNS["name"]), reverse=(direction == "desc"))
    total_pages = max(1, (total + per_page - 1) // per_page)
    page = min(page, total_pages)
    offset = (page - 1) * per_page
    return {
        "barrel_pickers": pickers[offset : offset + per_page],
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": total_pages,
    }


def add_barrel_picker(form: BarrelPickerAddForm, user: User) -> BarrelPicker:
    picker = BarrelPicker(user_id=user.id)
    form.populate_obj(picker)
    db.session.add(picker)
    db.session.commit()
    current_app.logger.info(f"{user.username} added barrel picker {picker.name}.")
    return picker


def edit_barrel_picker(form: BarrelPickerEditForm, picker: BarrelPicker) -> None:
    form.populate_obj(picker)
    db.session.add(picker)
    db.session.commit()
    current_app.logger.info(f"{picker.user.username} edited barrel picker {picker.name}.")


def delete_barrel_picker(user: User, picker: BarrelPicker) -> Tuple[bool, str]:
    if picker.user.id != user.id:
        return False, "Permission denied."
    name = picker.name
    picker.bottles = []
    db.session.delete(picker)
    db.session.commit()
    current_app.logger.info(f"{user.username} deleted barrel picker {name}.")
    return True, f'Barrel picker "{name}" has been successfully deleted.'
