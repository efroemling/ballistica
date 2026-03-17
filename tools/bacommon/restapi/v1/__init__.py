# Released under the MIT License. See LICENSE for details.
#
"""Public REST API v1 endpoint enum for the Ballistica master-server.

See ``CLAUDE.md`` in this directory for package-wide contributor conventions
(IOAttrs keys, standalone constraint, docstring format, file layout).

All endpoints require an ``Authorization: Bearer <key>`` header. Responses
are JSON; any non-200 response has an
:class:`~bacommon.restapi.v1.accounts.ErrorResponse` body regardless of
which endpoint was called.

See :class:`Endpoint` for the full list of available endpoints and
their usage.

Example — fetch info for the authenticated account:

.. code-block:: bash

    curl -H 'Authorization: Bearer <your-api-key>' \\
        https://www.ballistica.net/api/v1/accounts/me

The dataclasses in the submodules serve as schema documentation and can
also be used directly with :mod:`efro.dataclassio` to parse or construct
values::

    from efro.dataclassio import dataclass_from_json
    from bacommon.restapi.v1.accounts import AccountResponse

    account = dataclass_from_json(AccountResponse, response_json_str)
"""

from enum import StrEnum


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
    #: ``PUT`` — upload or replace a file. Raw body = file contents.
    #: Parent directories are created automatically. Returns HTTP 204.
    #:
    #: ``DELETE`` — delete a file or directory. Returns HTTP 204.
    #:
    #: ``POST`` — perform a structured file operation.
    #: JSON body: ``{"op": "mkdir"}``, ``{"op": "move", "dest": "path"}``,
    #: or ``{"op": "copy", "dest": "path"}``.
    #: Returns HTTP 204.
    WORKSPACE_FILE = '/api/v1/workspaces/{workspace_id}/files/{file_path}'
