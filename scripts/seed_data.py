"""
Seed the local database with fake distilleries, bottlers, and bottles.

Usage:
    python scripts/seed_data.py <username>

The user must already exist. All seeded records are attached to that user.
"""

import random
import sys
from datetime import datetime, timedelta

from faker import Faker

sys.path.insert(0, ".")

from mywhiskies.app import create_app
from mywhiskies.extensions import db
from mywhiskies.models import Bottle, Bottler, Distillery, User
from mywhiskies.models.bottle import BottleTypes

fake = Faker()

# ---------------------------------------------------------------------------
# Realistic whisky geography
# ---------------------------------------------------------------------------

DISTILLERY_REGIONS = [
    ("Kentucky", "Louisville"),
    ("Kentucky", "Bardstown"),
    ("Kentucky", "Lawrenceburg"),
    ("Kentucky", "Loretto"),
    ("Kentucky", "Clermont"),
    ("Tennessee", "Lynchburg"),
    ("Tennessee", "Tullahoma"),
    ("Scotland", "Speyside"),
    ("Scotland", "Islay"),
    ("Scotland", "Highlands"),
    ("Scotland", "Lowlands"),
    ("Scotland", "Campbeltown"),
    ("Ireland", "County Cork"),
    ("Ireland", "County Antrim"),
    ("Japan", "Yamazaki"),
    ("Japan", "Nikka"),
    ("Texas", "Austin"),
    ("New York", "Finger Lakes"),
    ("Colorado", "Denver"),
    ("Washington", "Seattle"),
]

BOTTLER_REGIONS = [
    ("Scotland", "Edinburgh"),
    ("Scotland", "Glasgow"),
    ("Scotland", "Speyside"),
    ("Kentucky", "Louisville"),
    ("United States", "New York"),
]

DISTILLERY_NAME_PARTS = [
    ("Glen", "Moor", "Craig", "Ben", "Loch", "Burn", "Strath"),
    ("more", "fiddich", "livet", "kinchie", "rannoch", "goyne", "haven"),
]

BOURBON_EXPRESSIONS = [
    "Single Barrel", "Small Batch", "Barrel Proof", "Bottled in Bond",
    "Four Grain", "Wheated", "High Rye", "Cask Strength", "Reserve",
    "Select", "Private Selection", "Master's Keep",
]

SCOTCH_EXPRESSIONS = [
    "12 Year", "15 Year", "18 Year", "21 Year", "25 Year",
    "Cask Strength", "Quarter Cask", "Double Matured", "Sherry Cask",
    "Port Finish", "Rum Cask Finish", "Single Cask",
]

BOTTLE_SIZES = [375, 750, 1000, 1750]

BOTTLE_TYPES_BY_REGION = {
    "Kentucky": [BottleTypes.BOURBON, BottleTypes.RYE],
    "Tennessee": [BottleTypes.TENNESSEE_WHISKEY, BottleTypes.BOURBON],
    "Scotland": [BottleTypes.SCOTCH],
    "Ireland": [BottleTypes.IRISH_WHISKEY],
    "Japan": [BottleTypes.WORLD_WHISKEY],
    "Texas": [BottleTypes.BOURBON, BottleTypes.AMERICAN_WHISKEY],
    "New York": [BottleTypes.RYE, BottleTypes.AMERICAN_SINGLE_MALT],
    "Colorado": [BottleTypes.BOURBON, BottleTypes.AMERICAN_WHISKEY],
    "Washington": [BottleTypes.AMERICAN_SINGLE_MALT, BottleTypes.RYE],
}


def fake_distillery_name(region_1: str) -> str:
    if region_1 in ("Scotland", "Ireland"):
        prefix = random.choice(DISTILLERY_NAME_PARTS[0])
        suffix = random.choice(DISTILLERY_NAME_PARTS[1])
        return f"{prefix}{suffix} Distillery"
    else:
        return f"{fake.last_name()} {random.choice(['Distilling', 'Distillery', 'Spirits', 'Craft Distillery'])}"


def fake_bottler_name() -> str:
    return f"{fake.last_name()} {random.choice(['Brothers', 'Independent Bottlers', 'Selections', 'Whisky Co.', '& Co.'])}"


def bottle_name(distillery_name: str, region_1: str) -> str:
    base = distillery_name.replace(" Distillery", "").replace(" Distilling", "").replace(" Spirits", "")
    if region_1 in ("Scotland", "Ireland", "Japan"):
        expression = random.choice(SCOTCH_EXPRESSIONS)
    else:
        expression = random.choice(BOURBON_EXPRESSIONS)
    return f"{base} {expression}"


def random_past_date(years_back: int = 5) -> datetime:
    days = random.randint(0, years_back * 365)
    return datetime.utcnow() - timedelta(days=days)


