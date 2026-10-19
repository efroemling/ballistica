# Released under the MIT License. See LICENSE for details.
#
"""Triggering and on-screen presentation for instant replays.

The engine does the actual work (see
``ballistica/scene_v1/support/instant_replay_recorder.h``); this module
decides *when* a replay is worth showing and puts the banner over it
while it plays.

Game modes ask for replays of their own big moments (a goal, a capture)
through :func:`play_highlight`. The generic kill-cam and death-cam are
opt-in per game (:attr:`bascenev1.GameActivity.instant_replay_kill_cams`)
since in score-driven modes they would compete with those highlights.
"""

from typing import TYPE_CHECKING

import babase
import bascenev1 as bs

if TYPE_CHECKING:
    from typing import Any, Callable

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
# free-for-all would spend more time in replays than in the game. Applies
# to the kill-cam only; a death-cam fires on every death it's offered.
COOLDOWN_SECONDS = 25.0

# Don't interrupt the opening moments of a round; there's nothing worth
# replaying yet and the engine's window isn't full. Kill-cam only, same
# as the cooldown.
MIN_ROUND_AGE_SECONDS = 8.0

# How far back a highlight looks and how slowly it plays. The post-roll
# is how long after the moment we wait before cutting away: a clip ends
# at the instant it starts, so without it the replay would stop right
# as the ball crosses the line.
HIGHLIGHT_DURATION = 4.0
HIGHLIGHT_SPEED = 0.5
HIGHLIGHT_POST_ROLL = 1.0

# Scene seconds between asking for a highlight and running its `then`
# callback. Starting a replay is deferred to the next event-loop pass,
# and scene time stands still while the clip plays, so this only has to
# cover that hop; `then` lands just after the clip hands back.
_THEN_DELAY = 0.1

_g_last_kill_cam_time: float | None = None


def play_highlight(
    activity: bs.GameActivity,
    *,
    then: Callable[[], Any] | None = None,
    post_roll: float = HIGHLIGHT_POST_ROLL,
) -> None:
    """Replay a moment that just happened, once its post-roll has played.

    For game modes to call on their own big moments: a goal, a flag
    capture. Must be called in the activity's context.

    `then` runs after the replay (or right away, if there won't be
    one). Pass the game's ending here for a game-winning moment: ending
    straight away would put the score screen up before the clip could
    be shown.
    """
    if not _replays_enabled():
        if then is not None:
            then()
        return

    def _play() -> None:
        _maybe_play(
            activity,
            rate_limit=False,
            duration=HIGHLIGHT_DURATION,
            speed=HIGHLIGHT_SPEED,
        )

    def _then() -> None:
        # The round may have been ended some other way in the meantime
        # (time ran out during the post-roll, say).
        if then is not None and not activity.has_ended():
            then()

    bs.timer(post_roll, _play)
    if then is not None:
        bs.timer(post_roll + _THEN_DELAY, _then)


def _replays_enabled() -> bool:
    return bool(babase.app.config.resolve('Instant Replay'))


def maybe_play_kill_cam(activity: bs.Activity, importance: int) -> None:
    """Show a kill-cam for a kill that just happened, if it earns one.

    Called from ``GameActivity.handlemessage`` right after a kill is
    scored; `importance` is the value the scoring system already
    computed for it, so we don't form a second opinion about what counts
    as a good kill. Cheap and silent when it decides not to fire.
    """
    if not _kill_cams_wanted(activity):
        return
    if importance < MIN_IMPORTANCE:
        return
    _maybe_play(activity)


def maybe_play_death_cam(activity: bs.Activity, killed: bool) -> None:
    """Show a death-cam when a player goes down with nobody to blame.

    Co-op and solo games never reach the kill-cam rule: what kills you
    there is a bot or a hazard, not another player, so there is no
    cross-team killer to key off. The moment worth replaying is your own
    death instead.

    Every such death gets one: unlike the kill-cam there's no cooldown
    or round-age floor here, since a death is already the rare event the
    kill-cam's rate limiting exists to find.
    """
    if not killed:
        # Left the game, or the round ended out from under them.
        return
    if not _kill_cams_wanted(activity):
        return

    # Deliberately not for multi-human versus games: there the kill-cam
    # already covers the interesting deaths, and firing on both would
    # mean two replays competing over the same moment. A lone human in a
    # ffa/teams game can't trip the kill-cam anyway (that needs a killer
    # on another team), so widening to solo play adds no overlap.
    session = activity.session
    if (
        not isinstance(session, bs.CoopSession)
        and len(session.sessionplayers) > 1
    ):
        return
    _maybe_play(activity, rate_limit=False)


def _kill_cams_wanted(activity: bs.Activity) -> bool:
    return isinstance(activity, bs.GameActivity) and bool(
        activity.instant_replay_kill_cams
    )


