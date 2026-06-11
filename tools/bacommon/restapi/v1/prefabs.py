# Released under the MIT License. See LICENSE for details.
#
"""Prefab-build related REST API types."""

# See CLAUDE.md in this directory for contributor conventions.

from __future__ import annotations

from dataclasses import dataclass
from typing import Annotated

from efro.dataclassio import IOAttrs, ioprepped


@ioprepped
@dataclass
class PrefabSymbolsResponse:
    """Debug-symbols lookup result for a prefab binary.

    Returned by :attr:`~bacommon.restapi.v1.Endpoint.PREFAB_SYMBOLS`.
    """

    #: Suggested local file name for the symbols file (the app's
    #: ``.pdb`` name). Place the downloaded file under this
    #: name next to the binary it was looked up for; debuggers and the
    #: engine's own stack-trace symbolication will then find it
    #: automatically.
    file_name: Annotated[str, IOAttrs('file_name')]

    #: Size of the symbols file in bytes.
    size: Annotated[int, IOAttrs('size')]

    #: Time-limited download URL for the symbols file.
    download_url: Annotated[str, IOAttrs('download_url')]
