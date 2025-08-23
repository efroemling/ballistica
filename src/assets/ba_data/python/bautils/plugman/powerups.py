# Released under the MIT License. See LICENSE for details.
#
# ba_meta require api 9
"""Override default powerup distribution."""

from __future__ import annotations
from typing import Dict, Sequence
import bascenev1 as bs

COUNTS: Dict[str, int] = {
    'triple_bombs': 4,
    'ice_bombs': 4,
    'punch': 0,
    'impact_bombs': 4,
    'land_mines': 4,
    'sticky_bombs': 4,
    'shield': 0,
    'health': 0,
    'curse': 0,
}

_ORDER = [
    'triple_bombs',
    'ice_bombs',
    'punch',
    'impact_bombs',
    'land_mines',
    'sticky_bombs',
    'shield',
    'health',
    'curse',
]


def _custom_distribution() -> Sequence[tuple[str, int]]:
    return tuple((k, int(COUNTS.get(k, 0))) for k in _ORDER)


def set_counts(new_counts: Dict[str, int]) -> None:
    COUNTS.update({k: int(v) for k, v in new_counts.items()})
    _apply_patch()


def _apply_patch() -> None:
    bs.get_default_powerup_distribution = _custom_distribution  # type: ignore[attr-defined]
    # print('[POWERUPS] Patched get_default_powerup_distribution')


# Patch immediately on import (no pushcall).
_apply_patch()
