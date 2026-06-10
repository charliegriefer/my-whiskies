import random
from itertools import groupby
from typing import Dict, List, Optional, Union

from flask import current_app, flash, url_for
from markupsafe import Markup

from mywhiskies.extensions import db
from mywhiskies.forms.bottle import BottleAddForm, BottleEditForm
from mywhiskies.models import BarrelPicker, Bottle, Bottler, Distillery, User
from mywhiskies.services.bottle.image import (
    delete_bottle_images,
    process_bottle_images,
)


def _normalize(s: str) -> str:
    """Normalize smart quotes/apostrophes to their ASCII equivalents."""
    return s.replace("‘", "'").replace("’", "'").replace("“", '"').replace("”", '"')


_SORT_FNS = {
    "name": lambda b: b.name.lower(),
    "type": lambda b: b.type.value.lower(),
    "abv": lambda b: float(b.abv) if b.abv else 0.0,
    "rating": lambda b: float(b.stars) if b.stars else 0.0,
    "sb": lambda b: b.is_single_barrel,
    "private": lambda b: b.is_private,
}

_GROUP_SORT_FNS = {
    "name": lambda g: g["name"].lower(),
    "type": lambda g: g["type"].value.lower(),
    "abv": lambda g: g["abv_max"] or 0.0,
    "rating": lambda g: g["max_stars"] or 0.0,
    "sb": lambda g: g["all_sb"],
    "private": lambda g: any(b.is_private for b in g["bottles"]),
}


def _make_groups(bottles: list) -> list:
    """Group bottles by (name, type) into dicts with aggregate display values."""
    bottles_sorted = sorted(bottles, key=lambda b: (b.name.lower(), b.type.name))
    groups = []
    for _, group_iter in groupby(bottles_sorted, key=lambda b: (b.name.lower(), b.type.name)):
        items = list(group_iter)
        abvs = [float(b.abv) for b in items if b.abv]
        stars_vals = [float(b.stars) for b in items if b.stars]
        groups.append(
            {
                "name": items[0].name,
                "type": items[0].type,
                "count": len(items),
                "bottles": items,
                "is_group": len(items) > 1,
                "abv_min": min(abvs) if abvs else None,
                "abv_max": max(abvs) if abvs else None,
                "max_stars": max(stars_vals) if stars_vals else None,
                "all_sb": all(b.is_single_barrel for b in items),
            }
        )
    return groups


