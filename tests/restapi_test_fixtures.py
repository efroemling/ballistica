# Released under the MIT License. See LICENSE for details.
#
"""Shared pytest fixtures for REST live-server tests."""

import os
from pathlib import Path
from typing import TYPE_CHECKING

import pytest
import urllib3
from efrotools.project import getlocalconfig

from efro.error import CleanError

if TYPE_CHECKING:
    from typing import Any


# Fleet selection precedence:
#   1. ``BALLISTICA_URL`` — explicit URL override (e.g. a custom
#      test server). Wins if set; otherwise we derive the URL from
#      ``BA_FLEET``.
#   2. ``BA_FLEET`` — ``'prod'`` (default), ``'test'``, or ``'dev'``.
# Default is intentionally ``prod``: this file lands in the public
# repo via spinoff, and a random clone running these tests should
# never accidentally talk to the dev server. Dev/test runs override
# explicitly.
_FLEET_URLS = {
    'prod': 'https://ballistica.net',
    'test': 'https://test.ballistica.net',
    'dev': 'https://dev.ballistica.net',
}


def _resolve_fleet() -> str:
    """Return the selected fleet name; raise on invalid values."""
    fleet = os.environ.get('BA_FLEET', 'prod').lower()
    if fleet not in _FLEET_URLS:
        raise CleanError(
            f'Invalid BA_FLEET value {fleet!r};'
            f' expected one of {sorted(_FLEET_URLS)}.'
        )
    return fleet


def _resolve_server_url() -> str:
    """Return the resolved base URL of the server under test."""
    override = os.environ.get('BALLISTICA_URL')
    if override:
        return override
    return _FLEET_URLS[_resolve_fleet()]


#: The resolved fleet for the current test run. Test modules import
#: this for prod-vs-non-prod branching at module scope (replacing
#: the older ad-hoc URL-string parsing).
BALLISTICA_FLEET: str = _resolve_fleet()


def _read_ballistica_api_key() -> str | None:
    """Return ballistica_api_key from localconfig.json, or None if absent."""
    val = getlocalconfig(Path('.')).get('ballistica_api_key')
    return str(val) if val is not None else None


def make_pool() -> urllib3.PoolManager:
    """PoolManager that honors HTTPS_PROXY (urllib3 doesn't by default)."""
    proxy = os.environ.get('HTTPS_PROXY') or os.environ.get('https_proxy')
    if proxy:
        # urllib3 does not pull credentials out of a proxy URL's
        # userinfo, so an authenticating proxy (CI runners, the Claude
        # Code sandbox, etc.) needs them passed explicitly as a
        # Proxy-Authorization header; otherwise the CONNECT tunnel for
        # an https target comes back '407 Proxy Authentication Required'.
        parsed = urllib3.util.parse_url(proxy)
        proxy_headers = (
            urllib3.make_headers(proxy_basic_auth=parsed.auth)
            if parsed.auth
            else None
        )
        return urllib3.ProxyManager(proxy, proxy_headers=proxy_headers)
    return urllib3.PoolManager()


class AuthedClient:
    """urllib3 PoolManager wrapper with a pre-set Authorization header."""

    def __init__(self, pool: urllib3.PoolManager, token: str) -> None:
        self._http = pool
        self._hdrs: dict[str, str] = {'Authorization': f'Bearer {token}'}

    def _h(self, extra: dict[str, str] | None = None) -> dict[str, str]:
        return self._hdrs if extra is None else {**self._hdrs, **extra}

    def get(self, url: str, **kw: Any) -> urllib3.BaseHTTPResponse:
        """GET request with auth header."""
        return self._http.request('GET', url, headers=self._h(), **kw)

    def post(
        self,
        url: str,
        *,
        json: Any = None,
        body: bytes | None = None,
        headers: dict[str, str] | None = None,
        **kw: Any,
    ) -> urllib3.BaseHTTPResponse:
        """POST request with auth header."""
        return self._http.request(
            'POST', url, json=json, body=body, headers=self._h(headers), **kw
        )

    def put(
        self, url: str, *, body: bytes | None = None, **kw: Any
    ) -> urllib3.BaseHTTPResponse:
        """PUT request with auth header."""
        return self._http.request(
            'PUT', url, body=body, headers=self._h(), **kw
        )

    def delete(self, url: str, **kw: Any) -> urllib3.BaseHTTPResponse:
        """DELETE request with auth header."""
        return self._http.request('DELETE', url, headers=self._h(), **kw)

    def patch(
        self, url: str, *, json: Any = None, **kw: Any
    ) -> urllib3.BaseHTTPResponse:
        """PATCH request with auth header."""
        return self._http.request(
            'PATCH', url, json=json, headers=self._h(), **kw
        )


@pytest.fixture(scope='session')
def http() -> urllib3.PoolManager:
    """Unauthenticated urllib3 connection pool."""
    return make_pool()


@pytest.fixture(scope='session')
def server_url() -> str:
    """Base URL of the server under test."""
    return _resolve_server_url()


@pytest.fixture(scope='session')
def api_key() -> str:
    """Bearer token for authenticated requests; skips if unavailable."""
    key = os.environ.get('BALLISTICA_API_KEY') or _read_ballistica_api_key()
    if not key:
        pytest.skip(
            'No API key available (set BALLISTICA_API_KEY or'
            ' ballistica_api_key in localconfig.json)'
        )
    return key


@pytest.fixture(scope='session')
def authed(
    api_key: str,
) -> AuthedClient:  # pylint: disable=redefined-outer-name
    """AuthedClient with the Bearer token pre-set."""
    return AuthedClient(make_pool(), api_key)
