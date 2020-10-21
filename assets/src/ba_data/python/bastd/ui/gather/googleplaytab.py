# Released under the MIT License. See LICENSE for details.
#
"""Defines the Google Play tab in the gather UI."""

from __future__ import annotations

from typing import TYPE_CHECKING

import _ba
import ba
from bastd.ui.gather.bases import GatherTab

if TYPE_CHECKING:
    from typing import Optional
    from bastd.ui.gather import GatherWindow


class GooglePlayGatherTab(GatherTab):
    """The public tab in the gather UI"""

    def __init__(self, window: GatherWindow) -> None:
        super().__init__(window)
        self._container: Optional[ba.Widget] = None

    def on_activate(
        self,
        parent_widget: ba.Widget,
        tab_button: ba.Widget,
        region_width: float,
        region_height: float,
        region_left: float,
        region_bottom: float,
    ) -> ba.Widget:
        c_width = region_width
        c_height = 380.0
        self._container = ba.containerwidget(
            parent=parent_widget,
            position=(region_left,
                      region_bottom + (region_height - c_height) * 0.5),
            size=(c_width, c_height),
            background=False,
            selection_loops_to_parent=True)
        v = c_height - 30.0
        ba.textwidget(
            parent=self._container,
            position=(c_width * 0.5, v - 140.0),
            color=(0.6, 1.0, 0.6),
            scale=1.3,
            size=(0.0, 0.0),
            maxwidth=c_width * 0.9,
            h_align='center',
            v_align='center',
            text=ba.Lstr(resource='googleMultiplayerDiscontinuedText'))
        return self._container

    def _on_google_play_show_invites_press(self) -> None:
        from bastd.ui import account
        if (_ba.get_account_state() != 'signed_in'
                or _ba.get_account_type() != 'Google Play'):
            account.show_sign_in_prompt('Google Play')
        else:
            _ba.show_invites_ui()

    def _on_google_play_invite_press(self) -> None:
        from bastd.ui.confirm import ConfirmWindow
        from bastd.ui.account import show_sign_in_prompt
        if (_ba.get_account_state() != 'signed_in'
                or _ba.get_account_type() != 'Google Play'):
            show_sign_in_prompt('Google Play')
        else:
            # If there's google play people connected to us, inform the user
            # that they will get disconnected. Otherwise just go ahead.
            google_player_count = (_ba.get_google_play_party_client_count())
            if google_player_count > 0:
                ConfirmWindow(
                    ba.Lstr(resource='gatherWindow.'
                            'googlePlayReInviteText',
                            subs=[('${COUNT}', str(google_player_count))]),
                    lambda: ba.timer(
                        0.2, _ba.invite_players, timetype=ba.TimeType.REAL),
                    width=500,
                    height=150,
                    ok_text=ba.Lstr(resource='gatherWindow.'
                                    'googlePlayInviteText'))
            else:
                ba.timer(0.1, _ba.invite_players, timetype=ba.TimeType.REAL)
