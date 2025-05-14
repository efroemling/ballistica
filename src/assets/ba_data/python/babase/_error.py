# Released under the MIT License. See LICENSE for details.
#
"""Error related functionality."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Any


class ContextError(Exception):
    """Raised when a call is made in an invalid context.

    Examples of this include calling UI functions within an activity
    context or calling scene manipulation functions outside of a scene
    context.
    """


class NotFoundError(Exception):
    """Raised when a referenced object does not exist."""


class PlayerNotFoundError(NotFoundError):
    """Raised when an expected player does not exist."""


class SessionPlayerNotFoundError(NotFoundError):
    """Exception raised when an expected session-player does not exist."""


class TeamNotFoundError(NotFoundError):
    """Raised when an expected team does not exist."""


class MapNotFoundError(NotFoundError):
    """Raised when an expected map does not exist."""


class DelegateNotFoundError(NotFoundError):
    """Raised when an expected delegate object does not exist."""


class SessionTeamNotFoundError(NotFoundError):
    """Raised when an expected session-team does not exist."""


class NodeNotFoundError(NotFoundError):
    """Raised when an expected node does not exist."""


class ActorNotFoundError(NotFoundError):
    """Raised when an expected actor does not exist."""


class ActivityNotFoundError(NotFoundError):
    """Raised when an expected activity does not exist."""


class SessionNotFoundError(NotFoundError):
    """Raised when an expected session does not exist."""


class InputDeviceNotFoundError(NotFoundError):
    """Raised when an expected input-device does not exist."""


class WidgetNotFoundError(NotFoundError):
    """Raised when an expected widget does not exist."""
