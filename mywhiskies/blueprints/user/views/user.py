from flask import render_template
from flask_login import current_user, login_required

from mywhiskies.blueprints.user import user_bp


@user_bp.route("/account")
@login_required
def account():
    return render_template(
        "user/account.html",
        title="My Whiskies Online: My Account",
        user=current_user,
    )
