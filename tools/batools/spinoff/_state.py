# Released under the MIT License. See LICENSE for details.
#
"""State data for spinoff."""

from __future__ import annotations

from typing import TYPE_CHECKING, Annotated
from enum import Enum
from dataclasses import dataclass

from efro.dataclassio import (
    ioprepped,
    IOAttrs,
    dataclass_from_json,
    dataclass_to_json,
)

if TYPE_CHECKING:
    pass


class EntityType(Enum):
    """Type of something in the dst project."""

    FILE = 'f'
    SYMLINK = 's'


@ioprepped
@dataclass
class SrcEntity:
    """Data for a src entity."""

    entity_type: Annotated[EntityType, IOAttrs('t')]
    dst: Annotated[str, IOAttrs('d')]


@ioprepped
@dataclass
class DstEntity:
    """Data for something in the dst project."""

    entity_type: Annotated[EntityType, IOAttrs('t')]
    env_hash: Annotated[str | None, IOAttrs('e')]
    src_path: Annotated[str | None, IOAttrs('sp')]
    src_mtime: Annotated[float | None, IOAttrs('sm')]
    src_size: Annotated[int | None, IOAttrs('ss')]
    dst_mtime: Annotated[float | None, IOAttrs('dm')]
    dst_size: Annotated[int | None, IOAttrs('ds')]


@ioprepped
@dataclass
class DstEntitySet:
    """All entities for a project."""

    entities: Annotated[dict[str, DstEntity], IOAttrs('e')]

    @classmethod
    def read_from_file(cls, path: str) -> DstEntitySet:
        """Load from a file."""
        with open(path, 'r', encoding='utf-8') as infile:
            return dataclass_from_json(cls, infile.read())

    def write_to_file(self, path: str) -> None:
        """Save to a file."""
        with open(path, 'w', encoding='utf-8') as outfile:
            outfile.write(dataclass_to_json(self))
