from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.responses import JSONResponse
from webauthn import (
    generate_registration_options,
    verify_registration_response,
    generate_authentication_options,
    verify_authentication_response,
    options_to_json,
)
from webauthn.helpers import (
    bytes_to_base64url,
    base64url_to_bytes,
    parse_authentication_credential_json,
    parse_registration_credential_json,
)
from webauthn.helpers.structs import (
    AuthenticatorSelectionCriteria,
    UserVerificationRequirement,
    RegistrationCredential,
    AuthenticationCredential,
)
from uuid import uuid4
import json
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

users_db = {}
challenges = {}

@router.post("/webauthn/registration/start")
async def start_registration(request: Request):
    # Generate a random user ID and username for demo
    user_id = str(uuid4())
    username = f"user_{user_id[:8]}"
    
    # Generate registration options
    options = generate_registration_options(
        rp_id="yourdomain.com",  # Replace with your domain
        rp_name="Your App Name",
        user_id=user_id,
        user_name=username,
        user_display_name=username,
        attestation="direct",
        authenticator_selection=AuthenticatorSelectionCriteria(
            user_verification=UserVerificationRequirement.PREFERRED
        ),
    )
    
    # Store the challenge for later verification
    challenges[user_id] = options.challenge
    
    # Store user data (in production, save to database)
    users_db[user_id] = {
        "id": user_id,
        "username": username,
        "public_key": None,
        "sign_count": 0
    }
    
    return JSONResponse(options_to_json(options))

@router.post("/webauthn/registration/complete")
async def complete_registration(request: Request):
    data = await request.json()
    credential = parse_registration_credential_json(json.dumps(data))
    user_id = credential.response.user.id
    
    if user_id not in challenges:
        raise HTTPException(status_code=400, detail="User not found")
    
    try:
        verification = verify_registration_response(
            credential=RegistrationCredential(
                id=credential.id,
                raw_id=base64url_to_bytes(credential.raw_id),
                response=credential.response,
                type=credential.type,
                client_extension_results=credential.client_extension_results,
            ),
            expected_challenge=challenges[user_id],
            expected_rp_id="yourdomain.com",  # Replace with your domain
            expected_origin="https://yourdomain.com",  # Replace with your origin
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    # Store the public key and other info
    users_db[user_id]["public_key"] = bytes_to_base64url(verification.credential_public_key)
    users_db[user_id]["sign_count"] = verification.sign_count
    users_db[user_id]["credential_id"] = bytes_to_base64url(verification.credential_id)
    
    del challenges[user_id]
    
    return {"status": "ok", "user_id": user_id}


@router.post("/webauthn/authentication/start")
async def start_authentication(request: Request):
    data = await request.json()
    user_id = data.get("user_id")
    
    if user_id not in users_db:
        raise HTTPException(status_code=404, detail="User not found")
    
    user = users_db[user_id]
    
    options = generate_authentication_options(
        rp_id="yourdomain.com",  # Replace with your domain
        allow_credentials=[
            {
                "id": user["credential_id"],
                "type": "public-key",
                # Add transports if known (e.g., ["usb", "nfc", "ble", "internal"])
            }
        ],
        user_verification=UserVerificationRequirement.PREFERRED,
    )
    
    challenges[user_id] = options.challenge
    
    return JSONResponse(options_to_json(options))

@router.post("/webauthn/authentication/complete")
async def complete_authentication(request: Request):
    data = await request.json()
    credential = parse_authentication_credential_json(json.dumps(data))
    user_id = credential.response.user_handle
    
    if user_id not in users_db or user_id not in challenges:
        raise HTTPException(status_code=400, detail="Invalid user")
    
    user = users_db[user_id]
    
    try:
        verification = verify_authentication_response(
            credential=AuthenticationCredential(
                id=credential.id,
                raw_id=base64url_to_bytes(credential.raw_id),
                response=credential.response,
                type=credential.type,
                client_extension_results=credential.client_extension_results,
            ),
            expected_challenge=challenges[user_id],
            expected_rp_id="yourdomain.com",  # Replace with your domain
            expected_origin="https://yourdomain.com",  # Replace with your origin
            credential_public_key=base64url_to_bytes(user["public_key"]),
            credential_current_sign_count=user["sign_count"],
            require_user_verification=True,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    # Update sign count
    users_db[user_id]["sign_count"] = verification.new_sign_count
    del challenges[user_id]
    
    # In a real app, you'd create a session here
    return {"status": "ok", "user_id": user_id}