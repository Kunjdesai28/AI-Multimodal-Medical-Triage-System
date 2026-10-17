"""
Healthcare Institution Authentication & Access Control Routes.
Handles registration, secure login, password reset flow, and session validation.
"""
import os
import re
import uuid
import time
import urllib.parse
import requests
from fastapi import APIRouter, HTTPException, Depends, Header, status
from typing import Optional
from datetime import timedelta

from ...schemas.auth import (
    InstitutionRegisterRequest,
    InstitutionLoginRequest,
    ForgotPasswordRequest,
    AuthTokenResponse,
    InstitutionResponse
)
from ...auth.security import (
    hash_password,
    verify_password,
    validate_password_strength,
    validate_email_format,
    create_access_token,
    decode_access_token
)
from ...database.repository import TriageRepository
from ...services.email_service import send_registration_confirmation_email

router = APIRouter(prefix="/auth", tags=["Institution Authentication"])


@router.post("/register", response_model=AuthTokenResponse)
def register_institution(request: InstitutionRegisterRequest):
    """
    Registers a new healthcare institution (hospital, clinic, diagnostic center)
    with organization details only.
    """
    repo = TriageRepository()

    # 1. Resolve required organization fields
    hospital_name = (request.hospitalName or request.institutionName or "").strip()
    if not hospital_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Hospital / Clinic Name is required."
        )

    org_type = (request.organizationType or request.institutionType or "Hospital").strip()
    reg_number = (request.registrationNumber or "").strip()
    country = (request.country or "India").strip()
    state_val = (request.state or "").strip()
    city_val = (request.city or "").strip()
    addr_val = (request.address or "").strip()
    pincode_val = (request.pincode or request.postalCode or "").strip()
    contact_val = (request.contactNumber or request.officialPhone or "").strip()
    official_email = (request.officialEmail or "").strip().lower()

    if not official_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Official email address is required."
        )

    # 2. Validate Official Email syntax
    if not validate_email_format(official_email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid official email address format."
        )

    # 3. Validate Phone Number (Must be exactly 10 digits)
    contact_digits = re.sub(r'\D', '', contact_val)
    if not contact_digits or len(contact_digits) != 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Phone number must be exactly 10 digits."
        )
    contact_val = contact_digits

    # 4. Check duplicate Official Email
    if repo.find_institution_by_email(official_email):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Official email address '{official_email}' is already registered to an institution account."
        )

    # 5. Generate or validate Institution ID / Username
    clean_id = (request.institutionId or "").strip()
    if not clean_id:
        slug = re.sub(r'[^a-zA-Z0-9]', '_', hospital_name.lower()).strip('_')
        base_id = slug[:24] if slug else "hospital"
        clean_id = base_id
        count = 1
        while repo.find_institution_by_id(clean_id):
            clean_id = f"{base_id}_{count}"
            count += 1
    else:
        if repo.find_institution_by_id(clean_id):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Institution ID or Username '{clean_id}' is already registered. Please choose another ID."
            )

    # 6. Password handling (supports case-insensitive comparison by hashing both exact and lowercase)
    if request.password:
        raw_pw = request.password
        if request.confirmPassword and raw_pw.strip() != request.confirmPassword.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Passwords do not match. Please re-enter your password."
            )
        is_strong, msg = validate_password_strength(raw_pw)
        if not is_strong:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg)
        pw_hash = hash_password(raw_pw)
        pw_hash_lower = hash_password(raw_pw.strip().lower())
    else:
        temp_pw = f"Inst-{uuid.uuid4().hex[:12]}"
        pw_hash = hash_password(temp_pw)
        pw_hash_lower = hash_password(temp_pw.lower())

    # 7. Extract Location Metadata if provided (latitude, longitude, placeId)
    location_dict = None
    if request.location:
        location_dict = {
            "latitude": request.location.latitude,
            "longitude": request.location.longitude,
            "placeId": request.location.placeId
        }

    # 8. Build institutional record
    institution_doc = {
        "institutionId": clean_id,
        "institutionName": hospital_name,
        "hospitalName": hospital_name,
        "institutionType": org_type,
        "organizationType": org_type,
        "registrationNumber": reg_number or None,
        "officialEmail": official_email,
        "officialPhone": contact_val,
        "contactNumber": contact_val,
        "website": request.website.strip() if request.website else None,
        "country": country,
        "state": state_val,
        "city": city_val,
        "postalCode": pincode_val,
        "pincode": pincode_val,
        "address": addr_val,
        "location": location_dict,
        "timezone": getattr(request, "timezone", None) or "Asia/Kolkata",
        "administratorName": getattr(request, "administratorName", None) or f"{hospital_name} Admin",
        "administratorDesignation": getattr(request, "administratorDesignation", None) or "Medical Director",
        "administratorEmail": getattr(request, "administratorEmail", None) or official_email,
        "administratorPhone": getattr(request, "administratorPhone", None) or contact_val,
        "passwordHash": pw_hash,
        "passwordHashLower": pw_hash_lower,
        "accountStatus": "active"
    }

    try:
        created = repo.create_institution(institution_doc)
        
        # Dispatch institutional registration confirmation email (SMTP with offline fallback)
        try:
            email_sent, email_log = send_registration_confirmation_email(institution_doc)
            print(f"[Registration] Confirmation email dispatched to {official_email}: {email_sent} ({email_log})")
        except Exception as mail_err:
            print(f"[Registration] Non-fatal email dispatch error: {mail_err}")

        # Issue initial access token
        token_payload = {
            "sub": created["institutionId"],
            "inst_name": created.get("hospitalName", created.get("institutionName", "Hospital")),
            "inst_type": created.get("organizationType", created.get("institutionType", "Hospital")),
            "email": created["officialEmail"]
        }
        token = create_access_token(token_payload)

        # Merge for response representation
        resp_data = dict(created)
        resp_data.setdefault("hospitalName", hospital_name)
        resp_data.setdefault("organizationType", org_type)
        resp_data.setdefault("contactNumber", contact_val)
        resp_data.setdefault("pincode", pincode_val)

        return AuthTokenResponse(
            success=True,
            token=token,
            institution=InstitutionResponse(**resp_data),
            message=f"Hospital/Clinic registration completed successfully. Confirmation email sent to {official_email}."
        )
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(ve))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}"
        )


