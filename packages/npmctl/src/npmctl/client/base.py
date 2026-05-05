"""HTTP client for the Nginx Proxy Manager API."""

from __future__ import annotations

import time
from collections.abc import Mapping
from typing import Any

import requests

from npmctl.client.contracts import CONTRACTS
from npmctl.errors import ApiError, CapabilityError
from npmctl.models import ExistingResource, ExistingState, ResourceKind
from npmctl.schema import Capabilities


class NpmClient:
    """Small typed client for the NPM OpenAPI surface."""

    def __init__(self, *, base_url: str, identity: str, secret: str, timeout_s: float = 15.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.identity = identity
        self.secret = secret
        self.timeout_s = timeout_s
        self.session = requests.Session()
        self._token: str | None = None
        self._expires: int | None = None

    def health(self) -> dict[str, Any]:
        return self._request("get", "/", authenticated=False)

    def login(self) -> None:
        payload = {"identity": self.identity, "secret": self.secret, "scope": "user"}
        data = self._request("post", "/tokens", authenticated=False, json=payload)
        token, expires = _extract_token(data)
        self._token = token
        self._expires = expires

    def refresh(self) -> None:
        try:
            data = self._request("get", "/tokens", authenticated=True)
        except ApiError:
            self.login()
            return
        token, expires = _extract_token(data)
        self._token = token
        self._expires = expires

    def openapi_schema(self) -> dict[str, Any]:
        return self._request("get", "/schema", authenticated=False)

    def capabilities(self) -> Capabilities:
        return Capabilities.from_openapi(self.openapi_schema())

    def list_resource(self, kind: ResourceKind) -> tuple[ExistingResource, ...]:
        contract = CONTRACTS[kind]
        data = self._request("get", contract.collection_path, authenticated=True)
        if not isinstance(data, list):
            raise ApiError(f"expected list response for {kind.value}, got {type(data).__name__}")
        if kind == ResourceKind.PROXY_HOST:
            return tuple(ExistingResource.from_proxy_host(item) for item in data)
        if kind == ResourceKind.CERTIFICATE:
            return tuple(ExistingResource.from_certificate(item) for item in data)
        if kind == ResourceKind.ACCESS_LIST:
            return tuple(ExistingResource.from_access_list(item) for item in data)
        raise CapabilityError(f"unsupported resource kind: {kind}")

    def existing_state(self, *, include_certificates: bool = True, include_access_lists: bool = True) -> ExistingState:
        proxy_hosts = self.list_resource(ResourceKind.PROXY_HOST)
        certificates = self.list_resource(ResourceKind.CERTIFICATE) if include_certificates else ()
        access_lists = self.list_resource(ResourceKind.ACCESS_LIST) if include_access_lists else ()
        return ExistingState(proxy_hosts=proxy_hosts, certificates=certificates, access_lists=access_lists)

    def create_resource(self, kind: ResourceKind, payload: Mapping[str, Any]) -> ExistingResource:
        contract = CONTRACTS[kind]
        data = self._request("post", contract.collection_path, authenticated=True, json=dict(payload))
        return _parse_created(kind, data)

    def update_resource(
        self, kind: ResourceKind, resource_id: int, payload: Mapping[str, Any], *, method: str = "put"
    ) -> ExistingResource:
        contract = CONTRACTS[kind]
        data = self._request(method, contract.item_path(resource_id), authenticated=True, json=dict(payload))
        return _parse_created(kind, data)

    def delete_resource(self, kind: ResourceKind, resource_id: int) -> bool:
        contract = CONTRACTS[kind]
        data = self._request("delete", contract.item_path(resource_id), authenticated=True, allow_empty=True)
        return data is True or data == {} or data is None

    def _ensure_token(self) -> None:
        if self._token is None or self._expires is None:
            self.login()
            return
        if int(time.time()) >= self._expires - 30:
            self.refresh()

    def _request(
        self,
        method: str,
        path: str,
        *,
        authenticated: bool,
        json: Mapping[str, Any] | None = None,
        allow_empty: bool = False,
    ) -> Any:
        if authenticated:
            self._ensure_token()
        headers = {"Content-Type": "application/json"}
        if authenticated and self._token:
            headers["Authorization"] = f"Bearer {self._token}"
        url = f"{self.base_url}{path}"
        try:
            response = self.session.request(method.upper(), url, headers=headers, json=json, timeout=self.timeout_s)
        except requests.RequestException as exc:
            raise ApiError(f"{method.upper()} {path} transport error: {exc}") from exc
        if response.status_code < 200 or response.status_code >= 300:
            raise ApiError(f"{method.upper()} {path} failed: HTTP {response.status_code}: {_redact(response.text)}")
        if allow_empty and not response.content:
            return None
        try:
            return response.json()
        except ValueError as exc:
            if allow_empty:
                return {}
            raise ApiError(f"{method.upper()} {path} returned invalid JSON") from exc


def _extract_token(data: Any) -> tuple[str, int]:
    if isinstance(data, dict) and isinstance(data.get("result"), dict):
        data = data["result"]
    if not isinstance(data, dict):
        raise ApiError("token response must be an object")
    token = data.get("token")
    expires = data.get("expires")
    if not isinstance(token, str) or not token:
        raise ApiError("token response missing token")
    if isinstance(expires, str):
        # NPM sometimes returns ISO strings from login-as-user endpoints; tokens are normally unix seconds.
        raise ApiError("token response expires must be a unix timestamp")
    if isinstance(expires, bool) or not isinstance(expires, int | float):
        raise ApiError("token response missing numeric expires")
    return token, int(expires)


def _parse_created(kind: ResourceKind, data: Any) -> ExistingResource:
    if not isinstance(data, dict):
        raise ApiError(f"{kind.value} mutation response must be an object")
    if kind == ResourceKind.PROXY_HOST:
        return ExistingResource.from_proxy_host(data)
    if kind == ResourceKind.CERTIFICATE:
        return ExistingResource.from_certificate(data)
    if kind == ResourceKind.ACCESS_LIST:
        return ExistingResource.from_access_list(data)
    raise CapabilityError(f"unsupported resource kind: {kind}")


def _redact(text: str) -> str:
    redacted = text
    for marker in ("token", "secret", "password"):
        redacted = redacted.replace(marker, f"{marker[0]}***")
    return redacted[:1000]
