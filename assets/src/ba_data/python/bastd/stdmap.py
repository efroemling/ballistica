# Released under the MIT License. See LICENSE for details.
#
"""Defines standard map type."""

from __future__ import annotations

from typing import TYPE_CHECKING

import ba

if TYPE_CHECKING:
    from typing import Any


def _get_map_data(name: str) -> dict[str, Any]:
    import json

    print('Would get map data', name)
    with open(
        'ba_data/data/maps/' + name + '.json', encoding='utf-8'
    ) as infile:
        mapdata = json.loads(infile.read())
    assert isinstance(mapdata, dict)
    return mapdata


class StdMap(ba.Map):
    """A map completely defined by asset data."""

    _data: dict[str, Any] | None = None

    @classmethod
    def _getdata(cls) -> dict[str, Any]:
        if cls._data is None:
            cls._data = _get_map_data('bridgit')
        return cls._data

    def __init__(self) -> None:
        super().__init__()
