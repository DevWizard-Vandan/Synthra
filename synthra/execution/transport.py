"""HTTP transport primitives for execution clients."""

import json
import logging
from dataclasses import dataclass
from typing import Mapping, Protocol, TypeAlias, cast
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from synthra.execution.exceptions import ExecutionTransportError

logger = logging.getLogger(__name__)

JsonValue: TypeAlias = (
    None | bool | int | float | str | list["JsonValue"] | dict[str, "JsonValue"]
)
JsonObject: TypeAlias = dict[str, JsonValue]


@dataclass(frozen=True)
class HttpResponse:
    """Structured HTTP response returned by an injected transport."""

    status_code: int
    headers: Mapping[str, str]
    body: bytes

    def json_object(self) -> JsonObject:
        """Decode the response body as a JSON object.

        Returns:
            Parsed JSON object. Empty bodies are returned as an empty dictionary.

        Raises:
            ExecutionTransportError: If the response body is not a JSON object.
        """
        if not self.body:
            return {}
        try:
            parsed = json.loads(self.body.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as err:
            logger.error("Execution response JSON decoding failed.", exc_info=True)
            raise ExecutionTransportError("Response body is not valid JSON.") from err
        if not isinstance(parsed, dict):
            raise ExecutionTransportError("Response JSON payload must be an object.")
        return cast(JsonObject, parsed)


class HttpTransport(Protocol):
    """Protocol implemented by real and test HTTP transports."""

    def request(
        self,
        method: str,
        url: str,
        headers: Mapping[str, str],
        json_body: JsonObject | None,
        timeout_seconds: float,
    ) -> HttpResponse:
        """Send an HTTP request and return a structured response."""


class UrllibHttpTransport:
    """Minimal stdlib HTTP transport for production execution requests."""

    def request(
        self,
        method: str,
        url: str,
        headers: Mapping[str, str],
        json_body: JsonObject | None,
        timeout_seconds: float,
    ) -> HttpResponse:
        """Send an HTTP request using urllib.

        Args:
            method: HTTP method.
            url: Absolute URL.
            headers: Request headers.
            json_body: Optional JSON object body.
            timeout_seconds: Socket timeout.

        Returns:
            Structured response object.

        Raises:
            ExecutionTransportError: If the request cannot reach the server.
        """
        body: bytes | None = None
        request_headers: dict[str, str] = dict(headers)
        if json_body is not None:
            body = json.dumps(json_body, separators=(",", ":")).encode("utf-8")
            request_headers.setdefault("Content-Type", "application/json")

        request = Request(url, data=body, headers=request_headers, method=method)
        try:
            with urlopen(request, timeout=timeout_seconds) as response:
                response_headers = dict(response.headers.items())
                return HttpResponse(
                    status_code=response.status,
                    headers=response_headers,
                    body=response.read(),
                )
        except HTTPError as err:
            return HttpResponse(
                status_code=err.code,
                headers=dict(err.headers.items()),
                body=err.read(),
            )
        except (URLError, TimeoutError, OSError) as err:
            logger.error("Execution HTTP transport failed for %s %s.", method, url)
            raise ExecutionTransportError("Execution HTTP request failed.") from err
