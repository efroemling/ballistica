# Released under the MIT License. See LICENSE for details.
#
"""Kill-cam triggering and on-screen presentation for instant replays.

The engine does the actual work (see
``ballistica/scene_v1/support/instant_replay_recorder.h``); this module
decides *when* a replay is worth showing and puts the banner over it
while it plays.
"""

from typing import TYPE_CHECKING

import babase
import bascenev1 as bs

if TYPE_CHECKING:
    from typing import Any

# How far back a kill-cam looks, and how slowly it plays. The engine
# keeps a somewhat longer window than this, so asking for a bit less
# leaves room for the clip to start at a keyframe.
KILL_CAM_DURATION = 4.0
KILL_CAM_SPEED = 0.4

# Kills below this importance don't earn a cut-away. `importance` comes
# from Spaz.get_death_points and is already the game's own notion of "was
# that a big deal" (1 for an ordinary kill, higher for the flashy ones).
MIN_IMPORTANCE = 2

# Wall-clock seconds between kill-cams. Without this an eight-player
# free-for-all would spend more time in replays than in the game.
COOLDOWN_SECONDS = 25.0

# Don't interrupt the opening moments of a round; there's nothing worth
# replaying yet and the engine's window isn't full.
MIN_ROUND_AGE_SECONDS = 8.0

_g_last_kill_cam_time: float | None = None


def maybe_play_kill_cam(activity: bs.Activity, importance: int) -> None:
    """Show a kill-cam for a kill that just happened, if it earns one.

    Called from ``GameActivity.handlemessage`` right after a kill is
    scored; `importance` is the value the scoring system already
    computed for it, so we don't form a second opinion about what counts
    as a good kill. Cheap and silent when it decides not to fire.
    """
    if importance < MIN_IMPORTANCE:
        return
    _maybe_play(activity)


def maybe_play_death_cam(activity: bs.Activity, killed: bool) -> None:
    """Show a death-cam when a player goes down in co-op.

    Co-op never reaches the kill-cam rule: what kills you there is a bot
    or a hazard, not another player, so there is no cross-team killer to
    key off. The moment worth replaying is your own death instead.
    """
    # Deliberately co-op only. In a versus game the kill-cam already
    # covers the interesting deaths, and firing on both would mean two
    # replays competing over the same moment.
    if not killed:
        # Left the game, or the round ended out from under them.
        return
    if not isinstance(activity.session, bs.CoopSession):
        return
    _maybe_play(activity)


def _maybe_play(activity: bs.Activity) -> None:
    """Shared gating for both cams: config, cooldown, round age."""
    global _g_last_kill_cam_time  # pylint: disable=global-statement

    if not babase.app.config.resolve('Instant Replay'):
        return

    # A replay while the round is wrapping up would fight the score
    # screen for the screen.
    if activity.has_ended():
        return

    now = babase.apptime()
    if (
        _g_last_kill_cam_time is not None
        and now - _g_last_kill_cam_time < COOLDOWN_SECONDS
    ):
        return

    # Nothing worth replaying in the opening moments, and the engine's
    # window isn't full yet either.
    try:
        if bs.time() < MIN_ROUND_AGE_SECONDS:
            return
    except bs.ContextError:
        return

    _g_last_kill_cam_time = now
    bs.play_instant_replay(duration=KILL_CAM_DURATION, speed=KILL_CAM_SPEED)


# ------------------------------ presentation --------------------------------

_g_banner: Any = None


def show_banner() -> None:
    """Put the 'Instant Replay' banner up over the clip.

    Lives in the ui overlay stack rather than the scene, since the scene
    on screen belongs to the replay and the live one is frozen.
    """
    global _g_banner  # pylint: disable=global-statement

    import bauiv1 as bui

    if _g_banner is not None:
        return

    parent = bui.get_special_widget('overlay_stack')

    # Cover the whole virtual screen so we can place things against real
    # screen edges; the container itself draws nothing.
    width, height = babase.get_virtual_screen_size()
    _g_banner = bui.containerwidget(
        parent=parent,
        size=(width, height),
        background=False,
        transition='in_right',
        position=(0, 0),
        selectable=True,
    )
    bui.textwidget(
        parent=_g_banner,
        position=(width * 0.5 - 200, height - 110),
        size=(400, 40),
        text=babase.Lstr(value='Instant Replay'),
        h_align='center',
        v_align='center',
        color=(1.0, 0.9, 0.3),
        scale=1.5,
        shadow=1.0,
        flatness=1.0,
    )
    bui.buttonwidget(
        parent=_g_banner,
        position=(width * 0.5 - 75, height - 165),
        size=(150, 40),
        label=babase.Lstr(value='Skip'),
        text_scale=0.8,
        on_activate_call=_skip,
        autoselect=True,
    )


def hide_banner() -> None:
    """Take the banner back down."""
    global _g_banner  # pylint: disable=global-statement

    import bauiv1 as bui

    if _g_banner is None:
        return
    bui.containerwidget(edit=_g_banner, transition='out_right')
    _g_banner = None


def _skip() -> None:
    bs.stop_instant_replay()
