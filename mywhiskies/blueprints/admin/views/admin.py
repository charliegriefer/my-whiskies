from functools import wraps

from flask import abort, current_app, flash, redirect, render_template, request, session, url_for
from flask_login import current_user, login_required, login_user
from markupsafe import Markup

from mywhiskies.blueprints.admin import admin_bp
from mywhiskies.extensions import db
from mywhiskies.forms.admin import AddUserForm
from mywhiskies.models import User
from mywhiskies.services.admin.admin import create_user, get_all_users, get_user_stats, toggle_user_active
from mywhiskies.services.auth.email import send_password_reset_email
from mywhiskies.services.user.user import delete_user_account


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated:
            return current_app.login_manager.unauthorized()
        if current_user.username.lower() != current_app.config.get("ADMIN_USERNAME", "").lower():
            abort(404)
        return f(*args, **kwargs)

    return decorated


@admin_bp.route("/users", methods=["GET", "POST"])
@login_required
@admin_required
def users():
    form = AddUserForm()

    if form.validate_on_submit():
        username = form.username.data.strip().lower()
        email = form.email.data.strip().lower()

        if db.session.execute(db.select(User).filter_by(username=username)).scalar_one_or_none():
            form.username.errors.append("Username already taken.")
        elif db.session.execute(db.select(User).filter_by(email=email)).scalar_one_or_none():
            form.email.errors.append("Email already in use.")
        else:
            user = create_user(username, email, form.password.data, form.pre_verified.data)
            flash(Markup(f"User <strong>{user.username}</strong> has been created."), "success")
            return redirect(url_for("admin.users"))

    _valid_sorts = {"username", "bottles", "registered", "last_login", "status"}
    sort = request.args.get("sort", "username")
    if sort not in _valid_sorts:
        sort = "username"
    direction = request.args.get("dir", "asc")
    if direction not in {"asc", "desc"}:
        direction = "asc"

    stats = get_user_stats()
    all_users = get_all_users(sort=sort, direction=direction)
    return render_template(
        "admin/users.html",
        title="Admin: Users",
        stats=stats,
        users=all_users,
        form=form,
        sort=sort,
        direction=direction,
        admin_username=current_app.config.get("ADMIN_USERNAME", "").lower(),
    )


@admin_bp.route("/users/<user_id>/toggle-active", methods=["POST"])
@login_required
@admin_required
def toggle_active(user_id: str):
    user = db.get_or_404(User, user_id)
    if user.username.lower() == current_app.config.get("ADMIN_USERNAME", "").lower():
        abort(403)
    is_now_active = toggle_user_active(user)
    verb = "enabled" if is_now_active else "disabled"
    flash(Markup(f"User <strong>{user.username}</strong> has been {verb}."), "success")
    return redirect(url_for("admin.users"))


@admin_bp.route("/users/<user_id>/reset-password", methods=["POST"])
@login_required
@admin_required
def reset_password(user_id: str):
    user = db.get_or_404(User, user_id)
    if user.username.lower() == current_app.config.get("ADMIN_USERNAME", "").lower():
        abort(403)
    send_password_reset_email(user)
    flash(Markup(f"Password reset email sent to <strong>{user.email}</strong>."), "success")
    return redirect(url_for("admin.users"))


@admin_bp.route("/users/<user_id>/delete", methods=["POST"])
@login_required
@admin_required
def delete_user(user_id: str):
    user = db.get_or_404(User, user_id)
    if user.username.lower() == current_app.config.get("ADMIN_USERNAME", "").lower():
        abort(403)
    confirm = request.form.get("confirm_username", "").strip()
    if confirm != user.username:
        flash("Username confirmation did not match. User was not deleted.", "danger")
        return redirect(url_for("admin.users"))
    username = user.username
    delete_user_account(user)
    flash(Markup(f"User <strong>{username}</strong> has been permanently deleted."), "success")
    return redirect(url_for("admin.users"))


@admin_bp.route("/users/<user_id>/impersonate", methods=["POST"])
@login_required
@admin_required
def impersonate(user_id: str):
    user = db.get_or_404(User, user_id)
    if user.username.lower() == current_app.config.get("ADMIN_USERNAME", "").lower():
        abort(403)
    session["real_user_id"] = current_user.id
    session["impersonating_as"] = user.id
    login_user(user)
    flash(
        Markup(
            f"You are viewing as <strong>{user.username}</strong>. "
            f'<a href="{url_for("admin.end_impersonation")}">End Session</a>'
        ),
        "warning",
    )
    return redirect(url_for("bottle.list", username=user.username))


@admin_bp.route("/end-impersonation")
def end_impersonation():
    real_user_id = session.pop("real_user_id", None)
    session.pop("impersonating_as", None)
    if real_user_id:
        real_user = db.get_or_404(User, real_user_id)
        login_user(real_user)
    return redirect(url_for("admin.users"))
