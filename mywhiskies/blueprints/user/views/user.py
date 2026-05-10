from flask import flash, redirect, render_template, send_file, url_for
from flask_login import current_user, login_required, logout_user

from mywhiskies.blueprints.user import user_bp
from mywhiskies.forms.user import ChangePasswordForm, DeleteAccountForm
from mywhiskies.services.user.user import change_user_password, create_export_csv, delete_user_account


@user_bp.route("/<username:username>", methods=["GET"])
def bottles_redirect(username: str):
    return redirect(url_for("bottle.list", username=username))


@user_bp.route("/account")
@login_required
def account():
    return render_template(
        "user/account.html",
        title="My Whiskies Online: My Account",
        user=current_user,
        change_password_form=ChangePasswordForm(),
        delete_account_form=DeleteAccountForm(),
    )


@user_bp.route("/account/change_password", methods=["POST"])
@login_required
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if not change_user_password(current_user, form.current_password.data, form.password.data):
            flash("Current password is incorrect.", "danger")
    else:
        for field_errors in form.errors.values():
            for error in field_errors:
                flash(error, "danger")
    return redirect(url_for("user.account"))


@user_bp.route("/account/delete", methods=["POST"])
@login_required
def delete_account():
    form = DeleteAccountForm()
    if form.validate_on_submit():
        if form.confirm_username.data != current_user.username:
            flash("Username did not match. Account was not deleted.", "danger")
            return redirect(url_for("user.account"))
        delete_user_account(current_user)
        logout_user()
        flash("Your account has been permanently deleted.", "info")
        return redirect(url_for("core.main"))
    for field_errors in form.errors.values():
        for error in field_errors:
            flash(error, "danger")
    return redirect(url_for("user.account"))


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
