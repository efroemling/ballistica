# Released under the MIT License. See LICENSE for details.
#
"""Fixtures for public REST API live-server tests."""

import json
from typing import TYPE_CHECKING

import pytest

from bacommon.restapi.v1 import Endpoint

if TYPE_CHECKING:
    import urllib3

    from restapi_test_fixtures import AuthedClient


@pytest.fixture(scope='session', autouse=True)
def _require_api_key(api_key: str) -> None:  # pylint: disable=unused-argument
    """Skip all tests in this package when no API key is available."""


# Must start with the workspace test prefix (Workspace.TEST_NAME_PREFIX)
# so the server skips backup creation on snapshot updates and on
# teardown — otherwise every test session would leave a 30-day backup
# behind on the workspaces backups page.
_TEST_WS_NAME = '_test_restapi'


def _delete_workspaces_named(
    authed: AuthedClient, server_url: str, name: str
) -> None:
    """Delete all workspaces with the given name (idempotent cleanup).

    Accepts 404 on the DELETE in addition to 204 — a parallel session
    or manual cleanup may have removed the workspace between our LIST
    and DELETE. Any other status surfaces as a test error so real
    server/auth regressions don't silently leak storage.
    """
    r = authed.get(f'{server_url}{Endpoint.WORKSPACES}', timeout=10)
    assert r.status == 200
    for ws in json.loads(r.data).get('workspaces', []):
        if ws['name'] == name:
            path = Endpoint.WORKSPACE.format(workspace_id=ws['id'])
            dr = authed.delete(f'{server_url}{path}', timeout=10)
            assert dr.status in (
                204,
                404,
            ), f'cleanup DELETE {path} returned {dr.status}: {dr.data!r}'


@pytest.fixture(scope='session')
def ws_id(server_url: str, authed: AuthedClient) -> str:  # type: ignore[misc]
    """Session-scoped: creates _test_restapi workspace and tears it down."""
    _delete_workspaces_named(authed, server_url, _TEST_WS_NAME)
    r = authed.post(
        f'{server_url}{Endpoint.WORKSPACES}',
        json={'name': _TEST_WS_NAME},
        timeout=10,
    )
    assert r.status == 201, r.data.decode()
    workspace_id: str = json.loads(r.data)['id']
    yield workspace_id
    path = Endpoint.WORKSPACE.format(workspace_id=workspace_id)
    dr = authed.delete(f'{server_url}{path}', timeout=10)
    assert (
        dr.status == 204
    ), f'teardown DELETE {path} returned {dr.status}: {dr.data!r}'
