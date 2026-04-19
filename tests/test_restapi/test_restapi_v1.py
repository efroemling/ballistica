# Released under the MIT License. See LICENSE for details.
#
"""Live-server tests for public REST API v1 endpoints."""

from __future__ import annotations

import hashlib
import json
import os
from typing import TYPE_CHECKING

import pytest

from bacommon.restapi.v1 import Endpoint
from restapi_test_fixtures import make_pool

if TYPE_CHECKING:
    import urllib3

    from restapi_test_fixtures import AuthedClient

FAST_MODE = os.environ.get('BA_TEST_FAST_MODE') == '1'


def _delete_workspaces_named(
    authed: AuthedClient, server_url: str, name: str
) -> None:
    """Delete all workspaces with the given name (idempotent cleanup)."""
    r = authed.get(f'{server_url}{Endpoint.WORKSPACES}', timeout=10)
    assert r.status == 200
    for ws in json.loads(r.data).get('workspaces', []):
        if ws['name'] == name:
            path = Endpoint.WORKSPACE.format(workspace_id=ws['id'])
            authed.delete(f'{server_url}{path}', timeout=10)


def _upload_workspace_file(
    server_url: str,
    authed: AuthedClient,
    file_url: str,
    content: bytes,
) -> None:
    """Upload ``content`` to ``file_url`` via the init/finalize ops.

    Replaces the legacy single-call PUT used by older tests; with the
    buffered PUT path removed, all uploads now go through the
    streaming pipeline. The dedup short-circuit collapses repeated
    identical content to a single round-trip.
    """
    sha256_hex = hashlib.sha256(content).hexdigest()

    init_r = authed.post(
        f'{server_url}{file_url}',
        json={
            'op': 'upload-init',
            'size': len(content),
            'sha256': sha256_hex,
        },
        timeout=30,
    )
    assert init_r.status == 200, f'init failed: {init_r.data!r}'
    init = json.loads(init_r.data)

    if init['status'] == 'exists':
        return  # Dedup hit — server already wired the file in.

    assert init['status'] == 'upload_required'
    put_pool = make_pool()
    gcs_r = put_pool.request(
        'PUT',
        init['upload_url'],
        body=content,
        headers=init['upload_headers'],
        timeout=180,
    )
    assert gcs_r.status == 200, f'GCS PUT failed: {gcs_r.status}'
    fin_r = authed.post(
        f'{server_url}{file_url}',
        json={'op': 'upload-finalize', 'session_id': init['session_id']},
        timeout=60,
    )
    assert fin_r.status == 204, f'finalize failed: {fin_r.data!r}'


# --- Account endpoint ---


def test_account_no_auth(server_url: str, http: urllib3.PoolManager) -> None:
    """No auth header should return 401."""
    path = Endpoint.ACCOUNT.format(account_id='me')
    r = http.request('GET', f'{server_url}{path}', timeout=10)
    assert r.status == 401
    assert r.headers['Content-Type'].startswith('application/json')
    body = json.loads(r.data)
    assert body['error'] == 'unauthorized'


@pytest.mark.skipif(FAST_MODE, reason='fast mode')
def test_account_notfound(server_url: str, authed: AuthedClient) -> None:
    """Nonexistent account ID should return 404."""
    path = Endpoint.ACCOUNT.format(account_id='a-00000000')
    r = authed.get(f'{server_url}{path}', timeout=10)
    assert r.status == 404
    body = json.loads(r.data)
    assert body['error'] == 'not_found'


def test_account_me(server_url: str, authed: AuthedClient) -> None:
    """GET /api/v1/accounts/me returns the authenticated account's info."""
    path = Endpoint.ACCOUNT.format(account_id='me')
    r = authed.get(f'{server_url}{path}', timeout=10)
    assert r.status == 200
    body = json.loads(r.data)
    assert isinstance(body['id'], str)
    assert body['id'].startswith('a-')
    assert isinstance(body['tag'], str)
    assert isinstance(body['create_time'], str)
    assert isinstance(body['total_active_days'], int)
    # last_active_day is either None or a YYYY-MM-DD string
    lad = body['last_active_day']
    assert lad is None or (isinstance(lad, str) and len(lad) == 10)


