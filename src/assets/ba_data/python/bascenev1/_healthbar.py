# Released under the MIT License. See LICENSE for details.
#
"""Health bar related functionality."""

from enum import IntEnum, unique


@unique
class HealthBarDisplay(IntEnum):
    """When a shield node draws its health bar.

    Set as a shield node's ``health_bar_display`` attr. The older
    ``always_show_health_bar`` attr still works and is only consulted
    while this is :attr:`DEFAULT`; any other value takes precedence over
    it.
    """

    #: Classic behavior -- :attr:`ALWAYS` if the shield's
    #: ``always_show_health_bar`` is True, otherwise :attr:`AFTER_DAMAGE`.
    DEFAULT = 0

    #: Show the bar briefly after the shield takes damage.
    AFTER_DAMAGE = 1

    #: Always show the bar.
    ALWAYS = 2

    #: Never show the bar.
    NEVER = 3
