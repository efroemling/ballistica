# Released under the MIT License. See LICENSE for details.
#
"""Functionality related to classic game tips.

These can be shown at opportune times such as between rounds."""

from typing import TYPE_CHECKING

import babase
from babase import _builtinassets

if TYPE_CHECKING:
    pass


def get_all_tips() -> list[babase.LangStr]:
    """Return the complete list of tips.

    Tips are authored strings (``_classicassets.strings.tips``) rather
    than English text run through the legacy translate path, so they
    re-render on a language change like everything else. Which tips
    apply still depends on the platform.
    """
    # Safe up-call: bascenev1 is fully imported by the time a tip can
    # be shown; the cycle pylint sees is structural only. (baclassic
    # has no wrapper of its own -- its modules pull _classicassets from
    # bascenev1, same as _achievement.py.)
    # pylint: disable-next=cyclic-import
    from bascenev1 import _classicassets

    t = _classicassets.strings.tips
    app = babase.app

    tips: list[babase.LangStr] = [
        t.remote_app(remote_app_name=_builtinassets.strings.ui.remote_app_name),
        t.create_profiles,
        t.aim_punches,
        t.curse_health_powerup,
        t.spin_punch_respect,
        t.floss,
        t.dont_always_run,
        t.ctf_own_flag,
        t.sticky_bomb_dance,
        t.whack_head,
        t.one_hit_double_points,
        t.characters_identical,
        t.jump_before_throw,
        t.throw_strength_direction,
        t.punch_to_escape,
        t.shield_overconfidence,
        t.throw_players,
        t.ice_bombs,
        t.dont_overspin,
        t.whiplash_throw,
        t.fast_fists,
        t.hockey_turn_gradually,
        t.sticky_to_head,
        t.run_watch_cliffs,
        t.fuse_colors,
        t.reduce_visuals_framerate,
    ]

    if (
        app.classic is not None
        and app.classic.platform in ('android', 'ios')
        and not app.env.tv
    ):
        tips.append(t.reduce_visuals_heat)

    if app.classic is not None and app.classic.platform in ['mac', 'android']:
        tips.append(t.custom_soundtrack)

    # Hot-plugging is currently only on some platforms.
    # FIXME: Should add a platform entry for this so don't forget to update it.
    if app.classic is not None and app.classic.platform in [
        'mac',
        'android',
        'windows',
    ]:
        tips.append(t.join_leave_anytime)

    return tips