# --- Account-by-tag endpoint ---


def test_account_by_tag_no_auth(
    server_url: str, http: urllib3.PoolManager
) -> None:
    """No auth header should return 401."""
    path = Endpoint.ACCOUNT_BY_TAG.format(tag='SomeTag')
    r = http.request('GET', f'{server_url}{path}', timeout=10)
    assert r.status == 401
    body = json.loads(r.data)
    assert body['error'] == 'unauthorized'


@pytest.mark.skipif(FAST_MODE, reason='fast mode')
def test_account_by_tag_notfound(server_url: str, authed: AuthedClient) -> None:
    """Nonexistent tag should return 404."""
    path = Endpoint.ACCOUNT_BY_TAG.format(tag='zzzznosuchtagzzz')
    r = authed.get(f'{server_url}{path}', timeout=10)
    assert r.status == 404
    body = json.loads(r.data)
    assert body['error'] == 'not_found'


@pytest.mark.skipif(FAST_MODE, reason='fast mode')
def test_account_by_tag(server_url: str, authed: AuthedClient) -> None:
    """Look up our own account by tag and verify the response matches."""
    # First, fetch our account info to get our tag.
    me_path = Endpoint.ACCOUNT.format(account_id='me')
    me_r = authed.get(f'{server_url}{me_path}', timeout=10)
    assert me_r.status == 200
    me_body = json.loads(me_r.data)

    # Now look up by that tag.
    tag_path = Endpoint.ACCOUNT_BY_TAG.format(tag=me_body['tag'])
    tag_r = authed.get(f'{server_url}{tag_path}', timeout=10)
    assert tag_r.status == 200
    tag_body = json.loads(tag_r.data)

    assert tag_body['id'] == me_body['id']
    assert tag_body['tag'] == me_body['tag']
    assert tag_body['create_time'] == me_body['create_time']
    assert tag_body['total_active_days'] == me_body['total_active_days']


# --- Workspace endpoints ---


# --- Auth tests (no session needed) ---


def test_workspaces_no_auth(server_url: str, http: urllib3.PoolManager) -> None:
    """GET /workspaces without auth should return 401."""
    r = http.request('GET', f'{server_url}{Endpoint.WORKSPACES}', timeout=10)
    assert r.status == 401
    body = json.loads(r.data)
    assert body['error'] == 'unauthorized'
    assert 'message' in body


@pytest.mark.skipif(FAST_MODE, reason='fast mode')
def test_workspace_create_no_auth(
    server_url: str, http: urllib3.PoolManager
) -> None:
    """POST /workspaces without auth should return 401."""
    r = http.request(
        'POST',
        f'{server_url}{Endpoint.WORKSPACES}',
        json={'name': 'Whatever'},
        timeout=10,
    )
    assert r.status == 401
    assert json.loads(r.data)['error'] == 'unauthorized'


# --- Active workspace ---


def test_active_workspace_no_auth(
    server_url: str, http: urllib3.PoolManager
) -> None:
    """GET /workspaces/active without auth should return 401."""
    r = http.request(
        'GET', f'{server_url}{Endpoint.WORKSPACES_ACTIVE}', timeout=10
    )
    assert r.status == 401
    body = json.loads(r.data)
    assert body['error'] == 'unauthorized'


@pytest.mark.skipif(FAST_MODE, reason='fast mode')
def test_active_workspace_none(server_url: str, authed: AuthedClient) -> None:
    """Clear active workspace; GET should return null."""
    # Ensure no workspace is active.
    authed.post(
        f'{server_url}{Endpoint.WORKSPACES_ACTIVE}',
        json={'workspace_id': None},
        timeout=10,
    )

    r = authed.get(f'{server_url}{Endpoint.WORKSPACES_ACTIVE}', timeout=10)
    assert r.status == 200
    body = json.loads(r.data)
    assert body is None


