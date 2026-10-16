# Released under the MIT License. See LICENSE for details.
#
"""Enums shared with the native layer.

The engine's C++ versions of these are generated from this module, so
nothing but :mod:`enum` may be imported here, and every class must be
an :class:`~enum.Enum` with ascending int values. Values are spelled
out because some are stored or sent places; never renumber existing
ones. These are also available as ``babase.InputType`` and so on.
"""

from enum import Enum


class InputType(Enum):
    """Types of input a controller can send to the game."""

    UP_DOWN = 2
    LEFT_RIGHT = 3
    JUMP_PRESS = 4
    JUMP_RELEASE = 5
    PUNCH_PRESS = 6
    PUNCH_RELEASE = 7
    BOMB_PRESS = 8
    BOMB_RELEASE = 9
    PICK_UP_PRESS = 10
    PICK_UP_RELEASE = 11
    RUN = 12
    FLY_PRESS = 13
    FLY_RELEASE = 14
    START_PRESS = 15
    START_RELEASE = 16
    HOLD_POSITION_PRESS = 17
    HOLD_POSITION_RELEASE = 18
    LEFT_PRESS = 19
    LEFT_RELEASE = 20
    RIGHT_PRESS = 21
    RIGHT_RELEASE = 22
    UP_PRESS = 23
    UP_RELEASE = 24
    DOWN_PRESS = 25
    DOWN_RELEASE = 26


class QuitType(Enum):
    """Types of quit behavior that can be requested from the app.

    'soft' may hide/reset the app but keep the process running, depending
       on the platform (generally a thing on mobile).

    'back' is a variant of 'soft' which may give 'back-button-pressed'
       behavior depending on the platform. (returning to some previous
       activity instead of dumping to the home screen, etc.)

    'hard' leads to the process exiting. This generally should be avoided
       on platforms such as mobile where apps are expected to keep running
       until killed by the OS.
    """

    SOFT = 0
    BACK = 1
    HARD = 2


class SoundPriority(Enum):
    """How much a sound matters when more sounds want to play than can at
    once. When everything is busy, a new sound takes the place of the
    oldest playing sound of the lowest priority at or below its own
    (sounds that loop are never cut off this way).

    Sounds are 'default' unless their asset says otherwise.
    """

    LOWER = 0
    LOW = 1
    DEFAULT = 2
    HIGH = 3
    HIGHER = 4


class UIScale(Enum):
    """The overall scale the UI is being rendered for. Note that this is
    independent of pixel resolution. For example, a phone and a desktop PC
    might render the game at similar pixel resolutions but the size they
    display content at will vary significantly.

    'large' is used for devices such as desktop PCs where fine details can
       be clearly seen. UI elements are generally smaller on the screen
       and more content can be seen at once.

    'medium' is used for devices such as tablets, TVs, or VR headsets.
       This mode strikes a balance between clean readability and amount of
       content visible.

    'small' is used primarily for phones or other small devices where
       content needs to be presented as large and clear in order to remain
       readable from an average distance.
    """

    SMALL = 0
    MEDIUM = 1
    LARGE = 2


class Permission(Enum):
    """Permissions that can be requested from the OS."""

    STORAGE = 0
