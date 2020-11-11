# Released under the MIT License. See LICENSE for details.
#
"""Functionality for user-controllable settings."""

from __future__ import annotations

from typing import TYPE_CHECKING
from dataclasses import dataclass

if TYPE_CHECKING:
    from typing import Any, List, Tuple


@dataclass
class Setting:
    """Defines a user-controllable setting for a game or other entity.

    Category: Gameplay Classes
    """

    name: str
    default: Any


@dataclass
class BoolSetting(Setting):
    """A boolean game setting.

    Category: Settings Classes
    """
    default: bool


@dataclass
class IntSetting(Setting):
    """An integer game setting.

    Category: Settings Classes
    """
    default: int
    min_value: int = 0
    max_value: int = 9999
    increment: int = 1


@dataclass
class FloatSetting(Setting):
    """A floating point game setting.

    Category: Settings Classes
    """
    default: float
    min_value: float = 0.0
    max_value: float = 9999.0
    increment: float = 1.0


@dataclass
class ChoiceSetting(Setting):
    """A setting with multiple choices.

    Category: Settings Classes
    """
    choices: List[Tuple[str, Any]]


@dataclass
class IntChoiceSetting(ChoiceSetting):
    """An int setting with multiple choices.

    Category: Settings Classes
    """
    default: int
    choices: List[Tuple[str, int]]


@dataclass
class FloatChoiceSetting(ChoiceSetting):
    """A float setting with multiple choices.

    Category: Settings Classes
    """
    default: float
    choices: List[Tuple[str, float]]
