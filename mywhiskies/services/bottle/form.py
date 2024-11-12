from typing import Union

from mywhiskies.blueprints.bottle.forms import BottleAddForm, BottleEditForm
from mywhiskies.blueprints.bottle.models import BottleTypes


def prepare_bottle_form(
    user, form: Union[BottleAddForm, BottleEditForm]
) -> Union[BottleAddForm, BottleEditForm]:

    # set up bottle type dropdown
    form.type.choices = [(t.name, t.value) for t in BottleTypes]
    form.type.choices.sort()
    form.type.choices.append(
        form.type.choices.pop(form.type.choices.index(("other", "Other")))
    )
    form.type.choices.insert(0, ("", "Choose a Bottle Type"))

    # set up distilleries dropdown
    distilleries = user.distilleries
    distilleries.sort(key=lambda d: d.name)
    form.distilleries.choices = [(d.id, d.name) for d in distilleries]
    form.distilleries.choices.insert(0, ("", "Choose One or More Distilleries"))
    form.distilleries.choices.insert(1, ("", " "))

    # set up bottlers dropdown
    bottlers = user.bottlers
    bottlers.sort(key=lambda d: d.name)
    form.bottler_id.choices = [(b.id, b.name) for b in bottlers]
    form.bottler_id.choices.insert(0, (0, "Distillery Bottling"))

    # set up star rating dropdown
    form.stars.choices = [(str(x * 0.5), str(x * 0.5)) for x in range(0, 11)]
    form.stars.choices.insert(0, ("", "Enter a Star Rating (Optional)"))

    return form
