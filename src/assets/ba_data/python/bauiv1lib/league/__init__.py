# Released under the MIT License. See LICENSE for details.
#
"""League related UI functionality."""

from typing import TYPE_CHECKING

from bauiv1 import classicassets

if TYPE_CHECKING:
    import bauiv1 as bui


def league_display_name(name: str) -> str | bui.LangStr:
    """Return a displayable name for a league tier.

    ``name`` is the raw league id as it arrives from the server. Known
    tiers resolve to their authored entry; anything else (a tier this
    build predates, say) degrades honestly to its own untranslated
    text rather than being silently mistranslated.
    """
    strs = classicassets.strings.league
    return {
        'Bronze': strs.bronze,
        'Silver': strs.silver,
        'Gold': strs.gold,
        'Diamond': strs.diamond,
    }.get(name, name)
