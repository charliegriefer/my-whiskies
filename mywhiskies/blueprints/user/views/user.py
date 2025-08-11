from flask import redirect, render_template, send_file, url_for
from flask_login import current_user, login_required

from mywhiskies.blueprints.user import user_bp
from mywhiskies.services.user.user import create_export_csv


@user_bp.route("/<string:username>", methods=["GET"])
def bottles_redirect(username: str):
    return redirect(url_for("bottle.list", username=username))


@user_bp.route("/account")
@login_required
def account():
    return render_template(
        "user/account.html",
        title="My Whiskies Online: My Account",
        user=current_user,
    )


@user_bp.route("/export_data")
@login_required
def export_data():
    create_export_csv(current_user)

    return send_file(
        f"/tmp/{current_user.id}.csv",
        as_attachment=True,
        mimetype="text/csv",
        download_name=f"my_whiskies_{current_user.username}.csv",
    )
