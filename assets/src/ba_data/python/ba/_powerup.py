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
"""Powerup related functionality."""

from __future__ import annotations

from typing import TYPE_CHECKING
from dataclasses import dataclass

if TYPE_CHECKING:
    from typing import Sequence, Tuple, Optional
    import ba


@dataclass
class PowerupMessage:
    """A message telling an object to accept a powerup.

    Category: Message Classes

    This message is normally received by touching a ba.PowerupBox.

    Attributes:

       poweruptype
          The type of powerup to be granted (a string).
          See ba.Powerup.poweruptype for available type values.

       sourcenode
          The node the powerup game from, or None otherwise.
          If a powerup is accepted, a ba.PowerupAcceptMessage should be sent
          back to the sourcenode to inform it of the fact. This will generally
          cause the powerup box to make a sound and disappear or whatnot.
    """
    poweruptype: str
    sourcenode: Optional[ba.Node] = None


@dataclass
class PowerupAcceptMessage:
    """A message informing a ba.Powerup that it was accepted.

    Category: Message Classes

    This is generally sent in response to a ba.PowerupMessage
    to inform the box (or whoever granted it) that it can go away.
    """


def get_default_powerup_distribution() -> Sequence[Tuple[str, int]]:
    """Standard set of powerups."""
    return (('triple_bombs', 3), ('ice_bombs', 3), ('punch', 3),
            ('impact_bombs', 3), ('land_mines', 2), ('sticky_bombs', 3),
            ('shield', 2), ('health', 1), ('curse', 1))