def list_bottles_by_user(
    user: User,
    is_my_list: bool,
    q: str = "",
    types: Optional[List[str]] = None,
    show_killed: bool = False,
    sort: str = "name",
    direction: str = "asc",
    page: int = 1,
    per_page: int = 25,
) -> Dict:
    bottles = list(user.bottles)

    if not is_my_list:
        bottles = [b for b in bottles if not b.is_private]

    active_types = {b.type.name for b in bottles}
    has_killed = any(b.date_killed for b in bottles)

    killed_matches = 0
    if not show_killed:
        killed = [b for b in bottles if b.date_killed]
        if types:
            killed = [b for b in killed if b.type.name in types]
        if q:
            q_lower = _normalize(q.lower())
            killed = [
                b
                for b in killed
                if q_lower in _normalize(b.name.lower())
                or (b.description and q_lower in _normalize(b.description.lower()))
                or (b.bottler and q_lower in _normalize(b.bottler.name.lower()))
                or any(q_lower in _normalize(d.name.lower()) for d in b.distilleries)
                or any(q_lower in _normalize(p.name.lower()) for p in b.barrel_pickers)
            ]
        killed_matches = len(killed)
        bottles = [b for b in bottles if not b.date_killed]

    if types:
        bottles = [b for b in bottles if b.type.name in types]

    if q:
        q_lower = _normalize(q.lower())
        bottles = [
            b
            for b in bottles
            if q_lower in _normalize(b.name.lower())
            or (b.description and q_lower in _normalize(b.description.lower()))
            or (b.bottler and q_lower in _normalize(b.bottler.name.lower()))
            or any(q_lower in _normalize(d.name.lower()) for d in b.distilleries)
            or any(q_lower in _normalize(p.name.lower()) for p in b.barrel_pickers)
        ]

    groups = _make_groups(bottles)
    groups.sort(
        key=_GROUP_SORT_FNS.get(sort, _GROUP_SORT_FNS["name"]),
        reverse=(direction == "desc"),
    )

    total = len(groups)
    total_bottles = sum(g["count"] for g in groups)
    private_count = sum(1 for g in groups for b in g["bottles"] if b.is_private) if is_my_list else 0

    total_pages = max(1, (total + per_page - 1) // per_page)
    page = min(page, total_pages)
    offset = (page - 1) * per_page

    return {
        "grouped": groups[offset : offset + per_page],
        "total": total,
        "total_bottles": total_bottles,
        "private_count": private_count,
        "page": page,
        "per_page": per_page,
        "total_pages": total_pages,
        "has_killed": has_killed,
        "active_types": active_types,
        "killed_matches": killed_matches,
    }


def list_bottles_for_entity(
    entity: Union[BarrelPicker, Bottler, Distillery],
    is_my_list: bool,
    q: str = "",
    types: Optional[List[str]] = None,
    show_killed: bool = False,
    sort: str = "name",
    direction: str = "asc",
    page: int = 1,
    per_page: int = 25,
) -> Dict:
    bottles = list(entity.bottles)

    if not is_my_list:
        bottles = [b for b in bottles if not b.is_private]

    has_killed = any(b.date_killed for b in bottles)

    killed_matches = 0
    if not show_killed:
        killed = [b for b in bottles if b.date_killed]
        if types:
            killed = [b for b in killed if b.type.name in types]
        if q:
            q_lower = _normalize(q.lower())
            killed = [
                b
                for b in killed
                if q_lower in _normalize(b.name.lower())
                or (b.description and q_lower in _normalize(b.description.lower()))
                or (b.bottler and q_lower in _normalize(b.bottler.name.lower()))
                or any(q_lower in _normalize(d.name.lower()) for d in b.distilleries)
                or any(q_lower in _normalize(p.name.lower()) for p in b.barrel_pickers)
            ]
        killed_matches = len(killed)
        bottles = [b for b in bottles if not b.date_killed]

    if types:
        bottles = [b for b in bottles if b.type.name in types]

    if q:
        q_lower = _normalize(q.lower())
        bottles = [
            b
            for b in bottles
            if q_lower in _normalize(b.name.lower())
            or (b.description and q_lower in _normalize(b.description.lower()))
            or (b.bottler and q_lower in _normalize(b.bottler.name.lower()))
            or any(q_lower in _normalize(d.name.lower()) for d in b.distilleries)
            or any(q_lower in _normalize(p.name.lower()) for p in b.barrel_pickers)
        ]

    groups = _make_groups(bottles)
    groups.sort(
        key=_GROUP_SORT_FNS.get(sort, _GROUP_SORT_FNS["name"]),
        reverse=(direction == "desc"),
    )

    total = len(groups)
    total_bottles = sum(g["count"] for g in groups)
    private_count = sum(1 for g in groups for b in g["bottles"] if b.is_private) if is_my_list else 0

    total_pages = max(1, (total + per_page - 1) // per_page)
    page = min(page, total_pages)
    offset = (page - 1) * per_page

    return {
        "grouped": groups[offset : offset + per_page],
        "total": total,
        "total_bottles": total_bottles,
        "private_count": private_count,
        "page": page,
        "per_page": per_page,
        "total_pages": total_pages,
        "has_killed": has_killed,
        "killed_matches": killed_matches,
    }


def get_random_bottle(
    user: User,
    q: str = "",
    types: Optional[List[str]] = None,
) -> Optional[Bottle]:
    bottles = [b for b in user.bottles if not b.date_killed]
    if types:
        bottles = [b for b in bottles if b.type.name in types]
    if q:
        q_lower = _normalize(q.lower())
        bottles = [
            b
            for b in bottles
            if q_lower in _normalize(b.name.lower())
            or (b.description and q_lower in _normalize(b.description.lower()))
            or (b.bottler and q_lower in _normalize(b.bottler.name.lower()))
            or any(q_lower in _normalize(d.name.lower()) for d in b.distilleries)
            or any(q_lower in _normalize(p.name.lower()) for p in b.barrel_pickers)
        ]
    return random.choice(bottles) if bottles else None


def set_bottle_details(form: BottleAddForm, bottle: Optional[Bottle] = None, user: Optional[User] = None) -> Bottle:
    distilleries = [db.session.get(Distillery, did) for did in form.distilleries.data]
    barrel_pickers = [db.session.get(BarrelPicker, pid) for pid in (form.barrel_pickers.data or [])]
    bottler_id = form.bottler_id.data if form.bottler_id.data != "0" else None
    if bottle is None:
        bottle = Bottle(user_id=user.id)

    bottle.name = form.name.data
    bottle.url = form.url.data
    bottle.type = form.type.data
    bottle.distilleries = distilleries
    bottle.barrel_pickers = barrel_pickers
    bottle.bottler_id = bottler_id
    bottle.size = form.size.data
    bottle.year_barrelled = form.year_barrelled.data
    bottle.year_bottled = form.year_bottled.data
    bottle.abv = form.abv.data
    bottle.description = form.description.data
    bottle.review = form.review.data
    bottle.stars = form.stars.data
    bottle.cost = form.cost.data
    bottle.date_purchased = form.date_purchased.data
    bottle.date_opened = form.date_opened.data
    bottle.date_killed = form.date_killed.data
    bottle.is_single_barrel = form.is_single_barrel.data
    bottle.is_private = form.is_private.data
    bottle.personal_note = form.personal_note.data

    return bottle


def add_bottle(form: BottleAddForm, user: User) -> Bottle:
    bottle = set_bottle_details(form=form, user=user)

    db.session.add(bottle)
    db.session.commit()

    ok, error = process_bottle_images(form, bottle, is_pro=user.is_pro)
    if ok:
        url = url_for("bottle.detail", username=bottle.user.username, user_num=bottle.user_num)
        flash(Markup(f'"<a href="{url}">{bottle.name}</a>" has been successfully added.'), "success")
    else:
        db.session.delete(bottle)
        db.session.commit()
        flash(error or f'An error occurred while creating "{bottle.name}".', "danger")
        return None

    current_app.logger.info(f"{user.username} added bottle {bottle.name} successfully.")
    return bottle


def edit_bottle(form: BottleEditForm, bottle: Bottle) -> None:
    bottle = set_bottle_details(form=form, bottle=bottle)

    db.session.add(bottle)
    db.session.commit()

    ok, error = process_bottle_images(form, bottle, is_pro=bottle.user.is_pro)
    if not ok:
        flash(error or f'An error occurred while updating images for "{bottle.name}".', "danger")
        return

    url = url_for("bottle.detail", username=bottle.user.username, user_num=bottle.user_num)
    flash(Markup(f'"<a href="{url}">{bottle.name}</a>" has been successfully updated.'), "success")
    current_app.logger.info(f"{bottle.user.username} edited bottle {bottle.name} successfully.")


def delete_bottle(user: User, bottle: Bottle) -> None:
    if bottle.user_id != user.id:
        flash("There was an issue deleting this bottle.", "danger")
        return

    if bottle.images:
        delete_bottle_images(bottle)

    db.session.delete(bottle)
    db.session.commit()
    current_app.logger.info(f"{user.username} deleted bottle {bottle.name} successfully.")
    flash("Bottle deleted successfully", "success")
