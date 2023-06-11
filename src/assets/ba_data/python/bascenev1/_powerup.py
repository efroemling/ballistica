# Released under the MIT License. See LICENSE for details.
#
"""Powerup related functionality."""

from __future__ import annotations

from typing import TYPE_CHECKING
from dataclasses import dataclass

if TYPE_CHECKING:
    from typing import Sequence

    import bascenev1


@dataclass
class PowerupMessage:
    """A message telling an object to accept a powerup.

    Category: **Message Classes**

    This message is normally received by touching a bascenev1.PowerupBox.
    """

    poweruptype: str
    """The type of powerup to be granted (a string).
       See bascenev1.Powerup.poweruptype for available type values."""

    sourcenode: bascenev1.Node | None = None
    """The node the powerup game from, or None otherwise.
       If a powerup is accepted, a bascenev1.PowerupAcceptMessage should be
       sent back to the sourcenode to inform it of the fact. This will
       generally cause the powerup box to make a sound and disappear or
       whatnot."""


@dataclass
class PowerupAcceptMessage:
    """A message informing a bascenev1.Powerup that it was accepted.

    Category: **Message Classes**

    This is generally sent in response to a bascenev1.PowerupMessage
    to inform the box (or whoever granted it) that it can go away.
    """


def get_default_powerup_distribution() -> Sequence[tuple[str, int]]:
    """Standard set of powerups."""
    return (
        ('triple_bombs', 3),
        ('ice_bombs', 3),
        ('punch', 3),
        ('impact_bombs', 3),
        ('land_mines', 2),
        ('sticky_bombs', 3),
        ('shield', 2),
        ('health', 1),
        ('curse', 1),
    )