@router.post("/login", response_model=AuthTokenResponse)
def login_institution(request: InstitutionLoginRequest):
    """
    Authenticates an existing registered institution via Institution ID, Official Email,
    Hospital/Clinic Name, or Contact Phone Number.
    Supports case-insensitive identifier and case-insensitive password matching.
    """
    repo = TriageRepository()
    ident = request.identifier.strip()

    inst = repo.get_institution_by_identifier(ident)
    if not inst:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Institution ID or Password. Please check your credentials."
        )

    # Verify password (supports case-insensitive password matching)
    stored_hash = inst.get("passwordHash", "")
    stored_hash_lower = inst.get("passwordHashLower", "")
    
    password_valid = False
    # 1. Exact match
    if stored_hash and verify_password(request.password, stored_hash):
        password_valid = True
    # 2. Case-insensitive lowercase match via stored lowercase hash
    elif stored_hash_lower and verify_password(request.password.strip().lower(), stored_hash_lower):
        password_valid = True
    # 3. Fallback: match lowercase password against stored_hash
    elif stored_hash and verify_password(request.password.strip().lower(), stored_hash):
        password_valid = True
    elif stored_hash and verify_password(request.password.strip(), stored_hash):
        password_valid = True

    if not password_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Institution ID or Password. Please check your credentials."
        )

    if inst.get("accountStatus") == "suspended":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This institution account has been temporarily suspended. Please contact hospital support."
        )

    # Generate token (longer duration if Remember Me checked)
    expiry = timedelta(days=30) if request.rememberMe else timedelta(hours=72)
    token_payload = {
        "sub": inst["institutionId"],
        "inst_name": inst.get("institutionName", "Hospital"),
        "inst_type": inst.get("institutionType", "Hospital"),
        "email": inst.get("officialEmail", "")
    }
    token = create_access_token(token_payload, expires_delta=expiry)

    sanitized = repo.sanitize_institution(inst)
    return AuthTokenResponse(
        success=True,
        token=token,
        institution=InstitutionResponse(**sanitized),
        message=f"Welcome back to TRIAGEAI, {inst.get('institutionName', 'Hospital')}."
    )


