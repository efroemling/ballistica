# Released under the MIT License. See LICENSE for details.
#
"""The base asset set classic hands to the engine."""

import babase
from bascenev1 import _builtinassets
from bascenev1 import _classicassets


def make_base_asset_set() -> babase.BaseAssetSet:
    """Build the art classic supplies for base's classic-flavored draws.

    Every slot of :class:`babase.BaseAssetSet` starts at a neutral
    builtin placeholder; this names classic's real art for all of them.
    Slots hold handles, so nothing loads here -- loading happens when
    the set is applied at activation.
    """
    tex = _classicassets.textures
    msh = _classicassets.meshes
    assets = babase.BaseAssetSet()

    # Reflections.
    assets.reflection_char = tex.reflection_char
    assets.reflection_powerup = tex.reflection_powerup
    assets.reflection_soft = tex.reflection_soft
    assets.reflection_sharp = tex.reflection_sharp
    assets.reflection_sharper = tex.reflection_sharper
    assets.reflection_sharpest = tex.reflection_sharpest

    # Effects.
    assets.smoke = tex.smoke
    assets.sparks = tex.sparks
    assets.fuse = tex.fuse
    assets.shrapnel_rock_color = tex.shrapnel1_color
    assets.shrapnel_rock = msh.shrapnel1
    assets.shrapnel_board = msh.shrapnel_board
    assets.shrapnel_slime = msh.shrapnel_slime

    # Props.
    assets.flag_pole_color = tex.flag_pole_color
    assets.flag_stand = msh.flag_stand
    assets.boxing_glove = msh.boxing_glove
    assets.boxing_gloves_color = tex.boxing_gloves_color
    assets.character_icon_mask = tex.character_icon_mask

    # More effects.
    assets.light = tex.light
    assets.light_soft = tex.light_soft

    # Touch controls.
    assets.action_buttons = tex.action_buttons
    assets.touch_arrows = tex.touch_arrows
    assets.touch_arrows_actions = tex.touch_arrows_actions
    assets.arrow = tex.arrow
    assets.action_button_bottom = msh.action_button_bottom
    assets.action_button_left = msh.action_button_left
    assets.action_button_right = msh.action_button_right
    assets.action_button_top = msh.action_button_top
    assets.arrow_back = msh.arrow_back
    assets.arrow_front = msh.arrow_front

    # Jingles. cork_pop's art is ours now; gun_cocking's wav is
    # babase-python-pinned so it stays in the builtin package and we
    # simply point our slot at it there.
    assets.cork_pop = _classicassets.audio.cork_pop
    assets.gun_cocking = _builtinassets.audio.gun_cocking

    return assets
