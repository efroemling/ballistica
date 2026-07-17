# Released under the MIT License. See LICENSE for details.
#
# Auto-generated; do not edit by hand.
"""Asset-package wrapper for ``a-0.babuiltinassets.260715`` (bauiv1).

Bare minimum assets always bundled with the engine.

These are loaded at launch and always available in the C++ layer.
"""

# ba_meta require api 9
# ba_meta require asset-package a-0.babuiltinassets.260715

# pylint: disable=useless-suppression
# pylint: disable=too-many-lines
# pylint: disable=too-few-public-methods, disallowed-name

__asset_package__ = 'a-0.babuiltinassets.260715'

from typing import TYPE_CHECKING

from bauiv1._assetref import AssetRefDir

if TYPE_CHECKING:
    from bauiv1._assetref import MeshRef, SoundRef, TextureRef

    class AudioGroup:
        """
        Sounds needed during engine bootstrap and early UI (clicks, errors, and
        other always-available effects).

        See source for the full asset list.
        """

        blank: SoundRef
        blip: SoundRef
        cash_register: SoundRef
        click01: SoundRef
        cork_pop: SoundRef
        deek: SoundRef
        ding: SoundRef
        error: SoundRef
        gun_cocking: SoundRef
        powerdown01: SoundRef
        punch01: SoundRef
        score_increase: SoundRef
        sparkle01: SoundRef
        sparkle02: SoundRef
        sparkle03: SoundRef
        swish: SoundRef
        swish2: SoundRef
        swish3: SoundRef
        tap: SoundRef
        ticking_crazy: SoundRef

    class MeshesGroup:
        """
        Meshes needed during engine bootstrap and early UI.

        See source for the full asset list.
        """

        action_button_bottom: MeshRef
        action_button_left: MeshRef
        action_button_right: MeshRef
        action_button_top: MeshRef
        arrow_back: MeshRef
        arrow_front: MeshRef
        box: MeshRef
        boxing_glove: MeshRef
        button_back_opaque: MeshRef
        button_back_small_opaque: MeshRef
        button_back_small_transparent: MeshRef
        button_back_transparent: MeshRef
        button_large_opaque: MeshRef
        button_large_transparent: MeshRef
        button_larger_opaque: MeshRef
        button_larger_transparent: MeshRef
        button_medium_opaque: MeshRef
        button_medium_transparent: MeshRef
        button_small_opaque: MeshRef
        button_small_transparent: MeshRef
        button_square_opaque: MeshRef
        button_square_transparent: MeshRef
        button_tab_opaque: MeshRef
        button_tab_transparent: MeshRef
        check_transparent: MeshRef
        cross_out: MeshRef
        cylinder: MeshRef
        eye_ball: MeshRef
        eye_ball_iris: MeshRef
        eye_lid: MeshRef
        flag_pole: MeshRef
        flag_stand: MeshRef
        flash: MeshRef
        hair_tuft1: MeshRef
        hair_tuft1b: MeshRef
        hair_tuft2: MeshRef
        hair_tuft3: MeshRef
        hair_tuft4: MeshRef
        image16x1: MeshRef
        image1x1: MeshRef
        image1x1_full_screen: MeshRef
        image1x1_vrfull_screen: MeshRef
        image2x1: MeshRef
        image4x1: MeshRef
        locator: MeshRef
        locator_box: MeshRef
        locator_circle: MeshRef
        locator_circle_outline: MeshRef
        overlay_guide: MeshRef
        scorch: MeshRef
        scroll_bar_thumb_opaque: MeshRef
        scroll_bar_thumb_short_opaque: MeshRef
        scroll_bar_thumb_short_simple: MeshRef
        scroll_bar_thumb_short_transparent: MeshRef
        scroll_bar_thumb_simple: MeshRef
        scroll_bar_thumb_transparent: MeshRef
        scroll_bar_trough_transparent: MeshRef
        shield: MeshRef
        shock_wave: MeshRef
        shrapnel1: MeshRef
        shrapnel_board: MeshRef
        shrapnel_slime: MeshRef
        soft_edge_inside: MeshRef
        soft_edge_outside: MeshRef
        text_box_transparent: MeshRef
        vr_fade: MeshRef
        vr_overlay: MeshRef
        window_hsmall_vmed_opaque: MeshRef
        window_hsmall_vmed_transparent: MeshRef
        window_hsmall_vsmall_opaque: MeshRef
        window_hsmall_vsmall_transparent: MeshRef
        wing: MeshRef

    class TexturesGroup:
        """
        Textures needed during engine bootstrap and early UI, including the
        reflection cube-maps.

        See source for the full asset list.
        """

        action_buttons: TextureRef
        arrow: TextureRef
        back_icon: TextureRef
        black: TextureRef
        bomb_button: TextureRef
        boxing_gloves_color: TextureRef
        button_square: TextureRef
        button_square_wide: TextureRef
        character_icon_mask: TextureRef
        circle: TextureRef
        circle_no_alpha: TextureRef
        circle_outline: TextureRef
        circle_outline_no_alpha: TextureRef
        circle_shadow: TextureRef
        circle_soft: TextureRef
        cursor: TextureRef
        explosion: TextureRef
        eye_color: TextureRef
        eye_color_tint_mask: TextureRef
        flag_pole_color: TextureRef
        font_big: TextureRef
        font_extras: TextureRef
        font_extras2: TextureRef
        font_extras3: TextureRef
        font_extras4: TextureRef
        font_extras5: TextureRef
        font_small0: TextureRef
        font_small1: TextureRef
        font_small2: TextureRef
        font_small3: TextureRef
        font_small4: TextureRef
        font_small5: TextureRef
        font_small6: TextureRef
        font_small7: TextureRef
        fuse: TextureRef
        glow: TextureRef
        light: TextureRef
        light_sharp: TextureRef
        light_soft: TextureRef
        menu_button: TextureRef
        nub: TextureRef
        ouya_abutton: TextureRef
        page_left_right: TextureRef
        rgb_stripes: TextureRef
        scorch: TextureRef
        scorch_big: TextureRef
        scroll_widget: TextureRef
        scroll_widget_glow: TextureRef
        shadow: TextureRef
        shadow_sharp: TextureRef
        shadow_soft: TextureRef
        shield: TextureRef
        shrapnel1_color: TextureRef
        smoke: TextureRef
        soft_rect: TextureRef
        soft_rect2: TextureRef
        soft_rect_vertical: TextureRef
        sparks: TextureRef
        spinner: TextureRef
        spinner0: TextureRef
        spinner1: TextureRef
        spinner10: TextureRef
        spinner11: TextureRef
        spinner2: TextureRef
        spinner3: TextureRef
        spinner4: TextureRef
        spinner5: TextureRef
        spinner6: TextureRef
        spinner7: TextureRef
        spinner8: TextureRef
        spinner9: TextureRef
        start_button: TextureRef
        text_clear_button: TextureRef
        touch_arrows: TextureRef
        touch_arrows_actions: TextureRef
        ui_atlas: TextureRef
        ui_atlas2: TextureRef
        users_button: TextureRef
        white: TextureRef
        window_hsmall_vmed: TextureRef
        window_hsmall_vsmall: TextureRef
        wings: TextureRef

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
    audio = AssetRefDir(__asset_package__, _TREE['audio'], 'audio')
    meshes = AssetRefDir(__asset_package__, _TREE['meshes'], 'meshes')
    textures = AssetRefDir(__asset_package__, _TREE['textures'], 'textures')