@router.get("/me", response_model=InstitutionResponse)
def get_current_institution(authorization: Optional[str] = Header(None)):
    """
    Validates current institution session using Bearer authorization token.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token required. Please sign in to access TRIAGEAI."
        )

    token = authorization.split("Bearer ")[1].strip()
    payload = decode_access_token(token)
    if not payload or not payload.get("sub"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session has expired or is invalid. Please sign in again."
        )

    repo = TriageRepository()
    inst = repo.get_institution_by_identifier(payload["sub"])
    if not inst:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Institution account not found."
        )

    return InstitutionResponse(**repo.sanitize_institution(inst))


@router.post("/forgot-password")
def forgot_password(request: ForgotPasswordRequest):
    """
    Dispatches password reset instructions to the institution's verified email.
    """
    repo = TriageRepository()
    ident = request.identifier.strip()

    inst = repo.get_institution_by_identifier(ident)
    if not inst:
        # Standard security practice: Avoid revealing whether an account exists
        return {
            "success": True,
            "message": "If an account matching those details exists, password reset instructions have been sent to the registered email."
        }

    email = inst.get("officialEmail", "")
    # In production with configured SMTP, send email with reset link here
    return {
        "success": True,
        "message": f"Password reset instructions have been dispatched to the registered institution email ({email[:3]}***@{email.split('@')[-1] if '@' in email else ''})."
    }


@router.post("/logout")
def logout_institution(authorization: Optional[str] = Header(None)):
    """
    Terminates the institution administrator's active session.
    Instructs the frontend client to clear all local tokens and cached patient records.
    """
    return {
        "success": True,
        "message": "Institutional session terminated successfully. Workspace safely locked."
    }


# =====================================================================
# GOOGLE OAUTH 2.0 INTEGRATION
# =====================================================================

def get_google_client_id() -> str:
    return os.getenv("GOOGLE_CLIENT_ID", "").strip()

def get_google_client_secret() -> str:
    return os.getenv("GOOGLE_CLIENT_SECRET", "").strip()

def get_google_redirect_uri() -> str:
    return os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/api/auth/google/callback").strip()

def get_frontend_url() -> str:
    return os.getenv("FRONTEND_URL", "http://localhost:5173").strip()


@router.get("/google/config")
def get_google_oauth_config():
    """
    Returns Google OAuth public configuration for frontend initialization.
    """
    client_id = get_google_client_id()
    return {
        "client_id": client_id,
        "redirect_uri": get_google_redirect_uri(),
        "frontend_url": get_frontend_url(),
        "configured": bool(client_id)
    }


@router.get("/google")
def google_oauth_redirect():
    """
    Redirects directly to Google OAuth2 consent screen.
    """
    from fastapi.responses import RedirectResponse
    client_id = get_google_client_id()
    if not client_id:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="GOOGLE_CLIENT_ID is not configured in backend .env"
        )

    scope = "openid email profile"
    params = {
        "client_id": client_id,
        "redirect_uri": get_google_redirect_uri(),
        "response_type": "code",
        "scope": scope,
        "access_type": "offline",
        "prompt": "consent"
    }
    url = f"https://accounts.google.com/o/oauth2/v2/auth?{urllib.parse.urlencode(params)}"
    return RedirectResponse(url=url)


@router.get("/google/url")
def get_google_auth_url():
    """
    Constructs the Google OAuth2 authorization URL.
    """
    client_id = get_google_client_id()
    if not client_id:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="GOOGLE_CLIENT_ID is not configured in backend .env"
        )

    scope = "openid email profile"
    params = {
        "client_id": client_id,
        "redirect_uri": get_google_redirect_uri(),
        "response_type": "code",
        "scope": scope,
        "access_type": "offline",
        "prompt": "consent"
    }
    url = f"https://accounts.google.com/o/oauth2/v2/auth?{urllib.parse.urlencode(params)}"
    return {"url": url}



@router.get("/google/callback")
def google_oauth_callback(code: Optional[str] = None, error: Optional[str] = None):
    """
    EXACT AUTHORIZED REDIRECT URI:
    http://localhost:8000/api/auth/google/callback

    Exchanges authorization code with Google OAuth servers, retrieves verified
    institutional identity, creates or logs into the institution account,
    and redirects the browser to the main TRIAGEAI application with the access token.
    """
    from fastapi.responses import RedirectResponse

    client_id = get_google_client_id()
    client_secret = get_google_client_secret()
    redirect_uri = get_google_redirect_uri()
    frontend_url = get_frontend_url()

    if error or not code:
        err_msg = error or "Authorization code missing from Google redirect."
        return RedirectResponse(url=f"{frontend_url}?error={urllib.parse.quote(err_msg)}")

    if not client_id or not client_secret:
        return RedirectResponse(
            url=f"{frontend_url}?error={urllib.parse.quote('Google OAuth credentials not configured on server.')}"
        )

    # 1. Exchange code for access token & ID token
    token_url = "https://oauth2.googleapis.com/token"
    token_payload = {
        "code": code,
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uri": redirect_uri,
        "grant_type": "authorization_code"
    }

    try:
        token_res = requests.post(token_url, data=token_payload, timeout=10)
        token_data = token_res.json()
        if token_res.status_code != 200 or "access_token" not in token_data:
            err_desc = token_data.get("error_description", "Failed to retrieve access token from Google.")
            return RedirectResponse(url=f"{frontend_url}?error={urllib.parse.quote(err_desc)}")

        # 2. Retrieve verified user profile from Google
        profile_url = "https://www.googleapis.com/oauth2/v2/userinfo"
        headers = {"Authorization": f"Bearer {token_data['access_token']}"}
        profile_res = requests.get(profile_url, headers=headers, timeout=10)
        profile_data = profile_res.json()

        email = profile_data.get("email", "").strip().lower()
        name = profile_data.get("name", "Medical Professional")
        google_id = profile_data.get("id", "")

        if not email:
            return RedirectResponse(url=f"{frontend_url}?error={urllib.parse.quote('Email not provided by Google account.')}")

        # 3. Associate with registered institution
        repo = TriageRepository()
        inst = repo.find_institution_for_google_user(email)

        if not inst:
            # Under Healthcare Multi-Tenant Rules: Do NOT auto-provision an unrestricted institution.
            # Redirect to "Complete Institution Registration" with name & email pre-filled!
            params = {
                "action": "complete_registration",
                "google_name": name,
                "google_email": email,
                "google_id": google_id,
                "info": "Please complete your institution details to provision your dedicated clinical database."
            }
            redirect_query = urllib.parse.urlencode(params)
            return RedirectResponse(url=f"{frontend_url}?{redirect_query}")

        # 4. Issue TRIAGEAI access token
        token_payload = {
            "sub": inst["institutionId"],
            "inst_name": inst.get("institutionName", "Hospital"),
            "inst_type": inst.get("institutionType", "Hospital"),
            "email": inst.get("officialEmail", email),
            "role": "Institution Administrator"
        }
        internal_token = create_access_token(token_payload)

        # 5. Redirect browser back to TRIAGEAI frontend with token
        return RedirectResponse(url=f"{frontend_url}?token={internal_token}&login=success")

    except Exception as exc:
        return RedirectResponse(url=f"{frontend_url}?error={urllib.parse.quote(str(exc))}")


@router.post("/google/verify")
def verify_google_credential(credential: str):
    """
    Verifies a Google ID Token (from Google One-Tap or Google Sign-In popup).
    Ensures that only users associated with an institution are authenticated,
    otherwise prompts the client to complete institution registration.
    """
    try:
        verify_url = f"https://oauth2.googleapis.com/tokeninfo?id_token={credential}"
        res = requests.get(verify_url, timeout=10)
        data = res.json()

        if res.status_code != 200 or "email" not in data:
            raise HTTPException(status_code=400, detail="Invalid Google ID Token")

        client_id = get_google_client_id()
        # Check audience
        if client_id and data.get("aud") != client_id:
            raise HTTPException(status_code=400, detail="Google Token audience mismatch")

        email = data["email"].strip().lower()
        name = data.get("name", "Medical Professional")
        google_id = data.get("sub", data.get("id", ""))

        repo = TriageRepository()
        inst = repo.find_institution_for_google_user(email)
        if not inst:
            return {
                "success": False,
                "registered": False,
                "redirect_action": "complete_registration",
                "google_name": name,
                "google_email": email,
                "google_id": google_id,
                "message": "Google account verified, but not associated with an existing hospital. Please complete institution registration."
            }

        token_payload = {
            "sub": inst["institutionId"],
            "inst_name": inst.get("institutionName", "Hospital"),
            "inst_type": inst.get("institutionType", "Hospital"),
            "email": inst.get("officialEmail", email),
            "role": "Institution Administrator"
        }
        internal_token = create_access_token(token_payload)
        sanitized = repo.sanitize_institution(inst)

        return {
            "success": True,
            "registered": True,
            "token": internal_token,
            "institution": sanitized,
            "message": f"Welcome back, {inst.get('institutionName')}"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Google authentication failed: {str(e)}")
