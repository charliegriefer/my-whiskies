import pandas as pd

from mywhiskies.blueprints.user.models import User


def create_export_csv(current_user: User):
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
