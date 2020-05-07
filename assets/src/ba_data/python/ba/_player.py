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
"""Player related functionality."""
from __future__ import annotations
from typing import TYPE_CHECKING, TypeVar

if TYPE_CHECKING:
    from typing import Type
    import ba

T = TypeVar('T')


class BasePlayerData:
    """Base class for custom player data.

    Category: Gameplay Classes

    A convenience class that can be used as a base class for custom
    per-game player data. It simply provides the ability to easily fetch
    an instance of itself for a given ba.Player.
    """

    @classmethod
    def get(cls: Type[T], player: ba.Player) -> T:
        """Return the custom player data associated with a player.

        If one does not exist, it will be created.
        """

        # Store/return an instance of ourself in the player's per-game dict.
        data = player.gamedata.get('playerdata')
        if data is None:
            player.gamedata['playerdata'] = data = cls()
        assert isinstance(data, cls)
        return data
