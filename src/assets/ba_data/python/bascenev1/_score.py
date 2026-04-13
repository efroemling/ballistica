# Released under the MIT License. See LICENSE for details.
#
"""Score related functionality."""

from __future__ import annotations

from enum import Enum, unique
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import bascenev1


@unique
class ScoreType(Enum):
    """Type of scores."""

    SECONDS = 's'
    MILLISECONDS = 'ms'
    POINTS = 'p'


@dataclass
class ScoreConfig:
    """Settings for how a game handles scores."""

    label: str = 'Score'
    """A label show to the user for scores; 'Score', 'Time Survived', etc."""

    scoretype: bascenev1.ScoreType = ScoreType.POINTS
    """How the score value should be displayed."""

    lower_is_better: bool = False
    """Whether lower scores are preferable. Higher scores are by default."""

    none_is_winner: bool = False
    """Whether a value of None is considered better than other scores.
       By default it is not."""

    version: str = ''
    """To change high-score lists used by a game without renaming the game,
       change this. Defaults to an empty string."""
