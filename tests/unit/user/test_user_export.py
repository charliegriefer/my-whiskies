import csv
import json
import os

from mywhiskies.models import User
from mywhiskies.services.user.user import build_export_bottles, create_export_csv, create_export_json


def test_build_export_bottles_all_included(test_user_01: User) -> None:
    rows = build_export_bottles(test_user_01, include_killed=True, include_private=True, include_notes=True)
    assert len(rows) == len(test_user_01.bottles)


def test_build_export_bottles_excludes_private(test_user_01: User) -> None:
    private_count = sum(1 for b in test_user_01.bottles if b.is_private)
    rows = build_export_bottles(test_user_01, include_private=False)
    assert len(rows) == len(test_user_01.bottles) - private_count


def test_build_export_bottles_excludes_killed(test_user_01: User) -> None:
    killed_count = sum(1 for b in test_user_01.bottles if b.date_killed)
    rows = build_export_bottles(test_user_01, include_killed=False)
    assert len(rows) == len(test_user_01.bottles) - killed_count


def test_build_export_bottles_omits_notes_when_excluded(test_user_01: User) -> None:
    rows = build_export_bottles(test_user_01, include_notes=False)
    for row in rows:
        assert row["personal_note"] is None


def test_build_export_bottles_sorted_by_name(test_user_01: User) -> None:
    rows = build_export_bottles(test_user_01)
    names = [r["name"] for r in rows]
    assert names == sorted(names, key=str.lower)


def test_create_export_csv_writes_file(test_user_01: User) -> None:
    bottles = build_export_bottles(test_user_01)
    path = create_export_csv(test_user_01, bottles)
    assert os.path.exists(path)
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    assert len(rows) == len(bottles)
    assert "Bottle Name" in reader.fieldnames
    assert "Personal Note" in reader.fieldnames


def test_create_export_json_writes_file(test_user_01: User) -> None:
    bottles = build_export_bottles(test_user_01)
    path = create_export_json(test_user_01, bottles)
    assert os.path.exists(path)
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    assert len(data) == len(bottles)
    assert "name" in data[0]
