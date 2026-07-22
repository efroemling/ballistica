# Released under the MIT License. See LICENSE for details.
#
# Auto-generated; do not edit by hand.
"""Asset-package wrapper for ``a-0.babuiltinassets.260721a`` (bascenev1).

Bare minimum assets always bundled with the engine.

These are loaded at launch and always available in the C++ layer.
"""

# ba_meta require api 9
# ba_meta require asset-package a-0.babuiltinassets.260721a

# pylint: disable=useless-suppression
# pylint: disable=too-many-lines
# pylint: disable=too-few-public-methods, disallowed-name

__asset_package__ = 'a-0.babuiltinassets.260721a'

from typing import TYPE_CHECKING

from bascenev1._assetwrap import AssetDir

if TYPE_CHECKING:
    import bascenev1

    class AudioGroup:
        """
        Sounds needed during engine bootstrap and early UI (clicks, errors, and
        other always-available effects).

        See source for the full asset list.
        """

        blank: bascenev1.Sound
        blip: bascenev1.Sound
        cash_register: bascenev1.Sound
        click01: bascenev1.Sound
        cork_pop: bascenev1.Sound
        deek: bascenev1.Sound
        ding: bascenev1.Sound
        error: bascenev1.Sound
        gun_cocking: bascenev1.Sound
        powerdown01: bascenev1.Sound
        punch01: bascenev1.Sound
        score_increase: bascenev1.Sound
        sparkle01: bascenev1.Sound
        sparkle02: bascenev1.Sound
        sparkle03: bascenev1.Sound
        swish: bascenev1.Sound
        swish2: bascenev1.Sound
        swish3: bascenev1.Sound
        tap: bascenev1.Sound
        ticking_crazy: bascenev1.Sound

    class MeshesGroup:
        """
        Meshes needed during engine bootstrap and early UI.

        See source for the full asset list.
        """

        action_button_bottom: bascenev1.Mesh
        action_button_left: bascenev1.Mesh
        action_button_right: bascenev1.Mesh
        action_button_top: bascenev1.Mesh
        arrow_back: bascenev1.Mesh
        arrow_front: bascenev1.Mesh
        box: bascenev1.Mesh
        boxing_glove: bascenev1.Mesh
        button_back_opaque: bascenev1.Mesh
        button_back_small_opaque: bascenev1.Mesh
        button_back_small_transparent: bascenev1.Mesh
        button_back_transparent: bascenev1.Mesh
        button_large_opaque: bascenev1.Mesh
        button_large_transparent: bascenev1.Mesh
        button_larger_opaque: bascenev1.Mesh
        button_larger_transparent: bascenev1.Mesh
        button_medium_opaque: bascenev1.Mesh
        button_medium_transparent: bascenev1.Mesh
        button_small_opaque: bascenev1.Mesh
        button_small_transparent: bascenev1.Mesh
        button_square_opaque: bascenev1.Mesh
        button_square_transparent: bascenev1.Mesh
        button_tab_opaque: bascenev1.Mesh
        button_tab_transparent: bascenev1.Mesh
        check_transparent: bascenev1.Mesh
        cross_out: bascenev1.Mesh
        cylinder: bascenev1.Mesh
        eye_ball: bascenev1.Mesh
        eye_ball_iris: bascenev1.Mesh
        eye_lid: bascenev1.Mesh
        flag_pole: bascenev1.Mesh
        flag_stand: bascenev1.Mesh
        flash: bascenev1.Mesh
        hair_tuft1: bascenev1.Mesh
        hair_tuft1b: bascenev1.Mesh
        hair_tuft2: bascenev1.Mesh
        hair_tuft3: bascenev1.Mesh
        hair_tuft4: bascenev1.Mesh
        image16x1: bascenev1.Mesh
        image1x1: bascenev1.Mesh
        image1x1_full_screen: bascenev1.Mesh
        image1x1_vrfull_screen: bascenev1.Mesh
        image2x1: bascenev1.Mesh
        image4x1: bascenev1.Mesh
        locator: bascenev1.Mesh
        locator_box: bascenev1.Mesh
        locator_circle: bascenev1.Mesh
        locator_circle_outline: bascenev1.Mesh
        overlay_guide: bascenev1.Mesh
        scorch: bascenev1.Mesh
        scroll_bar_thumb_opaque: bascenev1.Mesh
        scroll_bar_thumb_short_opaque: bascenev1.Mesh
        scroll_bar_thumb_short_simple: bascenev1.Mesh
        scroll_bar_thumb_short_transparent: bascenev1.Mesh
        scroll_bar_thumb_simple: bascenev1.Mesh
        scroll_bar_thumb_transparent: bascenev1.Mesh
        scroll_bar_trough_transparent: bascenev1.Mesh
        shield: bascenev1.Mesh
        shock_wave: bascenev1.Mesh
        shrapnel1: bascenev1.Mesh
        shrapnel_board: bascenev1.Mesh
        shrapnel_slime: bascenev1.Mesh
        soft_edge_inside: bascenev1.Mesh
        soft_edge_outside: bascenev1.Mesh
        text_box_transparent: bascenev1.Mesh
        vr_fade: bascenev1.Mesh
        vr_overlay: bascenev1.Mesh
        window_hsmall_vmed_opaque: bascenev1.Mesh
        window_hsmall_vmed_transparent: bascenev1.Mesh
        window_hsmall_vsmall_opaque: bascenev1.Mesh
        window_hsmall_vsmall_transparent: bascenev1.Mesh
        wing: bascenev1.Mesh

    class TexturesGroup:
        """
        Textures needed during engine bootstrap and early UI, including the
        reflection cube-maps.

        See source for the full asset list.
        """

        action_buttons: bascenev1.Texture
        arrow: bascenev1.Texture
        back_icon: bascenev1.Texture
        black: bascenev1.Texture
        bomb_button: bascenev1.Texture
        boxing_gloves_color: bascenev1.Texture
        button_square: bascenev1.Texture
        button_square_wide: bascenev1.Texture
        character_icon_mask: bascenev1.Texture
        circle: bascenev1.Texture
        circle_no_alpha: bascenev1.Texture
        circle_outline: bascenev1.Texture
        circle_outline_no_alpha: bascenev1.Texture
        circle_shadow: bascenev1.Texture
        circle_soft: bascenev1.Texture
        cursor: bascenev1.Texture
        explosion: bascenev1.Texture
        eye_color: bascenev1.Texture
        eye_color_tint_mask: bascenev1.Texture
        flag_pole_color: bascenev1.Texture
        font_big: bascenev1.Texture
        font_extras: bascenev1.Texture
        font_extras2: bascenev1.Texture
        font_extras3: bascenev1.Texture
        font_extras4: bascenev1.Texture
        font_extras5: bascenev1.Texture
        font_small0: bascenev1.Texture
        font_small1: bascenev1.Texture
        font_small2: bascenev1.Texture
        font_small3: bascenev1.Texture
        font_small4: bascenev1.Texture
        font_small5: bascenev1.Texture
        font_small6: bascenev1.Texture
        font_small7: bascenev1.Texture
        fuse: bascenev1.Texture
        glow: bascenev1.Texture
        light: bascenev1.Texture
        light_sharp: bascenev1.Texture
        light_soft: bascenev1.Texture
        menu_button: bascenev1.Texture
        nub: bascenev1.Texture
        ouya_abutton: bascenev1.Texture
        page_left_right: bascenev1.Texture
        rgb_stripes: bascenev1.Texture
        scorch: bascenev1.Texture
        scorch_big: bascenev1.Texture
        scroll_widget: bascenev1.Texture
        scroll_widget_glow: bascenev1.Texture
        shadow: bascenev1.Texture
        shadow_sharp: bascenev1.Texture
        shadow_soft: bascenev1.Texture
        shield: bascenev1.Texture
        shrapnel1_color: bascenev1.Texture
        smoke: bascenev1.Texture
        soft_rect: bascenev1.Texture
        soft_rect2: bascenev1.Texture
        soft_rect_vertical: bascenev1.Texture
        sparks: bascenev1.Texture
        spinner: bascenev1.Texture
        spinner0: bascenev1.Texture
        spinner1: bascenev1.Texture
        spinner10: bascenev1.Texture
        spinner11: bascenev1.Texture
        spinner2: bascenev1.Texture
        spinner3: bascenev1.Texture
        spinner4: bascenev1.Texture
        spinner5: bascenev1.Texture
        spinner6: bascenev1.Texture
        spinner7: bascenev1.Texture
        spinner8: bascenev1.Texture
        spinner9: bascenev1.Texture
        start_button: bascenev1.Texture
        text_clear_button: bascenev1.Texture
        touch_arrows: bascenev1.Texture
        touch_arrows_actions: bascenev1.Texture
        ui_atlas: bascenev1.Texture
        ui_atlas2: bascenev1.Texture
        users_button: bascenev1.Texture
        white: bascenev1.Texture
        window_hsmall_vmed: bascenev1.Texture
        window_hsmall_vsmall: bascenev1.Texture
        wings: bascenev1.Texture

    #: The ``audio`` group - 20 assets (``blank``, ``blip``, ``cash_register``,
    #: ``click01``, ``cork_pop``, and 15 more). Full list in source.
    audio: AudioGroup

    #: The ``meshes`` group - 72 assets (``action_button_bottom``,
    #: ``action_button_left``, ``action_button_right``, ``action_button_top``,
    #: ``arrow_back``, and 67 more). Full list in source.
    meshes: MeshesGroup

    #: The ``textures`` group - 82 assets (``action_buttons``, ``arrow``,
    #: ``back_icon``, ``black``, ``bomb_button``, and 77 more). Full list in
    #: source.
    textures: TexturesGroup

