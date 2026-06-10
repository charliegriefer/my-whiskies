from datetime import datetime

from mywhiskies.extensions import db
from mywhiskies.models import Bottle, Bottler, Distillery, User
from mywhiskies.services.user.insights import get_collection_insights


def _make_user():
    user = User(
        username="insights_unit_user",
        email="insights_unit@example.com",
        email_confirmed=True,
        email_confirm_date=datetime(2024, 1, 1),
    )
    user.set_password("pass")
    db.session.add(user)
    db.session.commit()
    return user


def test_empty_collection_returns_zero_summary():
    user = _make_user()
    data = get_collection_insights(user)
    s = data["summary"]
    assert s["total"] == 0
    assert s["active"] == 0
    assert s["killed"] == 0
    assert s["avg_abv"] is None
    assert s["most_common_type"] is None
    assert s["single_barrel_count"] == 0
    assert data["type_breakdown"] == []
    assert data["top_distilleries"] == []
    assert data["top_bottlers"] == []


def test_summary_counts(test_user_01: User):
    data = get_collection_insights(test_user_01)
    s = data["summary"]
    assert s["total"] == len(test_user_01.bottles)
    killed = sum(1 for b in test_user_01.bottles if b.date_killed)
    assert s["killed"] == killed
    assert s["active"] == s["total"] - killed


def test_avg_abv_ignores_bottles_without_abv(test_user_01: User):
    bottles_with_abv = [b for b in test_user_01.bottles if b.abv is not None]
    data = get_collection_insights(test_user_01)
    if bottles_with_abv:
        expected = round(sum(float(b.abv) for b in bottles_with_abv) / len(bottles_with_abv), 1)
        assert data["summary"]["avg_abv"] == expected
    else:
        assert data["summary"]["avg_abv"] is None


def test_type_breakdown_sorted_descending(test_user_01: User):
    data = get_collection_insights(test_user_01)
    counts = [entry["count"] for entry in data["type_breakdown"]]
    assert counts == sorted(counts, reverse=True)


def test_type_breakdown_percentages_sum_to_100(test_user_01: User):
    data = get_collection_insights(test_user_01)
    total_pct = sum(entry["percentage"] for entry in data["type_breakdown"])
    assert abs(total_pct - 100.0) < 1.0


def test_abv_distribution_buckets():
    user = _make_user()
    distillery = Distillery(name="Test Dist", region_1="X", region_2="TX", user_id=user.id)
    db.session.add(distillery)
    db.session.commit()

    bottles = [
        Bottle(name="Low", type="BOURBON", abv=40.0, user_id=user.id),
        Bottle(name="Mid", type="BOURBON", abv=50.0, user_id=user.id),
        Bottle(name="High", type="BOURBON", abv=60.0, user_id=user.id),
        Bottle(name="No ABV", type="RYE", user_id=user.id),
    ]
    for b in bottles:
        b.distilleries = [distillery]
    db.session.add_all(bottles)
    db.session.commit()

    data = get_collection_insights(user)
    abv = data["abv_distribution"]
    assert abv["under_46"] == 1
    assert abv["range_46_55"] == 1
    assert abv["over_55"] == 1
    assert abv["unknown"] == 1


def test_top_distilleries_counts():
    user = _make_user()
    d1 = Distillery(name="Alpha Dist", region_1="X", region_2="TX", user_id=user.id)
    d2 = Distillery(name="Beta Dist", region_1="X", region_2="TX", user_id=user.id)
    db.session.add_all([d1, d2])
    db.session.commit()

    b1 = Bottle(name="B1", type="BOURBON", user_id=user.id)
    b2 = Bottle(name="B2", type="BOURBON", user_id=user.id)
    b3 = Bottle(name="B3", type="BOURBON", user_id=user.id)
    b1.distilleries = [d1]
    b2.distilleries = [d1]
    b3.distilleries = [d2]
    db.session.add_all([b1, b2, b3])
    db.session.commit()

    data = get_collection_insights(user)
    names = [e["name"] for e in data["top_distilleries"]]
    assert names[0] == "Alpha Dist"
    counts = {e["name"]: e["count"] for e in data["top_distilleries"]}
    assert counts["Alpha Dist"] == 2
    assert counts["Beta Dist"] == 1


def test_top_bottlers_counts():
    user = _make_user()
    distillery = Distillery(name="Bottler Test Dist", region_1="X", region_2="TX", user_id=user.id)
    bottler = Bottler(name="Top Bottler", region_1="X", region_2="TX", user_id=user.id)
    db.session.add_all([distillery, bottler])
    db.session.commit()

    b1 = Bottle(name="B1", type="BOURBON", bottler_id=bottler.id, user_id=user.id)
    b2 = Bottle(name="B2", type="BOURBON", bottler_id=bottler.id, user_id=user.id)
    b3 = Bottle(name="B3", type="BOURBON", user_id=user.id)
    for b in [b1, b2, b3]:
        b.distilleries = [distillery]
    db.session.add_all([b1, b2, b3])
    db.session.commit()

    data = get_collection_insights(user)
    assert data["top_bottlers"][0]["name"] == "Top Bottler"
    assert data["top_bottlers"][0]["count"] == 2
