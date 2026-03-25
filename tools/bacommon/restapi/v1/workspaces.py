# Released under the MIT License. See LICENSE for details.
#
# See CLAUDE.md in this directory for contributor conventions.
"""Workspace response types for REST API v1."""

from __future__ import annotations

import datetime
from dataclasses import dataclass
from enum import StrEnum
from typing import Annotated

from efro.dataclassio import ioprepped, IOAttrs


class WorkspaceEntryType(StrEnum):
    """Type of a workspace entry."""

    FILE = 'file'
    DIRECTORY = 'directory'


@ioprepped
@dataclass
class WorkspaceResponse:
    """Metadata for a single workspace.

    Returned by :attr:`~bacommon.restapi.v1.Endpoint.WORKSPACE`,
    :attr:`~bacommon.restapi.v1.Endpoint.WORKSPACES`, and
    :attr:`~bacommon.restapi.v1.Endpoint.WORKSPACES_ACTIVE`.
    """

    #: Unique workspace ID.
    id: Annotated[str, IOAttrs('id')]
    #: User-assigned workspace name.
    name: Annotated[str, IOAttrs('name')]
    #: Total size of all files in bytes.
    size: Annotated[int, IOAttrs('size')]
    #: When the workspace was created.
    create_time: Annotated[
        datetime.datetime, IOAttrs('create_time', time_format='iso')
    ]
    #: When the workspace was last modified.
    modified_time: Annotated[
        datetime.datetime, IOAttrs('modified_time', time_format='iso')
    ]


@ioprepped
@dataclass
class WorkspacesResponse:
    """List of workspaces for the authenticated account.

    Returned by :attr:`~bacommon.restapi.v1.Endpoint.WORKSPACES`.
    """

    workspaces: Annotated[list[WorkspaceResponse], IOAttrs('workspaces')]


@ioprepped
@dataclass
class WorkspaceEntryResponse:
    """A single file or directory entry in a workspace.

    Part of :class:`WorkspaceFilesResponse`.
    """

    #: Path relative to the workspace root (e.g. ``'mymod/plugin.py'``).
    path: Annotated[str, IOAttrs('path')]
    #: Whether this entry is a file or directory.
    type: Annotated[WorkspaceEntryType, IOAttrs('type')]
    #: Size in bytes. Present for files; absent for directories.
    size: Annotated[
        int | None, IOAttrs('size', soft_default=None, store_default=False)
    ]
    #: Last-modified time. Present for files; may be absent for directories.
    modified_time: Annotated[
        datetime.datetime | None,
        IOAttrs(
            'modified_time',
            time_format='iso',
            soft_default=None,
            store_default=False,
        ),
    ]


@ioprepped
@dataclass
class WorkspaceFilesResponse:
    """Flat listing of all files and directories in a workspace.

    Returned by :attr:`~bacommon.restapi.v1.Endpoint.WORKSPACE_FILES`.
    Entries are sorted by path.
    """

    entries: Annotated[list[WorkspaceEntryResponse], IOAttrs('entries')]
