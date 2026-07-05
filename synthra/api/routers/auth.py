"""Authentication router — login, logout, status endpoints."""

import uuid
import logging
from typing import Optional
from fastapi import APIRouter, Request, Response
from pydantic import BaseModel, SecretStr

from synthra.execution.models import WorldQuantCredentials
from synthra.execution.exceptions import (
    ExecutionAuthenticationError,
    VerificationRequiredError,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])


# Simple in-memory session store (maps secure session_id to username)
ACTIVE_SESSIONS: dict[str, str] = {}


class LoginRequest(BaseModel):
    """Payload schema for auth/login."""

    username: Optional[str] = None
    password: Optional[str] = None
    token: Optional[str] = None
    remember: bool = False


class LoginResponse(BaseModel):
    """Response schema for auth/login."""

    status: str
    message: Optional[str] = None
    verification_url: Optional[str] = None


class LogoutResponse(BaseModel):
    """Response schema for auth/logout."""

    status: str
    message: Optional[str] = None


class AuthStatusResponse(BaseModel):
    """Response schema for auth/status."""

    authenticated: bool
    username: Optional[str] = None
    state: str
    verification_url: Optional[str] = None


@router.post("/login", response_model=LoginResponse)
async def login(
    login_req: LoginRequest, request: Request, response: Response
) -> LoginResponse:
    """Authenticate credentials or session token against WorldQuant API client."""
    service = getattr(request.app.state, "service", None)
    if not service:
        return LoginResponse(status="error", message="ServiceState not initialized")

    if login_req.token:
        token = login_req.token.strip()
        if token.lower().startswith("bearer "):
            token = token[7:].strip()

        # Try to parse the email out of the JWT token
        username = "Token User"
        try:
            import base64
            import json
            parts = token.split(".")
            if len(parts) == 3:
                payload_b64 = parts[1]
                payload_b64 += "=" * ((4 - len(payload_b64) % 4) % 4)
                payload = json.loads(base64.b64decode(payload_b64).decode("utf-8"))
                username = payload.get("email") or payload.get("sub") or "Token User"
        except Exception:
            pass

        service.auth_username = username
        service.execution_client._session_headers = {
            "Authorization": f"Bearer {token}"
        }

        # Success path for token login
        session_id = str(uuid.uuid4())
        ACTIVE_SESSIONS[session_id] = username

        response.set_cookie(
            key="session_id",
            value=session_id,
            httponly=True,
            secure=False,
            samesite="lax",
        )

        service.auth_state = "Authenticated"
        service.auth_verification_url = None
        return LoginResponse(status="success")

    # Standard credentials-based path
    if not login_req.username or not login_req.password:
        return LoginResponse(status="error", message="Username and password are required")

    service.auth_state = "Authenticating"
    service.auth_username = login_req.username
    service.auth_verification_url = None

    try:
        # Update execution client credentials
        creds = WorldQuantCredentials(
            username=login_req.username,
            password=SecretStr(login_req.password),
        )
        service.execution_client._credentials = creds
        service.execution_client._session_headers = {}

        # Attempt authentication
        service.execution_client.authenticate()

        # Success path
        session_id = str(uuid.uuid4())
        ACTIVE_SESSIONS[session_id] = login_req.username

        # Set secure HTTP-only cookie
        response.set_cookie(
            key="session_id",
            value=session_id,
            httponly=True,
            secure=False,  # False allows local HTTP dev/testing
            samesite="lax",
        )

        service.auth_state = "Authenticated"
        return LoginResponse(status="success")

    except VerificationRequiredError as e:
        service.auth_state = "Waiting for Biometric Verification"
        service.auth_verification_url = e.verification_url
        return LoginResponse(
            status="verification_required",
            verification_url=e.verification_url,
        )

    except ExecutionAuthenticationError:
        service.auth_state = "Logged Out"
        service.auth_username = None
        return LoginResponse(status="error", message="Invalid username or password")

    except Exception as e:
        service.auth_state = "Logged Out"
        service.auth_username = None
        logger.error("Authentication error occurred", exc_info=True)
        return LoginResponse(status="error", message=str(e))


@router.get("/status", response_model=AuthStatusResponse)
async def status(request: Request) -> AuthStatusResponse:
    """Retrieve current authentication status."""
    service = getattr(request.app.state, "service", None)
    if not service:
        return AuthStatusResponse(authenticated=False, state="Logged Out")

    session_id = request.cookies.get("session_id")
    if session_id and session_id in ACTIVE_SESSIONS:
        return AuthStatusResponse(
            authenticated=True,
            username=service.auth_username,
            state=service.auth_state,
            verification_url=service.auth_verification_url,
        )

    # We do NOT run auto-authenticate here to prevent CAPTCHAs.
    # Return current state of authentication process.
    return AuthStatusResponse(
        authenticated=False,
        username=service.auth_username,
        state=service.auth_state,
        verification_url=service.auth_verification_url,
    )


@router.post("/logout", response_model=LogoutResponse)
async def logout(request: Request, response: Response) -> LogoutResponse:
    """Invalidate local session cookie."""
    service = getattr(request.app.state, "service", None)
    if service:
        service.auth_state = "Logged Out"
        service.auth_username = None
        service.auth_verification_url = None

    session_id = request.cookies.get("session_id")
    if session_id in ACTIVE_SESSIONS:
        del ACTIVE_SESSIONS[session_id]

    response.delete_cookie("session_id")
    return LogoutResponse(status="success")
