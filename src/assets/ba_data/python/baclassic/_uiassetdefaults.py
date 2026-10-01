# Released under the MIT License. See LICENSE for details.
#
"""The ui assets classic hands to ui_v1."""

import bauiv1 as bui
from bauiv1 import _classicassets, _classiccatalogassets, _uiv1assets


def make_ui_asset_set() -> bui.UIAssetSet:
    """Build the set of art classic wants the ui layer drawn with.

    Only the toolbar plus the few chrome slots ui_v1 has no art of its
    own for (the sprite atlas, the nub, the swish) are named here.
    ui_v1 has its own art for everything else and the set starts out
    at it, so this lists exactly what classic contributes and nothing
    more -- reassign any other slot on the returned set to restyle
    ui_v1's own furniture too.

    Note that ui_v1 neither knows nor cares which asset-package a slot
    came from; picking packages is this function's job, and moving an
    asset between them changes only the line below that names it.

    Cheap to call: slots hold asset *handles*, so nothing loads
    here -- loading happens when the set is applied at activation,
    and only for the slots that survive config amendment.
    """
    tex = _classicassets.textures
    uitex = _uiv1assets.textures
    cattex = _classiccatalogassets.textures
    msh = _classicassets.meshes
    snd = _classicassets.audio
    return bui.UIAssetSet(
        ui_atlas=uitex.ui_atlas,
        nub=tex.nub,
        swish=snd.swish,
        level_icon=tex.level_icon,
        trophy=tex.trophy,
        chest_icon_empty=tex.chest_icon_empty,
        log_icon=tex.log_icon,
        leaderboards_icon=tex.leaderboards_icon,
        inventory_icon=tex.inventory_icon,
        store_icon=tex.store_icon,
        store_character_xmas=tex.store_character_xmas,
        currency_meter=msh.currency_meter,
        currency_plus_button=msh.currency_plus_button,
        toolbar_backing_top2=msh.toolbar_backing_top2,
        toolbar_backing_bottom2=msh.toolbar_backing_bottom2,
        coin=cattex.coin,
        tickets=cattex.tickets,
        lock=tex.lock,
        tv=tex.tv,
        achievements_icon=tex.achievements_icon,
        settings_icon=tex.settings_icon,
    )
