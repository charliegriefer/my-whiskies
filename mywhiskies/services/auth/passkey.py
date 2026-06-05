import webauthn
from webauthn.helpers import base64url_to_bytes, bytes_to_base64url
from webauthn.helpers.structs import (
    AuthenticationCredential,
    AuthenticatorAssertionResponse,
    AuthenticatorAttestationResponse,
    AuthenticatorSelectionCriteria,
    PublicKeyCredentialDescriptor,
    RegistrationCredential,
    ResidentKeyRequirement,
    UserVerificationRequirement,
)

from mywhiskies.extensions import db
from mywhiskies.models import PasskeyCredential


def get_registration_options(user, rp_id: str, rp_name: str):
    return webauthn.generate_registration_options(
        rp_id=rp_id,
        rp_name=rp_name,
        user_id=user.id.encode(),
        user_name=user.username,
        user_display_name=user.username,
        authenticator_selection=AuthenticatorSelectionCriteria(
            resident_key=ResidentKeyRequirement.PREFERRED,
            user_verification=UserVerificationRequirement.PREFERRED,
        ),
        exclude_credentials=[
            PublicKeyCredentialDescriptor(id=base64url_to_bytes(pk.credential_id)) for pk in user.passkeys
        ],
    )


def verify_and_save_registration(
    user, credential_json: dict, challenge: bytes, rp_id: str, origin: str, nickname: str = None
):
    credential = RegistrationCredential(
        id=credential_json["id"],
        raw_id=base64url_to_bytes(credential_json["rawId"]),
        response=AuthenticatorAttestationResponse(
            client_data_json=base64url_to_bytes(credential_json["response"]["clientDataJSON"]),
            attestation_object=base64url_to_bytes(credential_json["response"]["attestationObject"]),
        ),
    )
    verified = webauthn.verify_registration_response(
        credential=credential,
        expected_challenge=challenge,
        expected_rp_id=rp_id,
        expected_origin=origin,
        require_user_verification=False,
    )
    passkey = PasskeyCredential(
        user_id=user.id,
        credential_id=bytes_to_base64url(verified.credential_id),
        public_key=verified.credential_public_key,
        sign_count=verified.sign_count,
        nickname=nickname,
    )
    db.session.add(passkey)
    db.session.commit()
    return passkey


def get_authentication_options(rp_id: str):
    return webauthn.generate_authentication_options(
        rp_id=rp_id,
        user_verification=UserVerificationRequirement.PREFERRED,
    )


def verify_authentication(credential_json: dict, challenge: bytes, rp_id: str, origin: str):
    credential_id = credential_json["id"]
    passkey = PasskeyCredential.query.filter_by(credential_id=credential_id).first()
    if passkey is None:
        return None

    credential = AuthenticationCredential(
        id=credential_json["id"],
        raw_id=base64url_to_bytes(credential_json["rawId"]),
        response=AuthenticatorAssertionResponse(
            client_data_json=base64url_to_bytes(credential_json["response"]["clientDataJSON"]),
            authenticator_data=base64url_to_bytes(credential_json["response"]["authenticatorData"]),
            signature=base64url_to_bytes(credential_json["response"]["signature"]),
            user_handle=(
                base64url_to_bytes(credential_json["response"]["userHandle"])
                if credential_json["response"].get("userHandle")
                else None
            ),
        ),
    )
    verified = webauthn.verify_authentication_response(
        credential=credential,
        expected_challenge=challenge,
        expected_rp_id=rp_id,
        expected_origin=origin,
        credential_public_key=passkey.public_key,
        credential_current_sign_count=passkey.sign_count,
        require_user_verification=False,
    )
    passkey.sign_count = verified.new_sign_count
    db.session.commit()
    return passkey.user
