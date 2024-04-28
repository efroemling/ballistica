# Released under the MIT License. See LICENSE for details.
#
"""Functionality related to game builds."""

from __future__ import annotations

import datetime
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Annotated

from efro.dataclassio import ioprepped, IOAttrs

if TYPE_CHECKING:
    pass


@ioprepped
@dataclass
class BuildInfoSet:
    """Set of build infos."""

    @dataclass
    class Entry:
        """Info about a particular app build."""

        filename: Annotated[str, IOAttrs('fname')]
        size: Annotated[int, IOAttrs('size')]
        version: Annotated[str, IOAttrs('version')]
        build_number: Annotated[int, IOAttrs('build')]
        checksum: Annotated[str, IOAttrs('checksum')]
        createtime: Annotated[datetime.datetime, IOAttrs('createtime')]

    builds: Annotated[list[Entry], IOAttrs('builds')] = field(
        default_factory=list
    )
