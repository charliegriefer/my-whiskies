from typing import Union

from mywhiskies.blueprints.bottle.forms import BottleAddForm, BottleEditForm
from mywhiskies.blueprints.bottle.models import BottleTypes
from mywhiskies.blueprints.user.models import User


def prep_bottle_form(
    user: User, form: Union[BottleAddForm, BottleEditForm]
) -> Union[BottleAddForm, BottleEditForm]:

    _set_up_bottle_type(form)  # set up bottle type dropdown
    _set_up_distilleries(form, user)  # set up distilleries dropdown
    _set_up_bottlers(form, user)  # set up bottlers dropdown
    _set_up_star_rating(form)  # set up star rating dropdown

    return form


def _set_up_bottle_type(form: Union[BottleAddForm, BottleEditForm]) -> None:
    form.type.choices = [(t.name, t.value) for t in BottleTypes]
    form.type.choices.sort()
    form.type.choices.append(
        form.type.choices.pop(form.type.choices.index(("OTHER", "Other")))
    )
    form.type.choices.insert(0, ("", "Choose a Bottle Type"))


def _set_up_distilleries(
    form: Union[BottleAddForm, BottleEditForm], user: User
) -> None:
    distilleries = user.distilleries
    distilleries.sort(key=lambda d: d.name)
    form.distilleries.choices = [(d.id, d.name) for d in distilleries]


def _set_up_bottlers(form: Union[BottleAddForm, BottleEditForm], user: User) -> None:
    bottlers = user.bottlers
    bottlers.sort(key=lambda d: d.name)
    form.bottler_id.choices = [(b.id, b.name) for b in bottlers]
    form.bottler_id.choices.insert(0, (0, "Distillery Bottling"))


def _set_up_star_rating(form: Union[BottleAddForm, BottleEditForm]) -> None:
    form.stars.choices = [(str(x * 0.5), str(x * 0.5)) for x in range(0, 11)]
    form.stars.choices.insert(0, ("", "Enter a Star Rating (Optional)"))
