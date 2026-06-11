from datetime import datetime, timezone
from typing import Any, Dict, Optional

import stripe
from flask import current_app

from mywhiskies.models import User


def get_subscription_info(user: User) -> Optional[Dict[str, Any]]:
    if not user.is_pro or not user.stripe_subscription_id:
        return None
    try:
        stripe.api_key = current_app.config["STRIPE_SECRET_KEY"]
        sub = stripe.Subscription.retrieve(user.stripe_subscription_id)
        dt = datetime.fromtimestamp(sub["current_period_end"], tz=timezone.utc)
        interval = sub["items"]["data"][0]["price"]["recurring"]["interval"]
        return {
            "interval": interval.capitalize(),
            "renewal_date": dt.strftime(f"%B {dt.day}, %Y"),
        }
    except Exception:
        return None
