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
