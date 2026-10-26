"""The RestAPI client: one call per endpoint the MCP server uses, errors turned into plain sentences."""
from __future__ import annotations

from typing import Any

import httpx

from .config import Config

__all__ = ["ApiError", "RestApi"]


class ApiError(Exception):
    """A failed call, as a sentence the assistant can act on. It never contains the API key."""


_HINTS = {
    401: "the bot refused the authentication: check the API key",
    403: "the bot refused the authentication: check the API key, and that the endpoint's security rule accepts "
         "an API key from where this tool connects (see the README)",
    404: "not found",
    409: "the bot refused the action in the server's current state",
    422: "a parameter was refused",
    503: "the node is not active",
    504: "the bot timed out",
}


class RestApi:
    def __init__(self, config: Config, transport: httpx.AsyncBaseTransport | None = None):
        self.config = config
        self._client = httpx.AsyncClient(base_url=config.base_url, timeout=config.timeout,
                                         verify=config.verify_tls, transport=transport,
                                         headers={"X-API-Key": config.api_key.reveal()})

    async def aclose(self) -> None:
        await self._client.aclose()

    async def _call(self, method: str, path: str, params: dict[str, Any] | None = None) -> Any:
        params = {k: (str(v).lower() if isinstance(v, bool) else v)
                  for k, v in (params or {}).items() if v is not None}
        try:
            response = await self._client.request(method, path, params=params)
        except httpx.TimeoutException:
            raise ApiError(f"{method} {path}: no answer from the bot within {self.config.timeout:g} s.") from None
        except httpx.HTTPError as ex:
            # the exception text names the URL, never the headers
            raise ApiError(f"{method} {path}: cannot reach the bot ({type(ex).__name__}: {ex}).") from None
        if response.is_success:
            try:
                return response.json()
            except ValueError:
                raise ApiError(f"{method} {path}: the bot answered something that is not JSON.") from None
        try:
            detail = response.json().get("detail")
        except (ValueError, AttributeError):
            detail = None
        if not isinstance(detail, str):
            detail = response.text[:300] if not detail else str(detail)[:300]
        hint = _HINTS.get(response.status_code, "")
        if response.status_code == 404 and detail in ("Not Found", "Not found."):
            hint = ("this endpoint does not exist or is disabled on the bot (log endpoints need a RestAPI with "
                    "/node/log and /instance/log)")
        raise ApiError(f"{method} {path}: HTTP {response.status_code}{' - ' + hint if hint else ''}: {detail}")

    async def get(self, path: str, **params) -> Any:
        return await self._call("GET", path, params)

    async def post(self, path: str, **params) -> Any:
        return await self._call("POST", path, params)