@pytest.mark.skipif(FAST_MODE, reason='fast mode')
def test_active_workspace_set_and_get(
    server_url: str, authed: AuthedClient
) -> None:
    """Set active workspace; GET should return full WorkspaceResponse."""
    name = '_test_restapi_active_ws'
    _delete_workspaces_named(authed, server_url, name)

    # Create a workspace to activate.
    cr = authed.post(
        f'{server_url}{Endpoint.WORKSPACES}',
        json={'name': name},
        timeout=10,
    )
    assert cr.status == 201
    ws = json.loads(cr.data)
    wid = ws['id']

    try:
        # Set it active.
        sr = authed.post(
            f'{server_url}{Endpoint.WORKSPACES_ACTIVE}',
            json={'workspace_id': wid},
            timeout=10,
        )
        assert sr.status == 200
        set_body = json.loads(sr.data)
        assert set_body['id'] == wid
        assert set_body['name'] == name

        # GET should return the same workspace.
        gr = authed.get(f'{server_url}{Endpoint.WORKSPACES_ACTIVE}', timeout=10)
        assert gr.status == 200
        get_body = json.loads(gr.data)
        assert get_body['id'] == wid
        assert get_body['name'] == name
        assert isinstance(get_body['size'], int)
        assert isinstance(get_body['create_time'], str)
        assert isinstance(get_body['modified_time'], str)
    finally:
        # Clean up: deactivate and delete.
        authed.post(
            f'{server_url}{Endpoint.WORKSPACES_ACTIVE}',
            json={'workspace_id': None},
            timeout=10,
        )
        path = Endpoint.WORKSPACE.format(workspace_id=wid)
        authed.delete(f'{server_url}{path}', timeout=10)


# --- Workspace lifecycle ---


def test_workspace_list(server_url: str, authed: AuthedClient) -> None:
    """GET /workspaces returns a list; each entry has expected fields."""
    r = authed.get(f'{server_url}{Endpoint.WORKSPACES}', timeout=10)
    assert r.status == 200
    body = json.loads(r.data)
    assert 'workspaces' in body
    assert isinstance(body['workspaces'], list)
    for ws in body['workspaces']:
        assert isinstance(ws['id'], str)
        assert isinstance(ws['name'], str)
        assert isinstance(ws['size'], int)
        assert isinstance(ws['create_time'], str)
        assert isinstance(ws['modified_time'], str)


@pytest.mark.skipif(FAST_MODE, reason='fast mode')
def test_workspace_create_and_delete(
    server_url: str, authed: AuthedClient
) -> None:
    """POST creates a workspace; GET returns it; DELETE removes it."""
    name = '_test_restapi_lifecycle'
    _delete_workspaces_named(authed, server_url, name)

    # Create
    r = authed.post(
        f'{server_url}{Endpoint.WORKSPACES}',
        json={'name': name},
        timeout=10,
    )
    assert r.status == 201
    ws = json.loads(r.data)
    assert ws['name'] == name
    wid = ws['id']

    # Appears in list
    list_r = authed.get(f'{server_url}{Endpoint.WORKSPACES}', timeout=10)
    ids = [w['id'] for w in json.loads(list_r.data)['workspaces']]
    assert wid in ids

    # GET single
    get_r = authed.get(
        f'{server_url}{Endpoint.WORKSPACE.format(workspace_id=wid)}',
        timeout=10,
    )
    assert get_r.status == 200
    assert json.loads(get_r.data)['id'] == wid

    # DELETE
    del_r = authed.delete(
        f'{server_url}{Endpoint.WORKSPACE.format(workspace_id=wid)}',
        timeout=10,
    )
    assert del_r.status == 204

    # No longer in list
    list2_r = authed.get(f'{server_url}{Endpoint.WORKSPACES}', timeout=10)
    ids2 = [w['id'] for w in json.loads(list2_r.data)['workspaces']]
    assert wid not in ids2


# --- Workspace name validation ---


@pytest.mark.parametrize(
    'bad_name',
    [
        '',
        ' Leading space',
        'Trailing space ',
        'bad/char',
        'x' * 129,
    ],
)
@pytest.mark.skipif(FAST_MODE, reason='fast mode')
def test_workspace_create_invalid_names(
    server_url: str, authed: AuthedClient, bad_name: str
) -> None:
    """Invalid workspace names should return 400 (invalid_parameter)."""
    r = authed.post(
        f'{server_url}{Endpoint.WORKSPACES}',
        json={'name': bad_name},
        timeout=10,
    )
    assert r.status == 400
    assert json.loads(r.data)['error'] == 'invalid_parameter'