def _maybe_play(
    activity: bs.Activity,
    *,
    rate_limit: bool = True,
    duration: float = KILL_CAM_DURATION,
    speed: float = KILL_CAM_SPEED,
) -> None:
    """Shared gating for both cams: config, cooldown, round age.

    `rate_limit` covers the two throttles that exist to keep kill-cams
    from swamping a busy match (the cooldown and the round-age floor).
    The death-cam turns it off; the config switch and the round-ended
    check always apply.
    """
    global _g_last_kill_cam_time  # pylint: disable=global-statement

    if not _replays_enabled():
        return

    # A replay while the round is wrapping up would fight the score
    # screen for the screen.
    if activity.has_ended():
        return

    now = babase.apptime()
    if (
        rate_limit
        and _g_last_kill_cam_time is not None
        and now - _g_last_kill_cam_time < COOLDOWN_SECONDS
    ):
        return

    # We need a scene context to read round age or to play at all. The
    # age floor itself is throttling: nothing worth replaying in the
    # opening moments, and the engine's window isn't full yet either.
    try:
        round_age = bs.time()
    except bs.ContextError:
        return
    if rate_limit and round_age < MIN_ROUND_AGE_SECONDS:
        return

    _g_last_kill_cam_time = now
    bs.play_instant_replay(duration=duration, speed=speed)


# ------------------------------ presentation --------------------------------

_g_banner: Any = None
_g_vote_text: Any = None


def show_banner() -> None:
    """Put the 'Instant Replay' banner up over the clip.

    Lives in the ui overlay stack rather than the scene, since the scene
    on screen belongs to the replay and the live one is frozen.
    """
    global _g_banner  # pylint: disable=global-statement

    import bauiv1 as bui
    from bauiv1 import _classicassets

    if _g_banner is not None or babase.app.env.headless:
        return

    parent = bui.get_special_widget('overlay_stack')

    # Cover the whole virtual screen so we can place things against real
    # screen edges; the container itself draws nothing.
    width, height = babase.get_virtual_screen_size()
    # Selectable with both callbacks wired so any press dismisses the
    # clip: while we're up, the overlay stack counts as 'main ui' (see
    # UIV1FeatureSet::IsMainUIVisible), so the ui-owning device's keys
    # arrive here as widget messages rather than reaching the input
    # delegate. jump/punch/pick-up/start arrive as activate and bomb as
    # cancel, so covering both is what makes "press anything" true.
    _g_banner = bui.containerwidget(
        parent=parent,
        size=(width, height),
        background=False,
        transition='in_right',
        position=(0, 0),
        selectable=True,
        root_selectable=True,
        # A press is a vote, not an immediate skip: the engine ends the
        # clip once every player has asked, like the tutorial's skip.
        on_activate_call=bs.vote_skip_instant_replay,
        on_cancel_call=bs.vote_skip_instant_replay,
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

    # Vote tally, sitting just above the prompt exactly as the
    # tutorial stacks its own. Empty until somebody votes.
    global _g_vote_text  # pylint: disable=global-statement
    _g_vote_text = bui.textwidget(
        parent=_g_banner,
        position=(width * 0.5 - 300, 90),
        size=(600, 40),
        text='',
        h_align='center',
        v_align='center',
        color=(1.0, 1.0, 1.0, 0.9),
        scale=1.4,
        shadow=0.5,
        flatness=0.0,
    )

    # Skip prompt, styled after the tutorial's: bottom-centered, quiet,
    # and driven by any press rather than a button.
    bui.textwidget(
        parent=_g_banner,
        position=(width * 0.5 - 300, 50),
        size=(600, 40),
        text=_classicassets.strings.tutorial.to_skip_press_anything,
        h_align='center',
        v_align='center',
        color=(1.0, 1.0, 1.0, 0.7),
        scale=1.1,
        shadow=0.5,
        flatness=0.0,
    )


def set_skip_votes(count: int, total: int) -> None:
    """Show how many viewers have asked to skip, tutorial-style.

    Driven from the host's tally (locally and over the wire), so every
    viewer sees the same numbers.
    """
    import bauiv1 as bui
    from bauiv1 import _classicassets

    if _g_vote_text is None:
        return
    bui.textwidget(
        edit=_g_vote_text,
        text=(
            _classicassets.strings.tutorial.skip_vote_count(
                count=str(count), total=str(total)
            )
            if count > 0
            else ''
        ),
    )


def hide_banner() -> None:
    """Take the banner back down."""
    global _g_banner, _g_vote_text  # pylint: disable=global-statement

    import bauiv1 as bui

    if _g_banner is None:
        return
    bui.containerwidget(edit=_g_banner, transition='out_right')
    _g_banner = None
    _g_vote_text = None
