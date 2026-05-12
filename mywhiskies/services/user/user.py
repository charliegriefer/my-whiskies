import csv
import json
import zipfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from typing import Optional

import boto3
from botocore.exceptions import ClientError
from flask import current_app, flash

from mywhiskies.extensions import db
from mywhiskies.models import User, UserLogin


def is_email_taken(email: str) -> bool:
    stmt = db.select(User).filter(User.email == email.strip(), User.is_deleted == False)  # noqa: E712
    return db.session.execute(stmt).first() is not None


def apply_email_change(user: User, new_email: str) -> None:
    user.email = new_email
    user.email_confirm_date = datetime.utcnow()
    db.session.commit()
    flash("Your e-mail address has been updated.", "success")


def get_user_by_email(email: str) -> Optional[User]:
    stmt = db.select(User).filter(User.email == email.strip())
    return db.session.execute(stmt).first()


_CSV_FIELDS = [
    ("Bottle Name", "name"),
    ("Bottle Type", "type"),
    ("Distilleries", "distilleries"),
    ("Year Barrelled", "year_barrelled"),
    ("Year Bottled", "year_bottled"),
    ("ABV", "abv"),
    ("Size", "size"),
    ("Description", "description"),
    ("Review", "review"),
    ("Personal Note", "personal_note"),
    ("Stars", "stars"),
    ("Cost", "cost"),
    ("Date Purchased", "date_purchased"),
    ("Date Opened", "date_opened"),
    ("Date Killed", "date_killed"),
]


def build_export_bottles(
    user: User,
    include_killed: bool = True,
    include_private: bool = True,
    include_notes: bool = True,
) -> list[dict]:
    rows = []
    for bottle in sorted(user.bottles, key=lambda b: b.name.lower()):
        if not include_killed and bottle.date_killed:
            continue
        if not include_private and bottle.is_private:
            continue
        rows.append(
            {
                "name": bottle.name,
                "type": bottle.type.value,
                "distilleries": ", ".join(d.name for d in bottle.distilleries),
                "year_barrelled": bottle.year_barrelled,
                "year_bottled": bottle.year_bottled,
                "abv": f"{bottle.abv:.2f}" if bottle.abv else None,
                "size": f"{bottle.size}ml" if bottle.size else None,
                "description": bottle.description,
                "review": bottle.review,
                "personal_note": bottle.personal_note if include_notes else None,
                "stars": bottle.stars,
                "cost": str(bottle.cost) if bottle.cost else None,
                "date_purchased": str(bottle.date_purchased) if bottle.date_purchased else None,
                "date_opened": str(bottle.date_opened) if bottle.date_opened else None,
                "date_killed": str(bottle.date_killed) if bottle.date_killed else None,
            }
        )
    return rows


def create_export_csv(user: User, bottles: list[dict]) -> str:
    path = f"/tmp/{user.id}.csv"
    headers = [label for label, _ in _CSV_FIELDS]
    keys = [key for _, key in _CSV_FIELDS]
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        for bottle in bottles:
            writer.writerow([bottle.get(k) for k in keys])
    return path


def create_export_json(user: User, bottles: list[dict]) -> str:
    path = f"/tmp/{user.id}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(bottles, f, indent=2, default=str)
    return path


def create_export_images_zip(user: User) -> str:
    s3_client = boto3.client("s3")
    img_s3_bucket = current_app.config["BOTTLE_IMAGE_S3_BUCKET"]
    img_s3_key = current_app.config["BOTTLE_IMAGE_S3_KEY"]
    path = f"/tmp/{user.id}_images.zip"

    tasks = []
    for bottle in user.bottles:
        safe_name = bottle.name.replace("/", "-").replace(":", "-")
        for img in bottle.images:
            zip_filename = f"{bottle.user_num:04d}_{safe_name}_{img.sequence}.jpg"
            s3_object_key = f"{img_s3_key}/{bottle.id}_{img.sequence}.jpg"
            tasks.append((zip_filename, s3_object_key))

    def fetch(zip_filename, s3_key):
        try:
            obj = s3_client.get_object(Bucket=img_s3_bucket, Key=s3_key)
            return zip_filename, obj["Body"].read()
        except ClientError:
            return zip_filename, None

    with zipfile.ZipFile(path, "w", zipfile.ZIP_STORED) as zf:
        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = {executor.submit(fetch, zf_name, s3_key): zf_name for zf_name, s3_key in tasks}
            for future in as_completed(futures):
                zip_filename, data = future.result()
                if data:
                    zf.writestr(zip_filename, data)

    return path


def set_account_privacy(user: User, is_private: bool) -> None:
    user.is_private = is_private
    db.session.commit()


def change_user_password(user: User, current_password: str, new_password: str) -> bool:
    if not user.check_password(current_password):
        return False
    user.set_password(new_password)
    db.session.commit()
    flash("Your password has been changed.", "success")
    return True


def delete_user_account(user: User) -> None:
    s3_client = boto3.client("s3")
    img_s3_bucket = current_app.config["BOTTLE_IMAGE_S3_BUCKET"]
    img_s3_key = current_app.config["BOTTLE_IMAGE_S3_KEY"]

    for bottle in list(user.bottles):
        for img in list(bottle.images):
            try:
                s3_client.delete_object(
                    Bucket=img_s3_bucket,
                    Key=f"{img_s3_key}/{bottle.id}_{img.sequence}.jpg",
                )
            except ClientError:
                pass
        db.session.delete(bottle)

    for bottler in list(user.bottlers):
        db.session.delete(bottler)

    for distillery in list(user.distilleries):
        db.session.delete(distillery)

    db.session.execute(db.delete(UserLogin).where(UserLogin.user_id == user.id))
    db.session.delete(user)
    db.session.commit()
