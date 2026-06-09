import stripe
from flask import current_app, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from mywhiskies.blueprints.payments import payments_bp
from mywhiskies.extensions import db


@payments_bp.route("/upgrade")
@login_required
def upgrade():
    if current_user.is_pro:
        flash("You're already on the Pro plan.", "info")
        return redirect(url_for("core.main"))
    return render_template(
        "payments/upgrade.html",
        title="Upgrade to Pro — My Whiskies Online",
        monthly_price_id=current_app.config["STRIPE_PRICE_MONTHLY"],
        annual_price_id=current_app.config["STRIPE_PRICE_ANNUAL"],
    )


@payments_bp.route("/upgrade/checkout", methods=["POST"])
@login_required
def checkout():
    price_id = request.form.get("price_id")
    valid_prices = {
        current_app.config["STRIPE_PRICE_MONTHLY"],
        current_app.config["STRIPE_PRICE_ANNUAL"],
    }
    if not price_id or price_id not in valid_prices:
        flash("Invalid pricing selection.", "danger")
        return redirect(url_for("payments.upgrade"))

    stripe.api_key = current_app.config["STRIPE_SECRET_KEY"]

    session_kwargs = {
        "line_items": [{"price": price_id, "quantity": 1}],
        "mode": "subscription",
        "client_reference_id": current_user.id,
        "success_url": url_for("payments.upgrade_success", _external=True) + "?session_id={CHECKOUT_SESSION_ID}",
        "cancel_url": url_for("payments.upgrade", _external=True),
    }
    if current_user.stripe_customer_id:
        session_kwargs["customer"] = current_user.stripe_customer_id
    else:
        session_kwargs["customer_email"] = current_user.email

    checkout_session = stripe.checkout.Session.create(**session_kwargs)
    return redirect(checkout_session.url, code=303)


@payments_bp.route("/upgrade/success")
@login_required
def upgrade_success():
    flash("You're now on Pro! Welcome to the good stuff.", "success")
    return redirect(url_for("core.main"))


@payments_bp.route("/stripe/webhook", methods=["POST"])
def webhook():
    payload = request.get_data()
    sig_header = request.headers.get("Stripe-Signature")
    stripe.api_key = current_app.config["STRIPE_SECRET_KEY"]

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, current_app.config["STRIPE_WEBHOOK_SECRET"])
    except (ValueError, stripe.error.SignatureVerificationError):
        return "", 400

    if event["type"] == "checkout.session.completed":
        _handle_checkout_completed(event["data"]["object"])
    elif event["type"] == "customer.subscription.deleted":
        _handle_subscription_deleted(event["data"]["object"])

    return "", 200


def _handle_checkout_completed(session):
    from mywhiskies.models import User

    user = db.session.get(User, session.get("client_reference_id"))
    if user:
        user.stripe_customer_id = session.get("customer")
        user.stripe_subscription_id = session.get("subscription")
        user.is_pro = True
        db.session.commit()


def _handle_subscription_deleted(subscription):
    from mywhiskies.models import User

    user = User.query.filter_by(stripe_subscription_id=subscription["id"]).first()
    if user:
        user.is_pro = False
        user.stripe_subscription_id = None
        db.session.commit()
