from flask import flash, redirect, render_template, send_file, url_for
from flask_login import current_user, login_required, logout_user

from mywhiskies.blueprints.user import user_bp
from mywhiskies.forms.user import ChangeEmailForm, ChangePasswordForm, DeleteAccountForm, PrivacyForm
from mywhiskies.models import User
from mywhiskies.services.auth.email import send_email_change_confirmation
from mywhiskies.services.user.user import (
    apply_email_change,
    change_user_password,
    create_export_csv,
    delete_user_account,
    is_email_taken,
    set_account_privacy,
)


@user_bp.route("/<username:username>", methods=["GET"])
def bottles_redirect(username: str):
    return redirect(url_for("bottle.list", username=username))


@user_bp.route("/account")
@login_required
def account():
    privacy_form = PrivacyForm()
    privacy_form.is_private.data = current_user.is_private
    return render_template(
        "user/account.html",
        title="My Whiskies Online: My Account",
        user=current_user,
        privacy_form=privacy_form,
        change_email_form=ChangeEmailForm(),
        change_password_form=ChangePasswordForm(),
        delete_account_form=DeleteAccountForm(),
    )


@user_bp.route("/account/privacy", methods=["POST"])
@login_required
def privacy():
    form = PrivacyForm()
    if form.validate_on_submit():
        set_account_privacy(current_user, form.is_private.data)
    return redirect(url_for("user.account"))


@user_bp.route("/account/change_email", methods=["POST"])
@login_required
def change_email():
    form = ChangeEmailForm()
    if form.validate_on_submit():
        new_email = form.email.data.strip().lower()
        if new_email == current_user.email.lower():
            flash("That is already your current e-mail address.", "warning")
            return redirect(url_for("user.account"))
        if is_email_taken(new_email):
            flash("That e-mail address is already in use.", "danger")
            return redirect(url_for("user.account"))
        send_email_change_confirmation(current_user, new_email)
        flash(f"A confirmation email has been sent to {new_email}. Click the link to complete the change.", "info")
    else:
        for field_errors in form.errors.values():
            for error in field_errors:
                flash(error, "danger")
    return redirect(url_for("user.account"))


@user_bp.route("/account/confirm_email_change/<token>")
@login_required
def confirm_email_change(token: str):
    user, new_email = User.verify_email_change_token(token)
    if not user or user.id != current_user.id:
        flash("The confirmation link is invalid or has expired.", "danger")
        return redirect(url_for("user.account"))
    apply_email_change(current_user, new_email)
    return redirect(url_for("user.account"))


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