# --- Rename (PATCH) ---


@pytest.mark.skipif(FAST_MODE, reason='fast mode')
def test_workspace_rename(server_url: str, authed: AuthedClient) -> None:
    """PATCH with a valid name renames the workspace."""
    name_orig = '_test_restapi_rename_orig'
    name_new = '_test_restapi_rename_new'
    _delete_workspaces_named(authed, server_url, name_orig)
    _delete_workspaces_named(authed, server_url, name_new)

    # Create
    r = authed.post(
        f'{server_url}{Endpoint.WORKSPACES}',
        json={'name': name_orig},
        timeout=10,
    )
    assert r.status == 201
    wid = json.loads(r.data)['id']
    path = Endpoint.WORKSPACE.format(workspace_id=wid)

    try:
        # Rename
        patch_r = authed.patch(
            f'{server_url}{path}',
            json={'name': name_new},
            timeout=10,
        )
        assert patch_r.status == 200
        assert json.loads(patch_r.data)['name'] == name_new

        # Verify via GET
        get_r = authed.get(f'{server_url}{path}', timeout=10)
        assert json.loads(get_r.data)['name'] == name_new
    finally:
        authed.delete(f'{server_url}{path}', timeout=10)


@pytest.mark.skipif(FAST_MODE, reason='fast mode')
def test_workspace_rename_invalid(
    server_url: str, authed: AuthedClient
) -> None:
    """PATCH with an empty name should return 400."""
    name = '_test_restapi_rename_invalid'
    _delete_workspaces_named(authed, server_url, name)

    r = authed.post(
        f'{server_url}{Endpoint.WORKSPACES}',
        json={'name': name},
        timeout=10,
    )
    assert r.status == 201
    wid = json.loads(r.data)['id']
    path = Endpoint.WORKSPACE.format(workspace_id=wid)

    try:
        patch_r = authed.patch(
            f'{server_url}{path}',
            json={'name': ''},
            timeout=10,
        )
        assert patch_r.status == 400
        assert json.loads(patch_r.data)['error'] == 'invalid_parameter'
    finally:
        authed.delete(f'{server_url}{path}', timeout=10)


# --- File operations ---


@pytest.mark.skipif(FAST_MODE, reason='fast mode')
def test_file_upload_and_download(
    server_url: str, authed: AuthedClient, ws_id: str
) -> None:
    """Upload a >16 MB file via init/finalize, GET returns the same bytes.

    Sized to clearly exceed Flask's ``MAX_CONTENT_LENGTH`` (16 MB,
    set in ``src/main.py``) — the legacy buffered PUT path would
    reject this. The init/finalize pipeline ships the bytes from
    the client straight to GCS via a signed URL, so the master
    server never sees the body. A successful end-to-end round-trip
    is the load-bearing assertion.
    """
    # Workspace filenames are restricted to a specific allowlist of
    # extensions; ``.bstr`` is the binary-blob option whose contents
    # are not content-validated.
    file_path = Endpoint.WORKSPACE_FILE.format(
        workspace_id=ws_id, file_path='large.bstr'
    )
    # 24 MB random bytes: above Flask's 16 MB cap, below the test
    # account's 32 MB STORAGE_BASE.
    content = os.urandom(24 * 1024 * 1024)
    _upload_workspace_file(server_url, authed, file_path, content)

    get_r = authed.get(f'{server_url}{file_path}', timeout=180)
    assert get_r.status == 200
    assert get_r.data == content


@pytest.mark.skipif(FAST_MODE, reason='fast mode')
def test_file_listing(
    server_url: str, authed: AuthedClient, ws_id: str
) -> None:
    """After upload, GET /files returns an entry with expected fields."""
    # Ensure at least one file exists
    file_path = Endpoint.WORKSPACE_FILE.format(
        workspace_id=ws_id, file_path='listing.txt'
    )
    _upload_workspace_file(server_url, authed, file_path, b'listing test')

    files_url = Endpoint.WORKSPACE_FILES.format(workspace_id=ws_id)
    r = authed.get(f'{server_url}{files_url}', timeout=10)
    assert r.status == 200
    entries = json.loads(r.data)['entries']
    assert isinstance(entries, list)
    paths = [e['path'] for e in entries]
    assert 'listing.txt' in paths
    for entry in entries:
        assert 'path' in entry
        assert entry['type'] in ('file', 'directory')
        if entry['type'] == 'file':
            assert isinstance(entry['size'], int)
            assert isinstance(entry['modified_time'], str)


