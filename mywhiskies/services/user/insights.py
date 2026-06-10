from collections import Counter
from typing import Any, Dict, List, Optional

from mywhiskies.models import User
from mywhiskies.models.bottle import BottleTypes


def get_collection_insights(user: User) -> Dict[str, Any]:
    bottles = user.bottles
    total = len(bottles)

    if total == 0:
        return _empty_insights()

    active = [b for b in bottles if not b.date_killed]
    killed = [b for b in bottles if b.date_killed]

    abv_bottles = [b for b in bottles if b.abv is not None]
    avg_abv: Optional[float] = None
    if abv_bottles:
        avg_abv = round(sum(float(b.abv) for b in abv_bottles) / len(abv_bottles), 1)

    type_counts: Counter = Counter(b.type for b in bottles)
    most_common_type: Optional[str] = None
    if type_counts:
        most_common_type = type_counts.most_common(1)[0][0].value

    single_barrel_count = sum(1 for b in bottles if b.is_single_barrel)

    type_breakdown: List[Dict] = []
    for bottle_type in BottleTypes:
        count = type_counts.get(bottle_type, 0)
        if count > 0:
            type_breakdown.append(
                {
                    "type": bottle_type.value,
                    "count": count,
                    "percentage": round(count / total * 100, 1),
                }
            )
    type_breakdown.sort(key=lambda x: x["count"], reverse=True)

    abv_under_46 = sum(1 for b in bottles if b.abv is not None and float(b.abv) < 46)
    abv_46_55 = sum(1 for b in bottles if b.abv is not None and 46 <= float(b.abv) <= 55)
    abv_over_55 = sum(1 for b in bottles if b.abv is not None and float(b.abv) > 55)
    abv_unknown = sum(1 for b in bottles if b.abv is None)

    distillery_counts: Counter = Counter()
    for b in bottles:
        for d in b.distilleries:
            distillery_counts[d.name] += 1
    top_distilleries = [{"name": name, "count": count} for name, count in distillery_counts.most_common(10)]

    bottler_counts: Counter = Counter(b.bottler.name for b in bottles if b.bottler)
    top_bottlers = [{"name": name, "count": count} for name, count in bottler_counts.most_common(10)]

    return {
        "summary": {
            "total": total,
            "active": len(active),
            "killed": len(killed),
            "avg_abv": avg_abv,
            "most_common_type": most_common_type,
            "single_barrel_count": single_barrel_count,
        },
        "type_breakdown": type_breakdown,
        "abv_distribution": {
            "under_46": abv_under_46,
            "range_46_55": abv_46_55,
            "over_55": abv_over_55,
            "unknown": abv_unknown,
        },
        "top_distilleries": top_distilleries,
        "top_bottlers": top_bottlers,
    }


def _empty_insights() -> Dict[str, Any]:
    return {
        "summary": {
            "total": 0,
            "active": 0,
            "killed": 0,
            "avg_abv": None,
            "most_common_type": None,
            "single_barrel_count": 0,
        },
        "type_breakdown": [],
        "abv_distribution": {"under_46": 0, "range_46_55": 0, "over_55": 0, "unknown": 0},
        "top_distilleries": [],
        "top_bottlers": [],
    }
