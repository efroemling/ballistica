# Released under the MIT License. See LICENSE for details.
#
"""Snippets of code for use by the c++ layer."""

# (most of these are self-explanatory)
# pylint: disable=missing-function-docstring

from typing import TYPE_CHECKING

import babase

import _bascenev1
from bascenev1._assetref import texture_from_ref

if TYPE_CHECKING:
    from typing import Any

    import bascenev1


def launch_main_menu_session() -> None:
    assert babase.app.classic is not None

    _bascenev1.new_host_session(babase.app.classic.get_main_menu_session())


def on_instant_replay_begin() -> None:
    # Presentation lives in bascenev1lib (it needs bauiv1, which this
    # package deliberately doesn't depend on).
    from bascenev1lib.instantreplay import show_banner

    show_banner()


def on_instant_replay_end() -> None:
    from bascenev1lib.instantreplay import hide_banner

    hide_banner()


def on_instant_replay_skip_votes(count: int, total: int) -> None:
    from bascenev1lib.instantreplay import set_skip_votes

    set_skip_votes(count, total)


def get_player_icon(sessionplayer: bascenev1.SessionPlayer) -> dict[str, Any]:
    info = sessionplayer.get_icon_info()
    return {
        'texture': texture_from_ref(info['texture']),
        'tint_texture': texture_from_ref(info['tint_texture']),
        'tint_color': info['tint_color'],
        'tint2_color': info['tint2_color'],
    }


def filter_chat_message(msg: str, client_id: int) -> str | None:
    """Intercept/filter chat messages.

    Called for all chat messages while hosting.
    Messages originating from the host will have clientID -1.
    Should filter and return the string to be displayed, or return None
    to ignore the message.
    """
    del client_id  # Unused by default.
    return msg


def local_chat_message(msg: str) -> None:
    classic = babase.app.classic
    assert classic is not None
    party_window = (
        None if classic.party_window is None else classic.party_window()
    )

    if party_window is not None:
        party_window.on_chat_message(msg)