@pytest.mark.skipif(FAST_MODE, reason='fast mode')
def test_mkdir(server_url: str, authed: AuthedClient, ws_id: str) -> None:
    """POST op=mkdir creates a directory that appears in the listing."""
    dir_path = Endpoint.WORKSPACE_FILE.format(
        workspace_id=ws_id, file_path='testdir'
    )
    r = authed.post(f'{server_url}{dir_path}', json={'op': 'mkdir'}, timeout=10)
    assert r.status == 204

    files_url = Endpoint.WORKSPACE_FILES.format(workspace_id=ws_id)
    listing = json.loads(
        authed.get(f'{server_url}{files_url}', timeout=10).data
    )
    dir_entries = [e for e in listing['entries'] if e['path'] == 'testdir']
    assert len(dir_entries) == 1
    assert dir_entries[0]['type'] == 'directory'


@pytest.mark.skipif(FAST_MODE, reason='fast mode')
def test_file_in_subdir(
    server_url: str, authed: AuthedClient, ws_id: str
) -> None:
    """Upload to a sub-path auto-creates the parent directory."""
    file_path = Endpoint.WORKSPACE_FILE.format(
        workspace_id=ws_id, file_path='subdir/notes.txt'
    )
    _upload_workspace_file(server_url, authed, file_path, b'notes')

    files_url = Endpoint.WORKSPACE_FILES.format(workspace_id=ws_id)
    listing = json.loads(
        authed.get(f'{server_url}{files_url}', timeout=10).data
    )
    paths = [e['path'] for e in listing['entries']]
    assert 'subdir/notes.txt' in paths


@pytest.mark.skipif(FAST_MODE, reason='fast mode')
def test_file_delete(server_url: str, authed: AuthedClient, ws_id: str) -> None:
    """DELETE a file; it should no longer appear in the listing."""
    file_path = Endpoint.WORKSPACE_FILE.format(
        workspace_id=ws_id, file_path='todelete.txt'
    )
    _upload_workspace_file(server_url, authed, file_path, b'bye')

    del_r = authed.delete(f'{server_url}{file_path}', timeout=10)
    assert del_r.status == 204

    files_url = Endpoint.WORKSPACE_FILES.format(workspace_id=ws_id)
    listing = json.loads(
        authed.get(f'{server_url}{files_url}', timeout=10).data
    )
    paths = [e['path'] for e in listing['entries']]
    assert 'todelete.txt' not in paths


@pytest.mark.skipif(FAST_MODE, reason='fast mode')
def test_file_move(server_url: str, authed: AuthedClient, ws_id: str) -> None:
    """POST op=move renames a file; src gone, dest present."""
    src = Endpoint.WORKSPACE_FILE.format(
        workspace_id=ws_id, file_path='src.txt'
    )
    _upload_workspace_file(server_url, authed, src, b'moving')

    move_r = authed.post(
        f'{server_url}{src}',
        json={'op': 'move', 'dest': 'dst.txt'},
        timeout=10,
    )
    assert move_r.status == 204

    files_url = Endpoint.WORKSPACE_FILES.format(workspace_id=ws_id)
    listing = json.loads(
        authed.get(f'{server_url}{files_url}', timeout=10).data
    )
    paths = [e['path'] for e in listing['entries']]
    assert 'dst.txt' in paths
    assert 'src.txt' not in paths


