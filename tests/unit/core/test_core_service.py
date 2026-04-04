from datetime import datetime

from mywhiskies.models import Bottle, User
from mywhiskies.services.core.core import get_index_counts, get_live_bottles_for_user


def test_get_index_counts_returns_expected_keys() -> None:
    counts = get_index_counts()

    assert "user_count" in counts
    assert "distillery_count" in counts
    assert "bottle_count" in counts
    assert "pic_count" in counts
    assert "bottle_type_counts" in counts


def test_get_index_counts_with_data(test_user_01: User) -> None:
    counts = get_index_counts()

    # test_user_01 has 1 confirmed user, 4 distilleries, 3 bottles
    assert counts["user_count"] >= 1
    assert counts["distillery_count"] >= 4
    assert counts["bottle_count"] >= 3
    assert isinstance(counts["bottle_type_counts"], list)


def test_get_live_bottles_all_live(test_user_01: User) -> None:
    # test_user_01's bottles have no date_killed set
    live_bottles = get_live_bottles_for_user(test_user_01)
    assert len(live_bottles) == len(test_user_01.bottles)


def test_get_live_bottles_excludes_killed(test_user_01: User) -> None:
    total = len(test_user_01.bottles)
    # kill one bottle
    test_user_01.bottles[0].date_killed = datetime(2024, 1, 1)

    live_bottles = get_live_bottles_for_user(test_user_01)
    assert len(live_bottles) == total - 1
