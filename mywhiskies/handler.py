import io
from typing import Union

import boto3
from botocore.exceptions import ClientError
from PIL import Image

from mywhiskies.blueprints.bottle.forms import BottleEditForm, BottleForm
from mywhiskies.blueprints.bottle.models import Bottle, BottleTypes


def prep_bottle_form(
    user, form: Union[BottleForm, BottleEditForm]
) -> Union[BottleForm, BottleEditForm]:
    # set up the bottle types dropdown
    form.type.choices = [(t.name, t.value) for t in BottleTypes]
    # sort the list and move "Other" to the bottom
    form.type.choices.sort()
    form.type.choices.append(
        form.type.choices.pop(form.type.choices.index(("other", "Other")))
    )
    form.type.choices.insert(0, ("", "Choose a Bottle Type"))

    # set up the distilleries dropdown
    distilleries = user.distilleries
    distilleries.sort(key=lambda d: d.name)
    form.distilleries.choices = [(d.id, d.name) for d in distilleries]
    form.distilleries.choices.insert(0, ("", "Choose One or More Distilleries"))
    form.distilleries.choices.insert(1, ("", " "))

    # set up the bottlers dropdown
    bottlers = user.bottlers
    bottlers.sort(key=lambda d: d.name)
    form.bottler_id.choices = [(b.id, b.name) for b in bottlers]
    form.bottler_id.choices.insert(0, (0, "Distillery Bottling"))

    # set up the star rating dropdown
    form.stars.choices = [(str(x * 0.5), str(x * 0.5)) for x in range(0, 11)]
    form.stars.choices.insert(0, ("", "Enter a Star Rating (Optional)"))

    return form


def bottle_add_images(
    form: Union[BottleForm, BottleEditForm], bottle_in: Bottle
) -> bool:
    for i in range(1, 4):
        image_field = form[f"bottle_image_{i}"]

        if image_field.data:
            image_in = Image.open(image_field.data)
            if image_in.width > 400:
                divisor = image_in.width / 400
                image_dims = (
                    int(image_in.width / divisor),
                    int(image_in.height / divisor),
                )
                image_in = image_in.resize(image_dims)

            new_filename = f"{bottle_in.id}_{i}"

            in_mem_file = io.BytesIO()
            image_in.save(in_mem_file, format="png")
            in_mem_file.seek(0)

            s3_client = boto3.client("s3")
            try:
                s3_client.put_object(
                    Body=in_mem_file,
                    Bucket="my-whiskies-pics",
                    Key=f"{new_filename}.png",
                    ContentType="image/png",
                )
            except ClientError:
                # TODO: log error
                return False

    return True


def bottle_edit_images(form: BottleEditForm, bottle: Bottle):
    s3_client = boto3.client("s3")

    for i in range(1, 4):
        if form[f"remove_image_{i}"].data:
            s3_client.copy_object(
                Bucket="my-whiskies-pics",
                CopySource=f"my-whiskies-pics/{bottle.id}_{i}.png",
                Key=f"__del_{bottle.id}_{i}.png",
                ContentType="image/png",
            )
            s3_client.delete_object(
                Bucket="my-whiskies-pics", Key=f"{bottle.id}_{i}.png"
            )

    images = s3_client.list_objects(Bucket="my-whiskies-pics", Prefix=bottle.id).get(
        "Contents", []
    )
    images.sort(key=lambda obj: obj.get("Key"))

    for idx, img in enumerate(images, 1):
        img_num = int(img.get("Key").split("_")[-1].split(".")[0])

        if idx != img_num:
            s3_client.copy_object(
                Bucket="my-whiskies-pics",
                CopySource=f"my-whiskies-pics/{bottle.id}_{img_num}.png",
                Key=f"{bottle.id}_{idx}.png",
                ContentType="image/png",
            )
            s3_client.delete_object(
                Bucket="my-whiskies-pics", Key=f"{bottle.id}_{img_num}.png"
            )


def bottle_delete_images(bottle: Bottle):
    s3_client = boto3.client("s3")
    for i in range(1, 4):
        s3_client.delete_object(
            Bucket="my-whiskies-pics", Key=f"__del_{bottle.id}_{i}.png"
        )


def get_bottle_image_count(bottle_id: str) -> int:
    s3_client = boto3.client("s3")
    images = s3_client.list_objects(Bucket="my-whiskies-pics", Prefix=bottle_id).get(
        "Contents", []
    )
    return len(images)
