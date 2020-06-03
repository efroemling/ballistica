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
"""Score related functionality."""

from __future__ import annotations

from enum import Enum, unique
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import ba


@unique
class ScoreType(Enum):
    """Type of scores.

    Category: Enums
    """
    SECONDS = 's'
    MILLISECONDS = 'ms'
    POINTS = 'p'


@dataclass
class ScoreConfig:
    """Settings for how a game handles scores.

    Category: Gameplay Classes

    Attrs:

       label
          A label show to the user for scores; 'Score', 'Time Survived', etc.

       scoretype
          How the score value should be displayed.

       lower_is_better
          Whether lower scores are preferable. Higher scores are by default.

       none_is_winner
          Whether a value of None is considered better than other scores.
          By default it is not.

       version
          To change high-score lists used by a game without renaming the game,
          change this. Defaults to an empty string.

    """
    label: str = 'Score'
    scoretype: ba.ScoreType = ScoreType.POINTS
    lower_is_better: bool = False
    none_is_winner: bool = False
    version: str = ''
