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
"""Some handy base class and special purpose Activity types."""
from __future__ import annotations

from typing import TYPE_CHECKING

import _ba
from ba._activity import Activity
from ba._music import setmusic, MusicType
from ba._enums import InputType, UIScale
# False-positive from pylint due to our class-generics-filter.
from ba._player import EmptyPlayer  # pylint: disable=W0611
from ba._team import EmptyTeam  # pylint: disable=W0611

if TYPE_CHECKING:
    from typing import Any, Dict, Optional
    import ba
    from ba._lobby import JoinInfo


class EndSessionActivity(Activity[EmptyPlayer, EmptyTeam]):
    """Special ba.Activity to fade out and end the current ba.Session."""

    def __init__(self, settings: dict):
        super().__init__(settings)

        # Keeps prev activity alive while we fade out.
        self.transition_time = 0.25
        self.inherits_tint = True
        self.inherits_slow_motion = True
        self.inherits_vr_camera_offset = True
        self.inherits_vr_overlay_center = True

    def on_transition_in(self) -> None:
        super().on_transition_in()
        _ba.fade_screen(False)
        _ba.lock_all_input()

    def on_begin(self) -> None:
        # pylint: disable=cyclic-import
        from bastd.mainmenu import MainMenuSession
        from ba._apputils import call_after_ad
        from ba._general import Call
        super().on_begin()
        _ba.unlock_all_input()
        call_after_ad(Call(_ba.new_host_session, MainMenuSession))


class JoinActivity(Activity[EmptyPlayer, EmptyTeam]):
    """Standard activity for waiting for players to join.

    It shows tips and other info and waits for all players to check ready.
    """

    def __init__(self, settings: dict):
        super().__init__(settings)

        # This activity is a special 'joiner' activity.
        # It will get shut down as soon as all players have checked ready.
        self.is_joining_activity = True

        # Players may be idle waiting for joiners; lets not kick them for it.
        self.allow_kick_idle_players = False

        # In vr mode we don't want stuff moving around.
        self.use_fixed_vr_overlay = True

        self._background: Optional[ba.Actor] = None
        self._tips_text: Optional[ba.Actor] = None
        self._join_info: Optional[JoinInfo] = None

    def on_transition_in(self) -> None:
        # pylint: disable=cyclic-import
        from bastd.actor.tipstext import TipsText
        from bastd.actor.background import Background
        super().on_transition_in()
        self._background = Background(fade_time=0.5,
                                      start_faded=True,
                                      show_logo=True)
        self._tips_text = TipsText()
        setmusic(MusicType.CHAR_SELECT)
        self._join_info = self.session.lobby.create_join_info()
        _ba.set_analytics_screen('Joining Screen')


class TransitionActivity(Activity[EmptyPlayer, EmptyTeam]):
    """A simple overlay to fade out/in.

    Useful as a bare minimum transition between two level based activities.
    """

    # Keep prev activity alive while we fade in.
    transition_time = 0.5
    inherits_slow_motion = True  # Don't change.
    inherits_tint = True  # Don't change.
    inherits_vr_camera_offset = True  # Don't change.
    inherits_vr_overlay_center = True
    use_fixed_vr_overlay = True

    def __init__(self, settings: dict):
        super().__init__(settings)
        self._background: Optional[ba.Actor] = None

    def on_transition_in(self) -> None:
        # pylint: disable=cyclic-import
        from bastd.actor import background  # FIXME: Don't use bastd from ba.
        super().on_transition_in()
        self._background = background.Background(fade_time=0.5,
                                                 start_faded=False,
                                                 show_logo=False)

    def on_begin(self) -> None:
        super().on_begin()

        # Die almost immediately.
        _ba.timer(0.1, self.end)


class ScoreScreenActivity(Activity[EmptyPlayer, EmptyTeam]):
    """A standard score screen that fades in and shows stuff for a while.

    After a specified delay, player input is assigned to end the activity.
    """

    transition_time = 0.5
    inherits_tint = True
    inherits_vr_camera_offset = True
    use_fixed_vr_overlay = True

    default_music: Optional[MusicType] = MusicType.SCORES

    def __init__(self, settings: dict):
        super().__init__(settings)
        self._birth_time = _ba.time()
        self._min_view_time = 5.0
        self._allow_server_transition = False
        self._background: Optional[ba.Actor] = None
        self._tips_text: Optional[ba.Actor] = None
        self._kicked_off_server_shutdown = False
        self._kicked_off_server_restart = False
        self._default_show_tips = True
        self._custom_continue_message: Optional[ba.Lstr] = None
        self._server_transitioning: Optional[bool] = None

    def on_player_join(self, player: EmptyPlayer) -> None:
        from ba._general import WeakCall
        super().on_player_join(player)
        time_till_assign = max(
            0, self._birth_time + self._min_view_time - _ba.time())

        # If we're still kicking at the end of our assign-delay, assign this
        # guy's input to trigger us.
        _ba.timer(time_till_assign, WeakCall(self._safe_assign, player))

    def on_transition_in(self) -> None:
        from bastd.actor.tipstext import TipsText
        from bastd.actor.background import Background
        super().on_transition_in()
        self._background = Background(fade_time=0.5,
                                      start_faded=False,
                                      show_logo=True)
        if self._default_show_tips:
            self._tips_text = TipsText()
        setmusic(self.default_music)

    def on_begin(self) -> None:
        # pylint: disable=cyclic-import
        from bastd.actor.text import Text
        from ba import _lang
        super().on_begin()

        # Pop up a 'press any button to continue' statement after our
        # min-view-time show a 'press any button to continue..'
        # thing after a bit.
        if _ba.app.ui.uiscale is UIScale.LARGE:
            # FIXME: Need a better way to determine whether we've probably
            #  got a keyboard.
            sval = _lang.Lstr(resource='pressAnyKeyButtonText')
        else:
            sval = _lang.Lstr(resource='pressAnyButtonText')

        Text(self._custom_continue_message
             if self._custom_continue_message is not None else sval,
             v_attach=Text.VAttach.BOTTOM,
             h_align=Text.HAlign.CENTER,
             flash=True,
             vr_depth=50,
             position=(0, 10),
             scale=0.8,
             color=(0.5, 0.7, 0.5, 0.5),
             transition=Text.Transition.IN_BOTTOM_SLOW,
             transition_delay=self._min_view_time).autoretain()

    def _player_press(self) -> None:

        # If this activity is a good 'end point', ask server-mode just once if
        # it wants to do anything special like switch sessions or kill the app.
        if (self._allow_server_transition and _ba.app.server is not None
                and self._server_transitioning is None):
            self._server_transitioning = _ba.app.server.handle_transition()
            assert isinstance(self._server_transitioning, bool)

        # If server-mode is handling this, don't do anything ourself.
        if self._server_transitioning is True:
            return

        # Otherwise end the activity normally.
        self.end()

    def _safe_assign(self, player: EmptyPlayer) -> None:

        # Just to be extra careful, don't assign if we're transitioning out.
        # (though theoretically that should be ok).
        if not self.is_transitioning_out() and player:
            player.assigninput((InputType.JUMP_PRESS, InputType.PUNCH_PRESS,
                                InputType.BOMB_PRESS, InputType.PICK_UP_PRESS),
                               self._player_press)