@pytest.mark.skipif(FAST_MODE, reason='fast mode')
def test_file_copy(server_url: str, authed: AuthedClient, ws_id: str) -> None:
    """POST op=copy duplicates a file; both orig and copy are present."""
    orig = Endpoint.WORKSPACE_FILE.format(
        workspace_id=ws_id, file_path='orig.txt'
    )
    _upload_workspace_file(server_url, authed, orig, b'original')

    copy_r = authed.post(
        f'{server_url}{orig}',
        json={'op': 'copy', 'dest': 'copy.txt'},
        timeout=10,
    )
    assert copy_r.status == 204

    files_url = Endpoint.WORKSPACE_FILES.format(workspace_id=ws_id)
    listing = json.loads(
        authed.get(f'{server_url}{files_url}', timeout=10).data
    )
    paths = [e['path'] for e in listing['entries']]
    assert 'orig.txt' in paths
    assert 'copy.txt' in paths


# --- File path validation ---


@pytest.mark.parametrize(
    'bad_path',
    [
        'UPPERCASE.txt',
        'has space.txt',
        'noextension',
        'bad.exe',
        'x' * 65 + '.txt',
    ],
)
@pytest.mark.skipif(FAST_MODE, reason='fast mode')
def test_file_upload_invalid_paths(
    server_url: str, authed: AuthedClient, ws_id: str, bad_path: str
) -> None:
    """upload-init for invalid file paths should return 400."""
    file_path = Endpoint.WORKSPACE_FILE.format(
        workspace_id=ws_id, file_path=bad_path
    )
    # Path is rejected by upload-init's validate_add_file_path() call
    # before any GCS upload session is allocated; the size/sha256
    # values below are well-formed but never used.
    r = authed.post(
        f'{server_url}{file_path}',
        json={
            'op': 'upload-init',
            'size': 1,
            'sha256': '0' * 64,
        },
        timeout=10,
    )
    assert r.status == 400


# --- POST op validation ---


@pytest.mark.skipif(FAST_MODE, reason='fast mode')
def test_post_op_invalid(
    server_url: str, authed: AuthedClient, ws_id: str
) -> None:
    """POST with unknown op should return 400 (invalid_parameter)."""
    file_path = Endpoint.WORKSPACE_FILE.format(
        workspace_id=ws_id, file_path='dummy.txt'
    )
    r = authed.post(
        f'{server_url}{file_path}', json={'op': 'frobnicate'}, timeout=10
    )
    assert r.status == 400
    assert json.loads(r.data)['error'] == 'invalid_parameter'


@pytest.mark.skipif(FAST_MODE, reason='fast mode')
def test_post_op_move_no_dest(
    server_url: str, authed: AuthedClient, ws_id: str
) -> None:
    """POST op=move without dest should return 400."""
    file_path = Endpoint.WORKSPACE_FILE.format(
        workspace_id=ws_id, file_path='dummy.txt'
    )
    r = authed.post(f'{server_url}{file_path}', json={'op': 'move'}, timeout=10)
    assert r.status == 400
    assert json.loads(r.data)['error'] == 'invalid_parameter'


@pytest.mark.skipif(FAST_MODE, reason='fast mode')
def test_post_op_not_json(
    server_url: str, authed: AuthedClient, ws_id: str
) -> None:
    """POST with non-JSON body should return 400."""
    file_path = Endpoint.WORKSPACE_FILE.format(
        workspace_id=ws_id, file_path='dummy.txt'
    )
    r = authed.post(
        f'{server_url}{file_path}',
        body=b'not-json',
        headers={'Content-Type': 'text/plain'},
        timeout=10,
    )
    assert r.status == 400


# --- Not-found cases ---


@pytest.mark.skipif(FAST_MODE, reason='fast mode')
def test_workspace_notfound(server_url: str, authed: AuthedClient) -> None:
    """GET on a nonexistent workspace ID should return 404."""
    path = Endpoint.WORKSPACE.format(workspace_id='nonexistent-ws-id-99999')
    r = authed.get(f'{server_url}{path}', timeout=10)
    assert r.status == 404
    assert json.loads(r.data)['error'] == 'not_found'


@pytest.mark.skipif(FAST_MODE, reason='fast mode')
def test_file_notfound(
    server_url: str, authed: AuthedClient, ws_id: str
) -> None:
    """GET on a nonexistent file path should return 404."""
    file_path = Endpoint.WORKSPACE_FILE.format(
        workspace_id=ws_id, file_path='missing.txt'
    )
    r = authed.get(f'{server_url}{file_path}', timeout=10)
    assert r.status == 404
