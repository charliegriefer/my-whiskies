from flask import current_app, jsonify, request, session
from flask_login import current_user, login_required, login_user
from webauthn import options_to_json
from webauthn.helpers import base64url_to_bytes, bytes_to_base64url

from mywhiskies.blueprints.auth import auth
from mywhiskies.services.auth.login import determine_next_page
from mywhiskies.services.auth.passkey import (
    get_authentication_options,
    get_registration_options,
    verify_and_save_registration,
    verify_authentication,
)


@auth.route("/passkey/register/begin", methods=["POST"])
@login_required
def passkey_register_begin():
    options = get_registration_options(
        current_user,
        rp_id=current_app.config["WEBAUTHN_RP_ID"],
        rp_name=current_app.config["WEBAUTHN_RP_NAME"],
    )
    session["passkey_register_challenge"] = bytes_to_base64url(options.challenge)
    return options_to_json(options), 200, {"Content-Type": "application/json"}


@auth.route("/passkey/register/complete", methods=["POST"])
@login_required
def passkey_register_complete():
    challenge_b64 = session.pop("passkey_register_challenge", None)
    if not challenge_b64:
        return jsonify({"error": "No active registration challenge."}), 400
    challenge = base64url_to_bytes(challenge_b64)

    credential_json = request.get_json()
    nickname = credential_json.pop("nickname", None) or None

    try:
        verify_and_save_registration(
            user=current_user,
            credential_json=credential_json,
            challenge=challenge,
            rp_id=current_app.config["WEBAUTHN_RP_ID"],
            origin=current_app.config["WEBAUTHN_ORIGIN"],
            nickname=nickname,
        )
    except Exception as e:
        current_app.logger.warning(f"Passkey registration failed for {current_user.username}: {e}")
        return jsonify({"error": "Registration failed. Please try again."}), 400

    return jsonify({"success": True})


@auth.route("/passkey/authenticate/begin", methods=["POST"])
def passkey_authenticate_begin():
    options = get_authentication_options(rp_id=current_app.config["WEBAUTHN_RP_ID"])
    session["passkey_auth_challenge"] = bytes_to_base64url(options.challenge)
    return options_to_json(options), 200, {"Content-Type": "application/json"}


@auth.route("/passkey/authenticate/complete", methods=["POST"])
def passkey_authenticate_complete():
    challenge_b64 = session.pop("passkey_auth_challenge", None)
    if not challenge_b64:
        return jsonify({"error": "No active authentication challenge."}), 400
    challenge = base64url_to_bytes(challenge_b64)

    credential_json = request.get_json()

    try:
        user = verify_authentication(
            credential_json=credential_json,
            challenge=challenge,
            rp_id=current_app.config["WEBAUTHN_RP_ID"],
            origin=current_app.config["WEBAUTHN_ORIGIN"],
        )
    except Exception as e:
        current_app.logger.warning(f"Passkey authentication failed: {e}")
        return jsonify({"error": "Authentication failed. Please try again."}), 400

    if user is None:
        return jsonify({"error": "Unknown credential."}), 401

    login_user(user)
    current_app.logger.info(f"User {user.username} logged in via passkey")
    next_page = determine_next_page(user, request.args.get("next"))
    return jsonify({"success": True, "redirect": next_page})
