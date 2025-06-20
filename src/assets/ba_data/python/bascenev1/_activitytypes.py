# Released under the MIT License. See LICENSE for details.
#
"""Some handy base class and special purpose Activity types."""
from __future__ import annotations

from typing import TYPE_CHECKING, override

import babase

import _bascenev1
from bascenev1._activity import Activity

from bascenev1._player import EmptyPlayer
from bascenev1._team import EmptyTeam
from bascenev1._music import MusicType, setmusic


if TYPE_CHECKING:
    import bascenev1
    from bascenev1._lobby import JoinInfo


class EndSessionActivity(Activity[EmptyPlayer, EmptyTeam]):
    """Special Activity to fade out and end the current Session."""

    def __init__(self, settings: dict):
        super().__init__(settings)

        # Keeps prev activity alive while we fade out.
        self.transition_time = 0.25
        self.inherits_tint = True
        self.inherits_slow_motion = True
        self.inherits_vr_camera_offset = True
        self.inherits_vr_overlay_center = True

    @override
    def on_transition_in(self) -> None:
        super().on_transition_in()
        babase.fade_screen(False)
        babase.lock_all_input()

    @override
    def on_begin(self) -> None:
        # pylint: disable=cyclic-import

        classic = babase.app.classic
        plus = babase.app.plus
        assert classic is not None
        assert plus is not None

        main_menu_session = classic.get_main_menu_session()

        super().on_begin()
        babase.unlock_all_input()
        assert babase.app.plus is not None

        call = babase.Call(_bascenev1.new_host_session, main_menu_session)
        if classic.can_show_interstitial():
            plus.ads.call_after_ad(call)
        else:
            babase.pushcall(call)


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

        self._background: bascenev1.Actor | None = None
        self._tips_text: bascenev1.Actor | None = None
        self._join_info: JoinInfo | None = None

    @override
    def on_transition_in(self) -> None:
        # pylint: disable=cyclic-import
        from bascenev1lib.actor.tipstext import TipsText
        from bascenev1lib.actor.background import Background

        super().on_transition_in()
        self._background = Background(
            fade_time=0.5, start_faded=True, show_logo=True
        )
        self._tips_text = TipsText()
        setmusic(MusicType.CHAR_SELECT)
        self._join_info = self.session.lobby.create_join_info()
        babase.set_analytics_screen('Joining Screen')


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
        self._background: bascenev1.Actor | None = None

    @override
    def on_transition_in(self) -> None:
        # pylint: disable=cyclic-import
        from bascenev1lib.actor.background import Background

        super().on_transition_in()
        self._background = Background(
            fade_time=0.5, start_faded=False, show_logo=False
        )

    @override
    def on_begin(self) -> None:
        super().on_begin()

        # Die almost immediately.
        _bascenev1.timer(0.1, self.end)


class ScoreScreenActivity(Activity[EmptyPlayer, EmptyTeam]):
    """A standard score screen that fades in and shows stuff for a while.

    After a specified delay, player input is assigned to end the activity.
    """

    transition_time = 0.5
    inherits_tint = True
    inherits_vr_camera_offset = True
    use_fixed_vr_overlay = True

    default_music: MusicType | None = MusicType.SCORES

    def __init__(self, settings: dict):
        super().__init__(settings)
        self._birth_time = babase.apptime()
        self._min_view_time = 5.0
        self._allow_server_transition = False
        self._background: bascenev1.Actor | None = None
        self._tips_text: bascenev1.Actor | None = None
        self._kicked_off_server_shutdown = False
        self._kicked_off_server_restart = False
        self._default_show_tips = True
        self._custom_continue_message: babase.Lstr | None = None
        self._server_transitioning: bool | None = None

    @override
    def on_player_join(self, player: EmptyPlayer) -> None:
        super().on_player_join(player)
        time_till_assign = max(
            0, self._birth_time + self._min_view_time - babase.apptime()
        )

        # If we're still kicking at the end of our assign-delay, assign this
        # guy's input to trigger us.
        _bascenev1.timer(
            time_till_assign, babase.WeakCall(self._safe_assign, player)
        )

    @override
    def on_transition_in(self) -> None:
        from bascenev1lib.actor.tipstext import TipsText
        from bascenev1lib.actor.background import Background

        super().on_transition_in()
        self._background = Background(
            fade_time=0.5, start_faded=False, show_logo=True
        )
        if self._default_show_tips:
            self._tips_text = TipsText()
        setmusic(self.default_music)

    @override
    def on_begin(self) -> None:
        # pylint: disable=cyclic-import
        from bascenev1lib.actor.text import Text

        super().on_begin()

        # Pop up a 'press any button to continue' statement after our
        # min-view-time show a 'press any button to continue..'
        # thing after a bit.
        assert babase.app.classic is not None
        if babase.app.ui_v1.uiscale is babase.UIScale.LARGE:
            # FIXME: Need a better way to determine whether we've probably
            #  got a keyboard.
            sval = babase.Lstr(resource='pressAnyKeyButtonText')
        else:
            sval = babase.Lstr(resource='pressAnyButtonText')

        Text(
            (
                self._custom_continue_message
                if self._custom_continue_message is not None
                else sval
            ),
            v_attach=Text.VAttach.BOTTOM,
            h_align=Text.HAlign.CENTER,
            flash=True,
            vr_depth=50,
            position=(0, 10),
            scale=0.8,
            color=(0.5, 0.7, 0.5, 0.5),
            transition=Text.Transition.IN_BOTTOM_SLOW,
            transition_delay=self._min_view_time,
        ).autoretain()

    def _player_press(self) -> None:
        # If this activity is a good 'end point', ask server-mode just once if
        # it wants to do anything special like switch sessions or kill the app.
        if (
            self._allow_server_transition
            and babase.app.classic is not None
            and babase.app.classic.server is not None
            and self._server_transitioning is None
        ):
            self._server_transitioning = (
                babase.app.classic.server.handle_transition()
            )
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
            player.assigninput(
                (
                    babase.InputType.JUMP_PRESS,
                    babase.InputType.PUNCH_PRESS,
                    babase.InputType.BOMB_PRESS,
                    babase.InputType.PICK_UP_PRESS,
                ),
                self._player_press,
            )
