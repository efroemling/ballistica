# Released under the MIT License. See LICENSE for details.
#
# Auto-generated; do not edit by hand.
"""Asset-package wrapper for ``a-0.bauiv1assets.260831a`` (bauiv1).

Standard ui chrome the ui_v1 widget layer draws itself with -- window backings,
button faces, scroll furniture, the ui atlases. Supplied to ui_v1 by the active
app-mode (see bauiv1.UIAssetSet), so an app-mode can skin the ui by supplying
its own set instead. Free of any single game concepts; classic-specific art
belongs in BaClassicAssets.
"""

# ba_meta require api 9
# ba_meta require asset-package a-0.bauiv1assets.260831a

# pylint: disable=useless-suppression
# pylint: disable=too-many-lines
# pylint: disable=too-few-public-methods, disallowed-name

from typing import TYPE_CHECKING

from bauiv1._assetref import AssetGroup

_ASSET_PACKAGE = 'a-0.bauiv1assets.260831a'

if TYPE_CHECKING:
    from bauiv1._assetref import MeshHandle, SoundHandle, TextureHandle

    class AudioGroup:
        """
        ::

            Standard ui interaction sounds -- the widget-layer swishes and
            tickers an app-mode can reskin along with the chrome.

            See source for the full asset list.
        """

        score_increase: SoundHandle
        swish: SoundHandle
        swish2: SoundHandle
        swish3: SoundHandle

    class MeshesGroup:
        """
        ::

            Standard ui chrome meshes -- the backing geometry the widget layer
            stretches its chrome textures over.

            See source for the full asset list.
        """

        button_back_opaque: MeshHandle
        button_back_small_opaque: MeshHandle
        button_back_small_transparent: MeshHandle
        button_back_transparent: MeshHandle
        button_large_opaque: MeshHandle
        button_large_transparent: MeshHandle
        button_larger_opaque: MeshHandle
        button_larger_transparent: MeshHandle
        button_medium_opaque: MeshHandle
        button_medium_transparent: MeshHandle
        button_small_opaque: MeshHandle
        button_small_transparent: MeshHandle
        button_square_opaque: MeshHandle
        button_square_transparent: MeshHandle
        button_tab_opaque: MeshHandle
        button_tab_transparent: MeshHandle
        check_transparent: MeshHandle
        image1x1: MeshHandle
        scroll_bar_thumb_opaque: MeshHandle
        scroll_bar_thumb_short_opaque: MeshHandle
        scroll_bar_thumb_short_simple: MeshHandle
        scroll_bar_thumb_short_transparent: MeshHandle
        scroll_bar_thumb_simple: MeshHandle
        scroll_bar_thumb_transparent: MeshHandle
        scroll_bar_trough_transparent: MeshHandle
        soft_edge_inside: MeshHandle
        soft_edge_outside: MeshHandle
        text_box_transparent: MeshHandle
        window_hsmall_vmed_opaque: MeshHandle
        window_hsmall_vmed_transparent: MeshHandle
        window_hsmall_vsmall_opaque: MeshHandle
        window_hsmall_vsmall_transparent: MeshHandle

    class TexturesGroup:
        """
        ::

            Standard ui chrome textures -- window backings, button faces, scroll
            furniture, the ui atlases.

            See source for the full asset list.
        """

        back_icon: TextureHandle
        bomb_button: TextureHandle
        button_square: TextureHandle
        button_square_wide: TextureHandle
        circle: TextureHandle
        circle_soft: TextureHandle
        glow: TextureHandle
        menu_button: TextureHandle
        nub: TextureHandle
        page_left_right: TextureHandle
        scroll_widget: TextureHandle
        scroll_widget_glow: TextureHandle
        shadow_sharp: TextureHandle
        spinner: TextureHandle
        spinner0: TextureHandle
        spinner1: TextureHandle
        spinner10: TextureHandle
        spinner11: TextureHandle
        spinner2: TextureHandle
        spinner3: TextureHandle
        spinner4: TextureHandle
        spinner5: TextureHandle
        spinner6: TextureHandle
        spinner7: TextureHandle
        spinner8: TextureHandle
        spinner9: TextureHandle
        start_button: TextureHandle
        text_clear_button: TextureHandle
        ui_atlas: TextureHandle
        ui_atlas2: TextureHandle
        users_button: TextureHandle
        white: TextureHandle
        window_hsmall_vmed: TextureHandle
        window_hsmall_vsmall: TextureHandle

    #: The ``audio`` group - 4 assets (``score_increase``, ``swish``,
    #: ``swish2``, ``swish3``). Full list in source.
    audio: AudioGroup

    #: The ``meshes`` group - 32 assets (``button_back_opaque``,
    #: ``button_back_small_opaque``, ``button_back_small_transparent``,
    #: ``button_back_transparent``, ``button_large_opaque``, and 27 more). Full
    #: list in source.
    meshes: MeshesGroup

    #: The ``textures`` group - 34 assets (``back_icon``, ``bomb_button``,
    #: ``button_square``, ``button_square_wide``, ``circle``, and 29 more). Full
    #: list in source.
    textures: TexturesGroup