_TREE = {
    'audio': {
        'blank': 's',
        'blip': 's',
        'cash_register': 's',
        'click01': 's',
        'cork_pop': 's',
        'deek': 's',
        'ding': 's',
        'error': 's',
        'gun_cocking': 's',
        'powerdown01': 's',
        'punch01': 's',
        'score_increase': 's',
        'sparkle01': 's',
        'sparkle02': 's',
        'sparkle03': 's',
        'swish': 's',
        'swish2': 's',
        'swish3': 's',
        'tap': 's',
        'ticking_crazy': 's',
    },
    'meshes': {
        'action_button_bottom': 'm',
        'action_button_left': 'm',
        'action_button_right': 'm',
        'action_button_top': 'm',
        'arrow_back': 'm',
        'arrow_front': 'm',
        'box': 'm',
        'boxing_glove': 'm',
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
        'cross_out': 'm',
        'cylinder': 'm',
        'eye_ball': 'm',
        'eye_ball_iris': 'm',
        'eye_lid': 'm',
        'flag_pole': 'm',
        'flag_stand': 'm',
        'flash': 'm',
        'hair_tuft1': 'm',
        'hair_tuft1b': 'm',
        'hair_tuft2': 'm',
        'hair_tuft3': 'm',
        'hair_tuft4': 'm',
        'image16x1': 'm',
        'image1x1': 'm',
        'image1x1_full_screen': 'm',
        'image1x1_vrfull_screen': 'm',
        'image2x1': 'm',
        'image4x1': 'm',
        'locator': 'm',
        'locator_box': 'm',
        'locator_circle': 'm',
        'locator_circle_outline': 'm',
        'overlay_guide': 'm',
        'scorch': 'm',
        'scroll_bar_thumb_opaque': 'm',
        'scroll_bar_thumb_short_opaque': 'm',
        'scroll_bar_thumb_short_simple': 'm',
        'scroll_bar_thumb_short_transparent': 'm',
        'scroll_bar_thumb_simple': 'm',
        'scroll_bar_thumb_transparent': 'm',
        'scroll_bar_trough_transparent': 'm',
        'shield': 'm',
        'shock_wave': 'm',
        'shrapnel1': 'm',
        'shrapnel_board': 'm',
        'shrapnel_slime': 'm',
        'soft_edge_inside': 'm',
        'soft_edge_outside': 'm',
        'text_box_transparent': 'm',
        'vr_fade': 'm',
        'vr_overlay': 'm',
        'window_hsmall_vmed_opaque': 'm',
        'window_hsmall_vmed_transparent': 'm',
        'window_hsmall_vsmall_opaque': 'm',
        'window_hsmall_vsmall_transparent': 'm',
        'wing': 'm',
    },
    'textures': {
        'action_buttons': 't',
        'arrow': 't',
        'back_icon': 't',
        'black': 't',
        'bomb_button': 't',
        'boxing_gloves_color': 't',
        'button_square': 't',
        'button_square_wide': 't',
        'character_icon_mask': 't',
        'circle': 't',
        'circle_no_alpha': 't',
        'circle_outline': 't',
        'circle_outline_no_alpha': 't',
        'circle_shadow': 't',
        'circle_soft': 't',
        'cursor': 't',
        'explosion': 't',
        'eye_color': 't',
        'eye_color_tint_mask': 't',
        'flag_pole_color': 't',
        'font_big': 't',
        'font_extras': 't',
        'font_extras2': 't',
        'font_extras3': 't',
        'font_extras4': 't',
        'font_extras5': 't',
        'font_small0': 't',
        'font_small1': 't',
        'font_small2': 't',
        'font_small3': 't',
        'font_small4': 't',
        'font_small5': 't',
        'font_small6': 't',
        'font_small7': 't',
        'fuse': 't',
        'glow': 't',
        'light': 't',
        'light_sharp': 't',
        'light_soft': 't',
        'menu_button': 't',
        'nub': 't',
        'ouya_abutton': 't',
        'page_left_right': 't',
        'rgb_stripes': 't',
        'scorch': 't',
        'scorch_big': 't',
        'scroll_widget': 't',
        'scroll_widget_glow': 't',
        'shadow': 't',
        'shadow_sharp': 't',
        'shadow_soft': 't',
        'shield': 't',
        'shrapnel1_color': 't',
        'smoke': 't',
        'soft_rect': 't',
        'soft_rect2': 't',
        'soft_rect_vertical': 't',
        'sparks': 't',
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
        'touch_arrows': 't',
        'touch_arrows_actions': 't',
        'ui_atlas': 't',
        'ui_atlas2': 't',
        'users_button': 't',
        'white': 't',
        'window_hsmall_vmed': 't',
        'window_hsmall_vsmall': 't',
        'wings': 't',
    },
}


if not TYPE_CHECKING:
    audio = AssetDir(__asset_package__, _TREE['audio'], 'audio')
    meshes = AssetDir(__asset_package__, _TREE['meshes'], 'meshes')
    textures = AssetDir(__asset_package__, _TREE['textures'], 'textures')
