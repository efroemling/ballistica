# Released under the MIT License. See LICENSE for details.
#
"""Ballistica public REST API version 1.

Use these APIs to interact with Ballistica cloud components directly.

Simple Example — fetch info for the authenticated account:

.. code-block:: bash

    curl -H 'Authorization: Bearer <your-api-key>' \
https://www.ballistica.net/api/v1/accounts/me

The dataclasses and Enums defined in these submodules serve as schema
documentation and can also be used directly with :mod:`efro.dataclassio`
to parse or construct values::

    from efro.dataclassio import dataclass_from_json
    from bacommon.restapi.v1.accounts import AccountResponse

    account = dataclass_from_json(AccountResponse, response_json_str)

Unless noted otherwise in their descriptions, all endpoints require an
``Authorization: Bearer <api-key>`` header. Responses are JSON; any
non-200 response has an
:class:`~bacommon.restapi.v1.ErrorResponse` body regardless of
which endpoint was called.

See :class:`Endpoint` for the full list of available endpoints and
their usage.
"""

from dataclasses import dataclass
from enum import StrEnum
from typing import Annotated

from efro.dataclassio import IOAttrs, ioprepped

# See `CLAUDE.md` in this directory for package-wide contributor
# conventions (IOAttrs keys, standalone constraint, docstring format,
# file layout).


@ioprepped
@dataclass
class ErrorResponse:
    """Returned by all :class:`Endpoint` members on any non-200 response.

    The HTTP status code conveys the specific failure type.
    """

    #: Machine-readable error code (e.g. ``'not_found'``, ``'unauthorized'``).
    error: Annotated[str, IOAttrs('error')]
    #: Human-readable description of the error.
    message: Annotated[str, IOAttrs('message')]


# Convention for adding entries to Endpoint:
# - Each member's ``#:`` comment must fully document the endpoint: HTTP method,
#   auth requirements, path parameters, query parameters, and a
#   ``:class:`XxxResponse``` cross-reference to its response dataclass.
# - Run ``make docs`` after editing to verify RST formatting and that all
#   cross-references resolve correctly.
class Endpoint(StrEnum):
    """Public REST API v1 endpoint paths.

    Each value is the URL path for an endpoint; see its description for the
    HTTP method, parameters, and response type.

    Tip: use :meth:`str.format` to fill in path parameters::

        url = Endpoint.ACCOUNT.format(account_id='a-1')
    """

    #: ``GET`` — fetch public info for a single account.
    #: Returns :class:`~bacommon.restapi.v1.accounts.AccountResponse`.
    #: Pass ``'me'`` as ``account_id`` to refer to the authenticated account.
    ACCOUNT = '/api/v1/accounts/{account_id}'

    #: ``GET`` — look up an account by its tag (display name).
    #: Returns :class:`~bacommon.restapi.v1.accounts.AccountResponse`.
    ACCOUNT_BY_TAG = '/api/v1/accounts/by-tag/{tag}'

    #: ``GET`` — list all workspaces for the authenticated account.
    #: Returns :class:`~bacommon.restapi.v1.workspaces.WorkspacesResponse`.
    #:
    #: ``POST`` — create a new workspace.
    #: Optional JSON body: ``{"name": "My Workspace"}``.
    #: Returns :class:`~bacommon.restapi.v1.workspaces.WorkspaceResponse`
    #: with HTTP 201.
    WORKSPACES = '/api/v1/workspaces'

    #: ``GET`` — fetch metadata for a single workspace.
    #: Returns :class:`~bacommon.restapi.v1.workspaces.WorkspaceResponse`.
    #:
    #: ``PATCH`` — rename the workspace.
    #: JSON body: ``{"name": "New Name"}``.
    #: Returns :class:`~bacommon.restapi.v1.workspaces.WorkspaceResponse`.
    #:
    #: ``DELETE`` — delete the workspace (creates a 30-day backup
    #: internally). Returns HTTP 204.
    WORKSPACE = '/api/v1/workspaces/{workspace_id}'

    #: ``GET`` — flat listing of all files and directories in the workspace.
    #: Returns
    #: :class:`~bacommon.restapi.v1.workspaces.WorkspaceFilesResponse`.
    WORKSPACE_FILES = '/api/v1/workspaces/{workspace_id}/files'

    #: ``GET`` — download a file. Returns raw file bytes.
    #:
    #: ``POST`` — perform a structured file operation; the ``op`` field
    #: of the JSON body selects which:
    #:
    #: - ``{"op": "mkdir"}`` — create a directory. Returns HTTP 204.
    #: - ``{"op": "move", "dest": "path"}`` — move the file or
    #:   directory. Returns HTTP 204.
    #: - ``{"op": "copy", "dest": "path"}`` — copy the file or
    #:   directory. Returns HTTP 204.
    #: - ``{"op": "upload-init", "size": 123, "sha256": "<hex>"}`` —
    #:   begin uploading or replacing a file. ``size`` is the file's
    #:   byte length and ``sha256`` its 64-char lowercase-hex digest.
    #:   If the server already has that exact content, the file is
    #:   wired into the workspace immediately and ``{"status":
    #:   "exists"}`` is returned — no upload needed. Otherwise returns
    #:   ``{"status": "upload_required", "session_id": ...,
    #:   "upload_url": ..., "upload_headers": ..., "expires_at": ...}``;
    #:   ``PUT`` the raw file bytes to ``upload_url`` with the given
    #:   headers, then issue ``upload-finalize``.
    #: - ``{"op": "upload-finalize", "session_id": "<id>"}`` — complete
    #:   an upload after the signed-url ``PUT`` succeeds. Returns HTTP
    #:   204.
    #:
    #: Parent directories are created automatically by uploads.
    #:
    #: ``DELETE`` — delete a file or directory. Returns HTTP 204.
    WORKSPACE_FILE = '/api/v1/workspaces/{workspace_id}/files/{file_path}'

    #: ``GET`` — fetch the active workspace for the authenticated account.
    #: Returns
    #: :class:`~bacommon.restapi.v1.workspaces.WorkspaceResponse`
    #: or ``null`` if no workspace is active.
    #:
    #: ``POST`` — set the active workspace.
    #: JSON body: ``{"workspace_id": "<id>"}`` to activate a workspace,
    #: or ``{"workspace_id": null}`` to disable syncing.
    #: ``workspace_id`` must refer to a workspace owned by the authenticated
    #: account; any other value (including IDs that do not exist) returns
    #: ``invalid_parameter``.
    #: Returns
    #: :class:`~bacommon.restapi.v1.workspaces.WorkspaceResponse`
    #: or ``null``.
    WORKSPACES_ACTIVE = '/api/v1/workspaces/active'

    #: ``GET`` — look up debug symbols for a prefab binary by the
    #: binary's SHA-256 hash (``exe_sha256``; 64 lowercase hex chars).
    #: No authentication required.
    #: Returns :class:`~bacommon.restapi.v1.prefabs.PrefabSymbolsResponse`
    #: containing a time-limited download URL, or a 404
    #: :class:`~bacommon.restapi.v1.ErrorResponse` if no symbols are
    #: available for that binary (symbols are retained for recent
    #: builds only).
    PREFAB_SYMBOLS = '/api/v1/prefab-symbols/{exe_sha256}'