# ---------------------------------------------------------------------------
# Seed functions
# ---------------------------------------------------------------------------

def seed_distilleries(user: User, count: int = 12) -> list[Distillery]:
    distilleries = []
    used_regions = random.sample(DISTILLERY_REGIONS, min(count, len(DISTILLERY_REGIONS)))
    for region_1, region_2 in used_regions:
        d = Distillery(
            name=fake_distillery_name(region_1),
            description=fake.paragraph(nb_sentences=2),
            region_1=region_1,
            region_2=region_2,
            url=None,
            user_id=user.id,
            user_num=0,  # overwritten by before_insert event
        )
        db.session.add(d)
        distilleries.append(d)
    db.session.flush()
    print(f"  Created {len(distilleries)} distilleries")
    return distilleries


def seed_bottlers(user: User, count: int = 5) -> list[Bottler]:
    bottlers = []
    regions = random.sample(BOTTLER_REGIONS, min(count, len(BOTTLER_REGIONS)))
    for region_1, region_2 in regions:
        b = Bottler(
            name=fake_bottler_name(),
            description=fake.paragraph(nb_sentences=1),
            region_1=region_1,
            region_2=region_2,
            url=None,
            user_id=user.id,
            user_num=0,
        )
        db.session.add(b)
        bottlers.append(b)
    db.session.flush()
    print(f"  Created {len(bottlers)} bottlers")
    return bottlers


def seed_bottles(
    user: User,
    distilleries: list[Distillery],
    bottlers: list[Bottler],
    count: int = 40,
) -> None:
    statuses = ["open"] * 10 + ["killed"] * 5 + ["unopen"] * 25

    for _ in range(count):
        # pick 1-2 distilleries
        num_distilleries = random.choices([1, 2], weights=[80, 20])[0]
        bottle_distilleries = random.sample(distilleries, min(num_distilleries, len(distilleries)))
        primary = bottle_distilleries[0]

        region_1 = primary.region_1
        bottle_type = random.choice(
            BOTTLE_TYPES_BY_REGION.get(region_1, list(BottleTypes))
        )

        date_purchased = random_past_date(years_back=6)
        year_barrelled = random.randint(2008, 2020)
        year_bottled = year_barrelled + random.randint(3, 12)

        status = random.choice(statuses)
        date_opened = None
        date_killed = None
        if status in ("open", "killed"):
            date_opened = date_purchased + timedelta(days=random.randint(30, 365))
        if status == "killed":
            date_killed = date_opened + timedelta(days=random.randint(30, 730))

        use_bottler = random.random() < 0.25
        bottler = random.choice(bottlers) if use_bottler else None

        abv = round(random.uniform(40.0, 67.5), 1)
        stars_pick = random.choice([None, None, 3.0, 3.5, 4.0, 4.0, 4.5, 4.5, 5.0]) if random.random() > 0.3 else None
        stars = round(stars_pick, 1) if stars_pick is not None else None

        b = Bottle(
            name=bottle_name(primary.name, region_1),
            type=bottle_type,
            abv=abv,
            size=random.choice(BOTTLE_SIZES),
            year_barrelled=year_barrelled if random.random() > 0.3 else None,
            year_bottled=year_bottled if random.random() > 0.2 else None,
            description=fake.paragraph(nb_sentences=2) if random.random() > 0.4 else None,
            review=fake.paragraph(nb_sentences=3) if status in ("open", "killed") and random.random() > 0.3 else None,
            stars=stars,
            cost=round(random.uniform(25.0, 250.0), 2) if random.random() > 0.2 else None,
            date_purchased=date_purchased if random.random() > 0.1 else None,
            date_opened=date_opened,
            date_killed=date_killed,
            is_private=random.random() < 0.1,
            is_single_barrel=random.random() < 0.3,
            user_id=user.id,
            user_num=0,
            bottler_id=bottler.id if bottler else None,
        )
        b.distilleries = bottle_distilleries
        db.session.add(b)

    db.session.flush()
    print(f"  Created {count} bottles")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    if len(sys.argv) != 2:
        print("Usage: python scripts/seed_data.py <username>")
        sys.exit(1)

    username = sys.argv[1]

    app = create_app()
    with app.app_context():
        user = db.session.scalar(db.select(User).where(User.username == username))
        if not user:
            print(f"Error: no user found with username '{username}'")
            sys.exit(1)

        print(f"Seeding data for user: {user.username}")
        distilleries = seed_distilleries(user)
        bottlers = seed_bottlers(user)
        seed_bottles(user, distilleries, bottlers)
        db.session.commit()
        print("Done.")


if __name__ == "__main__":
    main()
