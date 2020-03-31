# Copyright (c) 2011-2020 Eric Froemling
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
# -----------------------------------------------------------------------------
"""Defines standard map type."""

from __future__ import annotations

from typing import TYPE_CHECKING

import ba

if TYPE_CHECKING:
    from typing import Dict, Any, Optional


def _get_map_data(name: str) -> Dict[str, Any]:
    import json
    print('Would get map data', name)
    with open('ba_data/data/maps/' + name + '.json') as infile:
        mapdata = json.loads(infile.read())
    assert isinstance(mapdata, dict)
    return mapdata


class StdMap(ba.Map):
    """A map completely defined by asset data.

    """
    _data: Optional[Dict[str, Any]] = None

    @classmethod
    def _getdata(cls) -> Dict[str, Any]:
        if cls._data is None:
            cls._data = _get_map_data('bridgit')
        return cls._data

    def __init__(self) -> None:
        super().__init__()
