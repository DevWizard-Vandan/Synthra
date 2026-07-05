"""WorldQuant BRAIN execution client."""

import base64
import logging
import time
from typing import Mapping, cast
from urllib.parse import urljoin

from synthra.core.domain import SimulationRequest
from synthra.execution.exceptions import (
    ExecutionAuthenticationError,
    ExecutionClientError,
    ExecutionRateLimitError,
    ExecutionServerError,
    VerificationRequiredError,
)
from synthra.execution.models import (
    SimulationHandle,
    WorldQuantCredentials,
    WorldQuantExecutionConfig,
)
from synthra.execution.transport import (
    HttpResponse,
    HttpTransport,
    JsonObject,
    JsonValue,
    UrllibHttpTransport,
)

logger = logging.getLogger(__name__)


class WorldQuantExecutionClient:
    """Client for WorldQuant BRAIN authentication and simulation requests."""

    def __init__(
        self,
        credentials: WorldQuantCredentials,
        config: WorldQuantExecutionConfig | None = None,
        transport: HttpTransport | None = None,
    ) -> None:
        """Initialize the execution client with injected dependencies.

        Args:
            credentials: WorldQuant BRAIN username and password.
            config: Runtime configuration. Defaults to standard API paths.
            transport: HTTP transport. Tests should inject a mock transport.
        """
        self._credentials = credentials
        self._config = config or WorldQuantExecutionConfig()
        self._transport = transport or UrllibHttpTransport()
        self._session_headers: dict[str, str] = {}

    def authenticate(self) -> None:
        """Authenticate with the platform and store reusable session headers.

        Raises:
            ExecutionAuthenticationError: If credentials are rejected.
            ExecutionServerError: If server errors persist after retries.
        """
        auth_payload = (
            f"{self._credentials.username}:"
            f"{self._credentials.password.get_secret_value()}"
        ).encode("utf-8")
        headers = {
            "Authorization": f"Basic {base64.b64encode(auth_payload).decode('ascii')}",
            "Accept": "application/json",
        }
        response = self._request_with_retries(
            "POST",
            self._url(self._config.auth_path),
            headers,
            None,
        )
        payload = {}
        try:
            payload = response.json_object()
        except Exception:
            pass

        print(f"DEBUG_WQ_AUTH_STATUS: {response.status_code}", flush=True)
        print(f"DEBUG_WQ_AUTH_BODY: {response.body.decode('utf-8', errors='ignore')}", flush=True)

        verification_url = payload.get("verification_url") or payload.get("mfa_url")
        inquiry_id = payload.get("inquiry")
        if isinstance(inquiry_id, str) and inquiry_id.startswith("inq_"):
            verification_url = f"https://worldquantbrain.withpersona.com/inquiry?inquiry-id={inquiry_id}"

        if isinstance(verification_url, str) and verification_url:
            raise VerificationRequiredError(verification_url)

        if response.status_code not in {200, 201, 204}:
            if response.status_code in {401, 403}:
                raise ExecutionAuthenticationError(
                    "WorldQuant authentication was rejected."
                )
            self._raise_for_status(response)

        session_headers: dict[str, str] = {}
        token = self._extract_token(response)
        if token is not None:
            session_headers["Authorization"] = f"Bearer {token}"
        cookie = self._header(response.headers, "Set-Cookie")
        if cookie is not None:
            session_headers["Cookie"] = cookie
        if not session_headers:
            logger.warning("Authentication response did not include token or cookie.")
        self._session_headers = session_headers

    def submit_simulation(self, request: SimulationRequest) -> SimulationHandle:
        """Submit a simulation request and return its platform handle.

        Args:
            request: System-agnostic simulation parameters.

        Returns:
            The accepted simulation handle.
        """
        if not self._session_headers:
            self.authenticate()

        response = self._request_with_retries(
            "POST",
            self._url(self._config.simulations_path),
            self._json_headers(),
            cast(JsonObject, request.model_dump(mode="json")),
        )

        # Automatic session refresh on 401/403
        if response.status_code in {401, 403}:
            logger.info("Session expired/unauthorized. Re-authenticating...")
            self.authenticate()
            response = self._request_with_retries(
                "POST",
                self._url(self._config.simulations_path),
                self._json_headers(),
                cast(JsonObject, request.model_dump(mode="json")),
            )

        if response.status_code not in {200, 201, 202}:
            self._raise_for_status(response)

        payload = response.json_object()
        location = self._header(response.headers, "Location")
        simulation_id = self._string_field(payload, "id")
        status = self._string_field(payload, "status") or "submitted"

        if location is None:
            if simulation_id is None:
                raise ExecutionClientError(
                    "Simulation response must include an id or Location header."
                )
            location = self._url(f"{self._config.simulations_path}/{simulation_id}")

        return SimulationHandle(
            id=simulation_id or location.rstrip("/").split("/")[-1],
            status=status,
            location=location,
        )

    def get_simulation(self, handle: SimulationHandle) -> JsonObject:
        """Fetch the current state of a previously submitted simulation."""
        if not self._session_headers:
            self.authenticate()

        response = self._request_with_retries(
            "GET",
            handle.location,
            self._json_headers(),
            None,
        )

        # Automatic session refresh on 401/403
        if response.status_code in {401, 403}:
            logger.info("Session expired/unauthorized. Re-authenticating...")
            self.authenticate()
            response = self._request_with_retries(
                "GET",
                handle.location,
                self._json_headers(),
                None,
            )

        if response.status_code != 200:
            self._raise_for_status(response)
        return response.json_object()

    def _request_with_retries(
        self,
        method: str,
        url: str,
        headers: Mapping[str, str],
        json_body: JsonObject | None,
    ) -> HttpResponse:
        """Execute a request with bounded retries and exponential backoff."""
        attempts = self._config.max_retries + 1
        for attempt in range(attempts):
            logger.info(
                f"API Request: {method} {url} (attempt {attempt + 1}/{attempts})"
            )

            try:
                response = self._transport.request(
                    method=method,
                    url=url,
                    headers=headers,
                    json_body=json_body,
                    timeout_seconds=self._config.timeout_seconds,
                )
            except Exception as e:
                logger.warning(f"Transport exception during API request: {str(e)}")
                if attempt == attempts - 1:
                    raise
                response = HttpResponse(
                    status_code=599, headers={}, body=str(e).encode()
                )

            logger.info(f"API Response: {response.status_code} from {method} {url}")

            if response.status_code not in {408, 429, 500, 502, 503, 504, 599}:
                return response
            if attempt == attempts - 1:
                return response

            # Exponential backoff: 0.5 * 2^attempt seconds
            backoff = 0.5 * (2**attempt)
            logger.info(
                f"Retrying transient status {response.status_code} after {backoff}s..."
            )
            time.sleep(backoff)

        return response

    def _json_headers(self) -> dict[str, str]:
        """Build standard JSON headers merged with session credentials."""
        return {
            **self._session_headers,
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

    def _url(self, path: str) -> str:
        """Join a configured API path to the base URL."""
        return urljoin(f"{self._config.api_base_url.rstrip('/')}/", path.lstrip("/"))

    @staticmethod
    def _header(headers: Mapping[str, str], name: str) -> str | None:
        """Read a case-insensitive HTTP header value."""
        for key, value in headers.items():
            if key.lower() == name.lower():
                return value
        return None

    @staticmethod
    def _extract_token(response: HttpResponse) -> str | None:
        """Extract bearer-token style values from common authentication payloads."""
        if not response.body:
            return None
        payload = response.json_object()
        for key in ("token", "access_token"):
            value = payload.get(key)
            if isinstance(value, str) and value:
                return value
        return None

    @staticmethod
    def _string_field(payload: Mapping[str, JsonValue], field: str) -> str | None:
        """Return a non-empty string field from a JSON object."""
        value = payload.get(field)
        if isinstance(value, str) and value:
            return value
        return None

    @staticmethod
    def _raise_for_status(response: HttpResponse) -> None:
        """Raise a narrow execution error for a failed platform response."""
        if response.status_code == 429:
            raise ExecutionRateLimitError("WorldQuant API rate limit exceeded.")
        if 500 <= response.status_code <= 599:
            raise ExecutionServerError(
                f"WorldQuant API server error: {response.status_code}."
            )
        if 400 <= response.status_code <= 499:
            raise ExecutionClientError(
                f"WorldQuant API client error: {response.status_code}."
            )
        raise ExecutionClientError(
            f"Unexpected WorldQuant API response: {response.status_code}."
        )
