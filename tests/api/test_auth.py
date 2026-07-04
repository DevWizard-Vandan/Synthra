"""Tests for the auth router endpoints."""

from unittest.mock import MagicMock, patch
import pytest
from fastapi.testclient import TestClient

from synthra.execution.exceptions import (
    ExecutionAuthenticationError,
    VerificationRequiredError,
)


@pytest.fixture
def mock_service_state():
    """Fixture providing a mocked ServiceState."""
    state = MagicMock()
    state.auth_state = "Logged Out"
    state.auth_username = None
    state.auth_verification_url = None
    state.execution_client = MagicMock()

    async def async_noop() -> None:
        pass

    state.initialize = async_noop
    state.shutdown = async_noop
    return state


@pytest.fixture
def client(mock_service_state):
    """Provide a TestClient with mocked ServiceState initialization."""
    with patch(
        "synthra.api.app.ServiceState.get_instance", return_value=mock_service_state
    ):
        from synthra.api.app import create_app

        application = create_app()
        # Ensure service state is attached to application
        application.state.service = mock_service_state
        with TestClient(application, raise_server_exceptions=True) as tc:
            yield tc


def test_login_success(client, mock_service_state):
    """POST /auth/login returns success on valid credentials."""
    mock_service_state.execution_client.authenticate.return_value = None

    response = client.post(
        "/auth/login",
        json={"username": "test_user", "password": "test_password", "remember": True},
    )
    assert response.status_code == 200
    assert response.json() == {
        "status": "success",
        "message": None,
        "verification_url": None,
    }

    # Verify session cookie was set
    assert "session_id" in response.cookies
    assert mock_service_state.auth_state == "Authenticated"
    assert mock_service_state.auth_username == "test_user"


def test_login_invalid_credentials(client, mock_service_state):
    """POST /auth/login returns error on invalid credentials."""
    mock_service_state.execution_client.authenticate.side_effect = (
        ExecutionAuthenticationError("Auth failed")
    )

    response = client.post(
        "/auth/login",
        json={"username": "bad_user", "password": "bad_password", "remember": False},
    )
    assert response.status_code == 200
    assert response.json() == {
        "status": "error",
        "message": "Invalid username or password",
        "verification_url": None,
    }
    assert "session_id" not in response.cookies
    assert mock_service_state.auth_state == "Logged Out"


def test_login_verification_required(client, mock_service_state):
    """POST /auth/login returns verification_required status on MFA."""
    mock_service_state.execution_client.authenticate.side_effect = (
        VerificationRequiredError("https://mfa.example.test")
    )

    response = client.post(
        "/auth/login",
        json={"username": "mfa_user", "password": "mfa_password", "remember": False},
    )
    assert response.status_code == 200
    assert response.json() == {
        "status": "verification_required",
        "verification_url": "https://mfa.example.test",
        "message": None,
    }
    assert "session_id" not in response.cookies
    assert mock_service_state.auth_state == "Waiting for Biometric Verification"
    assert mock_service_state.auth_verification_url == "https://mfa.example.test"


def test_status_unauthenticated(client):
    """GET /auth/status returns unauthenticated when no session exists."""
    response = client.get("/auth/status")
    assert response.status_code == 200
    assert response.json() == {
        "authenticated": False,
        "username": None,
        "state": "Logged Out",
        "verification_url": None,
    }


def test_status_authenticated_and_logout(client, mock_service_state):
    """GET /auth/status returns authenticated and POST /auth/logout clears session."""
    mock_service_state.execution_client.authenticate.return_value = None

    # 1. Login to establish session
    login_resp = client.post(
        "/auth/login",
        json={"username": "user1", "password": "pass1", "remember": False},
    )
    assert login_resp.status_code == 200

    # 2. Get status with cookie
    status_resp = client.get("/auth/status")
    assert status_resp.status_code == 200
    assert status_resp.json() == {
        "authenticated": True,
        "username": "user1",
        "state": "Authenticated",
        "verification_url": None,
    }

    # 3. Invalidate via logout
    logout_resp = client.post("/auth/logout")
    assert logout_resp.status_code == 200
    assert logout_resp.json() == {"status": "success", "message": None}

    # Cookie should be deleted
    # 4. Status should now be unauthenticated
    status_resp_after = client.get("/auth/status")
    assert status_resp_after.status_code == 200
    assert status_resp_after.json()["authenticated"] is False
