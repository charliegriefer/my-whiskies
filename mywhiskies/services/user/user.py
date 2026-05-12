from datetime import datetime
from typing import Optional

import boto3
import pandas as pd
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


def create_export_csv(current_user: User) -> None:
    fieldnames = [
        "Bottle Name",
        "Bottle Type",
        "Distilleries",
        "Year Barrelled",
        "Year Bottled",
        "ABV",
        "Size",
        "Description",
        "Review",
        "Stars",
        "Cost",
        "Date Purchased",
        "Date Opened",
        "Date Killed",
    ]

    bottles = []
    for bottle in current_user.bottles:
        bottles.append(
            [
                bottle.name,
                bottle.type.value,
                ", ".join([b.name for b in bottle.distilleries]),
                bottle.year_barrelled,
                bottle.year_bottled,
                f"{bottle.abv:.2f}" if bottle.abv else None,
                f"{bottle.size}ml" if bottle.size else None,
                bottle.description,
                bottle.review,
                bottle.stars,
                bottle.cost,
                bottle.date_purchased,
                bottle.date_opened,
                bottle.date_killed,
            ]
        )

    df = pd.DataFrame(bottles, columns=fieldnames)
    df = df.sort_values(by=["Bottle Name"])
    df.to_csv(f"/tmp/{current_user.id}.csv", index=False)


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
