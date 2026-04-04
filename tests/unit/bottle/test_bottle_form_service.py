from mywhiskies.models import BottleTypes, User
from mywhiskies.services.bottle.form import prep_bottle_form
from mywhiskies.forms.bottle import BottleAddForm


def test_bottle_type_choices_first_is_placeholder(app, test_user_01: User) -> None:
    with app.test_request_context():
        form = BottleAddForm()
        prep_bottle_form(test_user_01, form)
        assert form.type.choices[0] == ("", "Choose a Bottle Type")


def test_bottle_type_choices_last_is_other(app, test_user_01: User) -> None:
    with app.test_request_context():
        form = BottleAddForm()
        prep_bottle_form(test_user_01, form)
        assert form.type.choices[-1] == ("OTHER", "Other")


def test_bottle_type_choices_includes_all_types(app, test_user_01: User) -> None:
    with app.test_request_context():
        form = BottleAddForm()
        prep_bottle_form(test_user_01, form)
        choice_keys = [c[0] for c in form.type.choices]
        for bottle_type in BottleTypes:
            assert bottle_type.name in choice_keys


def test_distillery_choices_match_user(app, test_user_01: User) -> None:
    with app.test_request_context():
        form = BottleAddForm()
        prep_bottle_form(test_user_01, form)
        choice_names = [c[1] for c in form.distilleries.choices]
        for distillery in test_user_01.distilleries:
            assert distillery.name in choice_names


def test_distillery_choices_are_sorted(app, test_user_01: User) -> None:
    with app.test_request_context():
        form = BottleAddForm()
        prep_bottle_form(test_user_01, form)
        choice_names = [c[1] for c in form.distilleries.choices]
        assert choice_names == sorted(choice_names)


def test_bottler_choices_first_is_distillery_bottling(app, test_user_01: User) -> None:
    with app.test_request_context():
        form = BottleAddForm()
        prep_bottle_form(test_user_01, form)
        assert form.bottler_id.choices[0] == (0, "Distillery Bottling")


def test_bottler_choices_match_user(app, test_user_01: User) -> None:
    with app.test_request_context():
        form = BottleAddForm()
        prep_bottle_form(test_user_01, form)
        choice_names = [c[1] for c in form.bottler_id.choices]
        for bottler in test_user_01.bottlers:
            assert bottler.name in choice_names


def test_star_rating_choices_first_is_placeholder(app, test_user_01: User) -> None:
    with app.test_request_context():
        form = BottleAddForm()
        prep_bottle_form(test_user_01, form)
        assert form.stars.choices[0] == ("", "Enter a Star Rating (Optional)")


def test_star_rating_choices_range(app, test_user_01: User) -> None:
    with app.test_request_context():
        form = BottleAddForm()
        prep_bottle_form(test_user_01, form)
        # 0.0 to 5.0 in 0.5 increments = 11 values, plus placeholder = 12 total
        assert len(form.stars.choices) == 12
