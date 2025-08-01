# Released under the MIT License. See LICENSE for details.
#
"""Functionality related to the join screen for multi-team sessions."""

from __future__ import annotations

from typing import override, TYPE_CHECKING

import babase
from bascenev1 import Activity, EmptyPlayer, EmptyTeam, MusicType, setmusic

from .lobby import TournamentLobby

if TYPE_CHECKING:
    import bascenev1
    from bascenev1lib.actor.text import Text
    from .lobby import TournamentJoinInfo


class TournamentJoinActivity(Activity[EmptyPlayer, EmptyTeam]):
    """JoinActivity related to tournament related things."""

    def __init__(self, settings: dict):
        super().__init__(settings)

        # This activity is a special "joiner" activity.
        # It will get shut down as soon as all players have checked ready.
        self.is_joining_activity = True

        # Players may be idle waiting for joiners; lets not kick them for it.
        self.allow_kick_idle_players = False

        # In vr mode we don"t want stuff moving around.
        self.use_fixed_vr_overlay = True

        self._background: bascenev1.Actor | None = None
        self._tips_text: bascenev1.Actor | None = None
        self._join_info: TournamentJoinInfo | None = None

        self._next_up_text: Text | None = None

    @override
    def on_transition_in(self) -> None:
        # pylint: disable=cyclic-import
        from bascenev1lib.actor.background import Background

        super().on_transition_in()
        self._background = Background(
            fade_time=0.5, start_faded=True, show_logo=False
        )
        self.session.lobby = TournamentLobby()
        # self._tips_text = TipsText()
        setmusic(MusicType.CHAR_SELECT)
        self._join_info = self.session.lobby.create_join_info()
        babase.set_analytics_screen("Joining Screen")

        # from bascenev1lib.actor.controlsguide import ControlsGuide

        # ControlsGuide(delay=1.0).autoretain()
        # assert isinstance(session, bs.MultiTeamSession)

        # # Show info about the next up game.
        # self._next_up_text = Text(
        #     # bs.Lstr(
        #     #     value="${1} ${2}",
        #     #     subs=[
        #     #         ("${1}", bs.Lstr(resource="upFirstText")),
        #     #         ("${2}", session.get_next_game_description()),
        #     #     ],
        #     # ),
        #     "stupid text",
        #     h_attach=Text.HAttach.CENTER,
        #     scale=0.7,
        #     v_attach=Text.VAttach.TOP,
        #     h_align=Text.HAlign.CENTER,
        #     position=(0, -70),
        #     flash=False,
        #     color=(0.5, 0.5, 0.5, 1.0),
        #     transition=Text.Transition.FADE_IN,
        #     transition_delay=5.0,
        # )
