import random
from typing import Dict, List, Optional, Union

import boto3
from flask import current_app, flash

from mywhiskies.extensions import db
from mywhiskies.forms.bottle import BottleAddForm, BottleEditForm
from mywhiskies.models import Bottle, Bottler, Distillery, User
from mywhiskies.services.bottle.image import (
    add_bottle_images,
    delete_bottle_images,
    get_s3_config,
)

_SORT_FNS = {
    "name": lambda b: b.name.lower(),
    "type": lambda b: b.type.value.lower(),
    "abv": lambda b: float(b.abv) if b.abv else 0.0,
    "rating": lambda b: float(b.stars) if b.stars else 0.0,
    "sb": lambda b: b.is_single_barrel,
    "private": lambda b: b.is_private,
}


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

    has_killed = any(b.date_killed for b in bottles)

    if not show_killed:
        bottles = [b for b in bottles if not b.date_killed]

    if types:
        bottles = [b for b in bottles if b.type.name in types]

    if q:
        q_lower = q.lower()
        bottles = [b for b in bottles if q_lower in b.name.lower()]

    total = len(bottles)
    bottles.sort(key=_SORT_FNS.get(sort, _SORT_FNS["name"]), reverse=(direction == "desc"))

    total_pages = max(1, (total + per_page - 1) // per_page)
    page = min(page, total_pages)
    offset = (page - 1) * per_page

    return {
        "bottles": bottles[offset : offset + per_page],
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": total_pages,
        "has_killed": has_killed,
    }


def list_bottles_for_entity(
    entity: Union[Bottler, Distillery],
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

    if not show_killed:
        bottles = [b for b in bottles if not b.date_killed]

    if types:
        bottles = [b for b in bottles if b.type.name in types]

    if q:
        q_lower = q.lower()
        bottles = [b for b in bottles if q_lower in b.name.lower()]

    total = len(bottles)
    bottles.sort(key=_SORT_FNS.get(sort, _SORT_FNS["name"]), reverse=(direction == "desc"))

    total_pages = max(1, (total + per_page - 1) // per_page)
    page = min(page, total_pages)
    offset = (page - 1) * per_page

    return {
        "bottles": bottles[offset : offset + per_page],
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": total_pages,
        "has_killed": has_killed,
    }


def get_random_bottle(user: User) -> Optional[Bottle]:
    active = [b for b in user.bottles if not b.date_killed]
    return random.choice(active) if active else None


def set_bottle_details(
    form: BottleAddForm, bottle: Optional[Bottle] = None, user: Optional[User] = None
) -> Bottle:
    """Update or create a bottle's details from the form data."""
    distilleries = [
        db.session.get(Distillery, distillery_id)
        for distillery_id in form.distilleries.data
    ]
    bottler_id = form.bottler_id.data if form.bottler_id.data != "0" else None
    if bottle is None:
        bottle = Bottle(user_id=user.id)

    bottle.name = form.name.data
    bottle.url = form.url.data
    bottle.type = form.type.data
    bottle.distilleries = distilleries
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

    # Upload images
    if add_bottle_images(form, bottle):
        flash(f'"{bottle.name}" has been successfully added.', "success")
    else:
        db.session.delete(bottle)
        db.session.commit()
        flash(f'An error occurred while creating "{bottle.name}".', "danger")
        return None  # Bottle creation failed

    current_app.logger.info(f"{user.username} added bottle {bottle.name} successfully.")
    return bottle


def edit_bottle(form: BottleEditForm, bottle: Bottle) -> None:
    bottle = set_bottle_details(form=form, bottle=bottle)

    db.session.add(bottle)
    db.session.commit()

    # Handle image removals - resequencing is handled in delete_bottle_images
    for seq in range(1, 4):
        if getattr(form, f"remove_image_{seq}").data == "YES":
            if image := bottle.get_image_by_sequence(seq):
                delete_bottle_images(bottle, [image.id])

    # Handle new image uploads - add_bottle_images will maintain proper sequencing
    add_bottle_images(form, bottle)

    flash(f'"{bottle.name}" has been successfully updated.', "success")
    current_app.logger.info(
        f"{bottle.user.username} edited bottle {bottle.name} successfully."
    )


def delete_bottle(user: User, bottle: Bottle) -> None:
    if bottle.user_id != user.id:
        flash("There was an issue deleting this bottle.", "danger")
        return

    img_s3_bucket, img_s3_key, _ = get_s3_config()

    if bottle.image_count:
        s3_client = boto3.client("s3")
        for i in range(1, bottle.image_count + 1):
            s3_client.delete_object(
                Bucket=f"{img_s3_bucket}",
                Key=f"{img_s3_key}/{bottle.id}_{i}.png",
            )

    db.session.delete(bottle)
    db.session.commit()
    current_app.logger.info(
        f"{user.username} deleted bottle {bottle.name} successfully."
    )
    flash("Bottle deleted successfully", "success")
