# Released under the MIT License. See LICENSE for details.
#
"""Shared pytest fixtures for REST live-server tests."""

from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING

import pytest
import urllib3
from efrotools.project import getlocalconfig

if TYPE_CHECKING:
    from typing import Any


def _read_ballistica_api_key() -> str | None:
    """Return ballistica_api_key from localconfig.json, or None if absent."""
    val = getlocalconfig(Path('.')).get('ballistica_api_key')
    return str(val) if val is not None else None


def make_pool() -> urllib3.PoolManager:
    """PoolManager that honors HTTPS_PROXY (urllib3 doesn't by default)."""
    proxy = os.environ.get('HTTPS_PROXY') or os.environ.get('https_proxy')
    if proxy:
        return urllib3.ProxyManager(proxy)
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
    return os.environ.get('BALLISTICA_URL', 'https://dev.ballistica.net')


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