_TREE = {
    'audio': {
        'score_increase': 's',
        'swish': 's',
        'swish2': 's',
        'swish3': 's',
    },
    'meshes': {
        'button_back_opaque': 'm',
        'button_back_small_opaque': 'm',
        'button_back_small_transparent': 'm',
        'button_back_transparent': 'm',
        'button_large_opaque': 'm',
        'button_large_transparent': 'm',
        'button_larger_opaque': 'm',
        'button_larger_transparent': 'm',
        'button_medium_opaque': 'm',
        'button_medium_transparent': 'm',
        'button_small_opaque': 'm',
        'button_small_transparent': 'm',
        'button_square_opaque': 'm',
        'button_square_transparent': 'm',
        'button_tab_opaque': 'm',
        'button_tab_transparent': 'm',
        'check_transparent': 'm',
        'image1x1': 'm',
        'scroll_bar_thumb_opaque': 'm',
        'scroll_bar_thumb_short_opaque': 'm',
        'scroll_bar_thumb_short_simple': 'm',
        'scroll_bar_thumb_short_transparent': 'm',
        'scroll_bar_thumb_simple': 'm',
        'scroll_bar_thumb_transparent': 'm',
        'scroll_bar_trough_transparent': 'm',
        'soft_edge_inside': 'm',
        'soft_edge_outside': 'm',
        'text_box_transparent': 'm',
        'window_hsmall_vmed_opaque': 'm',
        'window_hsmall_vmed_transparent': 'm',
        'window_hsmall_vsmall_opaque': 'm',
        'window_hsmall_vsmall_transparent': 'm',
    },
    'textures': {
        'back_icon': 't',
        'bomb_button': 't',
        'button_square': 't',
        'button_square_wide': 't',
        'circle': 't',
        'circle_soft': 't',
        'glow': 't',
        'menu_button': 't',
        'nub': 't',
        'page_left_right': 't',
        'scroll_widget': 't',
        'scroll_widget_glow': 't',
        'shadow_sharp': 't',
        'spinner': 't',
        'spinner0': 't',
        'spinner1': 't',
        'spinner10': 't',
        'spinner11': 't',
        'spinner2': 't',
        'spinner3': 't',
        'spinner4': 't',
        'spinner5': 't',
        'spinner6': 't',
        'spinner7': 't',
        'spinner8': 't',
        'spinner9': 't',
        'start_button': 't',
        'text_clear_button': 't',
        'ui_atlas': 't',
        'ui_atlas2': 't',
        'users_button': 't',
        'white': 't',
        'window_hsmall_vmed': 't',
        'window_hsmall_vsmall': 't',
    },
}


if not TYPE_CHECKING:
    audio = AssetGroup(_ASSET_PACKAGE, _TREE['audio'], 'audio')
    meshes = AssetGroup(_ASSET_PACKAGE, _TREE['meshes'], 'meshes')
    textures = AssetGroup(_ASSET_PACKAGE, _TREE['textures'], 'textures')
