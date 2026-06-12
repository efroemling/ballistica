# Released under the MIT License. See LICENSE for details.
#
"""Asset-package wrapper for ``a-0.babuiltinassets.260612`` (bascenev1).

Auto-generated; do not edit by hand.
"""

# ba_meta require asset-package a-0.babuiltinassets.260612
# pylint: disable=missing-function-docstring
# pylint: disable=too-many-public-methods, useless-suppression
# pylint: disable=too-many-lines, disallowed-name

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import bascenev1

__asset_package__ = 'a-0.babuiltinassets.260612'
_APVERID = __asset_package__


class _Audio:
    @property
    def blank(self) -> bascenev1.Sound:
        import bascenev1

        return bascenev1.getsound(f'{_APVERID}:audio/blank')

    @property
    def blip(self) -> bascenev1.Sound:
        import bascenev1

        return bascenev1.getsound(f'{_APVERID}:audio/blip')

    @property
    def cash_register(self) -> bascenev1.Sound:
        import bascenev1

        return bascenev1.getsound(f'{_APVERID}:audio/cash_register')

    @property
    def click01(self) -> bascenev1.Sound:
        import bascenev1

        return bascenev1.getsound(f'{_APVERID}:audio/click01')

    @property
    def cork_pop(self) -> bascenev1.Sound:
        import bascenev1

        return bascenev1.getsound(f'{_APVERID}:audio/cork_pop')

    @property
    def deek(self) -> bascenev1.Sound:
        import bascenev1

        return bascenev1.getsound(f'{_APVERID}:audio/deek')

    @property
    def ding(self) -> bascenev1.Sound:
        import bascenev1

        return bascenev1.getsound(f'{_APVERID}:audio/ding')

    @property
    def error(self) -> bascenev1.Sound:
        import bascenev1

        return bascenev1.getsound(f'{_APVERID}:audio/error')

    @property
    def gun_cocking(self) -> bascenev1.Sound:
        import bascenev1

        return bascenev1.getsound(f'{_APVERID}:audio/gun_cocking')

    @property
    def powerdown01(self) -> bascenev1.Sound:
        import bascenev1

        return bascenev1.getsound(f'{_APVERID}:audio/powerdown01')

    @property
    def punch01(self) -> bascenev1.Sound:
        import bascenev1

        return bascenev1.getsound(f'{_APVERID}:audio/punch01')

    @property
    def score_increase(self) -> bascenev1.Sound:
        import bascenev1

        return bascenev1.getsound(f'{_APVERID}:audio/score_increase')

    @property
    def sparkle01(self) -> bascenev1.Sound:
        import bascenev1

        return bascenev1.getsound(f'{_APVERID}:audio/sparkle01')

    @property
    def sparkle02(self) -> bascenev1.Sound:
        import bascenev1

        return bascenev1.getsound(f'{_APVERID}:audio/sparkle02')

    @property
    def sparkle03(self) -> bascenev1.Sound:
        import bascenev1

        return bascenev1.getsound(f'{_APVERID}:audio/sparkle03')

    @property
    def swish(self) -> bascenev1.Sound:
        import bascenev1

        return bascenev1.getsound(f'{_APVERID}:audio/swish')

    @property
    def swish2(self) -> bascenev1.Sound:
        import bascenev1

        return bascenev1.getsound(f'{_APVERID}:audio/swish2')

    @property
    def swish3(self) -> bascenev1.Sound:
        import bascenev1

        return bascenev1.getsound(f'{_APVERID}:audio/swish3')

    @property
    def tap(self) -> bascenev1.Sound:
        import bascenev1

        return bascenev1.getsound(f'{_APVERID}:audio/tap')

    @property
    def ticking_crazy(self) -> bascenev1.Sound:
        import bascenev1

        return bascenev1.getsound(f'{_APVERID}:audio/ticking_crazy')


audio = _Audio()


class _Meshes:
    @property
    def action_button_bottom(self) -> bascenev1.Mesh:
        import bascenev1

        return bascenev1.getmesh(f'{_APVERID}:meshes/action_button_bottom')

    @property
    def action_button_left(self) -> bascenev1.Mesh:
        import bascenev1

        return bascenev1.getmesh(f'{_APVERID}:meshes/action_button_left')

    @property
    def action_button_right(self) -> bascenev1.Mesh:
        import bascenev1

        return bascenev1.getmesh(f'{_APVERID}:meshes/action_button_right')

    @property
    def action_button_top(self) -> bascenev1.Mesh:
        import bascenev1

        return bascenev1.getmesh(f'{_APVERID}:meshes/action_button_top')

    @property
    def arrow_back(self) -> bascenev1.Mesh:
        import bascenev1

        return bascenev1.getmesh(f'{_APVERID}:meshes/arrow_back')

    @property
    def arrow_front(self) -> bascenev1.Mesh:
        import bascenev1

        return bascenev1.getmesh(f'{_APVERID}:meshes/arrow_front')

    @property
    def box(self) -> bascenev1.Mesh:
        import bascenev1

        return bascenev1.getmesh(f'{_APVERID}:meshes/box')

    @property
    def boxing_glove(self) -> bascenev1.Mesh:
        import bascenev1

        return bascenev1.getmesh(f'{_APVERID}:meshes/boxing_glove')

    @property
    def button_back_opaque(self) -> bascenev1.Mesh:
        import bascenev1

        return bascenev1.getmesh(f'{_APVERID}:meshes/button_back_opaque')

    @property
    def button_back_small_opaque(self) -> bascenev1.Mesh:
        import bascenev1

        return bascenev1.getmesh(f'{_APVERID}:meshes/button_back_small_opaque')

    @property
    def button_back_small_transparent(self) -> bascenev1.Mesh:
        import bascenev1

        return bascenev1.getmesh(
            f'{_APVERID}:meshes/button_back_small_transparent'
        )

    @property
    def button_back_transparent(self) -> bascenev1.Mesh:
        import bascenev1

        return bascenev1.getmesh(f'{_APVERID}:meshes/button_back_transparent')

    @property
    def button_large_opaque(self) -> bascenev1.Mesh:
        import bascenev1

        return bascenev1.getmesh(f'{_APVERID}:meshes/button_large_opaque')

    @property
    def button_large_transparent(self) -> bascenev1.Mesh:
        import bascenev1

        return bascenev1.getmesh(f'{_APVERID}:meshes/button_large_transparent')

    @property
    def button_larger_opaque(self) -> bascenev1.Mesh:
        import bascenev1

        return bascenev1.getmesh(f'{_APVERID}:meshes/button_larger_opaque')

    @property
    def button_larger_transparent(self) -> bascenev1.Mesh:
        import bascenev1

        return bascenev1.getmesh(f'{_APVERID}:meshes/button_larger_transparent')

    @property
    def button_medium_opaque(self) -> bascenev1.Mesh:
        import bascenev1

        return bascenev1.getmesh(f'{_APVERID}:meshes/button_medium_opaque')

    @property
    def button_medium_transparent(self) -> bascenev1.Mesh:
        import bascenev1

        return bascenev1.getmesh(f'{_APVERID}:meshes/button_medium_transparent')

    @property
    def button_small_opaque(self) -> bascenev1.Mesh:
        import bascenev1

        return bascenev1.getmesh(f'{_APVERID}:meshes/button_small_opaque')

    @property
    def button_small_transparent(self) -> bascenev1.Mesh:
        import bascenev1

        return bascenev1.getmesh(f'{_APVERID}:meshes/button_small_transparent')

    @property
    def button_square_opaque(self) -> bascenev1.Mesh:
        import bascenev1

        return bascenev1.getmesh(f'{_APVERID}:meshes/button_square_opaque')

    @property
    def button_square_transparent(self) -> bascenev1.Mesh:
        import bascenev1

        return bascenev1.getmesh(f'{_APVERID}:meshes/button_square_transparent')

    @property
    def button_tab_opaque(self) -> bascenev1.Mesh:
        import bascenev1

        return bascenev1.getmesh(f'{_APVERID}:meshes/button_tab_opaque')

    @property
    def button_tab_transparent(self) -> bascenev1.Mesh:
        import bascenev1

        return bascenev1.getmesh(f'{_APVERID}:meshes/button_tab_transparent')

    @property
    def check_transparent(self) -> bascenev1.Mesh:
        import bascenev1

        return bascenev1.getmesh(f'{_APVERID}:meshes/check_transparent')

    @property
    def cross_out(self) -> bascenev1.Mesh:
        import bascenev1

        return bascenev1.getmesh(f'{_APVERID}:meshes/cross_out')

    @property
    def cylinder(self) -> bascenev1.Mesh:
        import bascenev1

        return bascenev1.getmesh(f'{_APVERID}:meshes/cylinder')

    @property
    def eye_ball(self) -> bascenev1.Mesh:
        import bascenev1

        return bascenev1.getmesh(f'{_APVERID}:meshes/eye_ball')

    @property
    def eye_ball_iris(self) -> bascenev1.Mesh:
        import bascenev1

        return bascenev1.getmesh(f'{_APVERID}:meshes/eye_ball_iris')

    @property
    def eye_lid(self) -> bascenev1.Mesh:
        import bascenev1

        return bascenev1.getmesh(f'{_APVERID}:meshes/eye_lid')

    @property
    def flag_pole(self) -> bascenev1.Mesh:
        import bascenev1

        return bascenev1.getmesh(f'{_APVERID}:meshes/flag_pole')

    @property
    def flag_stand(self) -> bascenev1.Mesh:
        import bascenev1

        return bascenev1.getmesh(f'{_APVERID}:meshes/flag_stand')

    @property
    def flash(self) -> bascenev1.Mesh:
        import bascenev1

        return bascenev1.getmesh(f'{_APVERID}:meshes/flash')

    @property
    def hair_tuft1(self) -> bascenev1.Mesh:
        import bascenev1

        return bascenev1.getmesh(f'{_APVERID}:meshes/hair_tuft1')

    @property
    def hair_tuft1b(self) -> bascenev1.Mesh:
        import bascenev1

        return bascenev1.getmesh(f'{_APVERID}:meshes/hair_tuft1b')

    @property
    def hair_tuft2(self) -> bascenev1.Mesh:
        import bascenev1

        return bascenev1.getmesh(f'{_APVERID}:meshes/hair_tuft2')

    @property
    def hair_tuft3(self) -> bascenev1.Mesh:
        import bascenev1

        return bascenev1.getmesh(f'{_APVERID}:meshes/hair_tuft3')

    @property
    def hair_tuft4(self) -> bascenev1.Mesh:
        import bascenev1

        return bascenev1.getmesh(f'{_APVERID}:meshes/hair_tuft4')

    @property
    def image16x1(self) -> bascenev1.Mesh:
        import bascenev1

        return bascenev1.getmesh(f'{_APVERID}:meshes/image16x1')

    @property
    def image1x1(self) -> bascenev1.Mesh:
        import bascenev1

        return bascenev1.getmesh(f'{_APVERID}:meshes/image1x1')

    @property
    def image1x1_full_screen(self) -> bascenev1.Mesh:
        import bascenev1

        return bascenev1.getmesh(f'{_APVERID}:meshes/image1x1_full_screen')

    @property
    def image1x1_vrfull_screen(self) -> bascenev1.Mesh:
        import bascenev1

        return bascenev1.getmesh(f'{_APVERID}:meshes/image1x1_vrfull_screen')

    @property
    def image2x1(self) -> bascenev1.Mesh:
        import bascenev1

        return bascenev1.getmesh(f'{_APVERID}:meshes/image2x1')

    @property
    def image4x1(self) -> bascenev1.Mesh:
        import bascenev1

        return bascenev1.getmesh(f'{_APVERID}:meshes/image4x1')

    @property
    def locator(self) -> bascenev1.Mesh:
        import bascenev1

        return bascenev1.getmesh(f'{_APVERID}:meshes/locator')

    @property
    def locator_box(self) -> bascenev1.Mesh:
        import bascenev1

        return bascenev1.getmesh(f'{_APVERID}:meshes/locator_box')

    @property
    def locator_circle(self) -> bascenev1.Mesh:
        import bascenev1

        return bascenev1.getmesh(f'{_APVERID}:meshes/locator_circle')

    @property
    def locator_circle_outline(self) -> bascenev1.Mesh:
        import bascenev1

        return bascenev1.getmesh(f'{_APVERID}:meshes/locator_circle_outline')

    @property
    def overlay_guide(self) -> bascenev1.Mesh:
        import bascenev1

        return bascenev1.getmesh(f'{_APVERID}:meshes/overlay_guide')

    @property
    def scorch(self) -> bascenev1.Mesh:
        import bascenev1

        return bascenev1.getmesh(f'{_APVERID}:meshes/scorch')

    @property
    def scroll_bar_thumb_opaque(self) -> bascenev1.Mesh:
        import bascenev1

        return bascenev1.getmesh(f'{_APVERID}:meshes/scroll_bar_thumb_opaque')

    @property
    def scroll_bar_thumb_short_opaque(self) -> bascenev1.Mesh:
        import bascenev1

        return bascenev1.getmesh(
            f'{_APVERID}:meshes/scroll_bar_thumb_short_opaque'
        )

    @property
    def scroll_bar_thumb_short_simple(self) -> bascenev1.Mesh:
        import bascenev1

        return bascenev1.getmesh(
            f'{_APVERID}:meshes/scroll_bar_thumb_short_simple'
        )

    @property
    def scroll_bar_thumb_short_transparent(self) -> bascenev1.Mesh:
        import bascenev1

        return bascenev1.getmesh(
            f'{_APVERID}:meshes/scroll_bar_thumb_short_transparent'
        )

    @property
    def scroll_bar_thumb_simple(self) -> bascenev1.Mesh:
        import bascenev1

        return bascenev1.getmesh(f'{_APVERID}:meshes/scroll_bar_thumb_simple')

    @property
    def scroll_bar_thumb_transparent(self) -> bascenev1.Mesh:
        import bascenev1

        return bascenev1.getmesh(
            f'{_APVERID}:meshes/scroll_bar_thumb_transparent'
        )

    @property
    def scroll_bar_trough_transparent(self) -> bascenev1.Mesh:
        import bascenev1

        return bascenev1.getmesh(
            f'{_APVERID}:meshes/scroll_bar_trough_transparent'
        )

    @property
    def shield(self) -> bascenev1.Mesh:
        import bascenev1

        return bascenev1.getmesh(f'{_APVERID}:meshes/shield')

    @property
    def shock_wave(self) -> bascenev1.Mesh:
        import bascenev1

        return bascenev1.getmesh(f'{_APVERID}:meshes/shock_wave')

    @property
    def shrapnel1(self) -> bascenev1.Mesh:
        import bascenev1

        return bascenev1.getmesh(f'{_APVERID}:meshes/shrapnel1')

    @property
    def shrapnel_board(self) -> bascenev1.Mesh:
        import bascenev1

        return bascenev1.getmesh(f'{_APVERID}:meshes/shrapnel_board')

    @property
    def shrapnel_slime(self) -> bascenev1.Mesh:
        import bascenev1

        return bascenev1.getmesh(f'{_APVERID}:meshes/shrapnel_slime')

    @property
    def soft_edge_inside(self) -> bascenev1.Mesh:
        import bascenev1

        return bascenev1.getmesh(f'{_APVERID}:meshes/soft_edge_inside')

    @property
    def soft_edge_outside(self) -> bascenev1.Mesh:
        import bascenev1

        return bascenev1.getmesh(f'{_APVERID}:meshes/soft_edge_outside')

    @property
    def text_box_transparent(self) -> bascenev1.Mesh:
        import bascenev1

        return bascenev1.getmesh(f'{_APVERID}:meshes/text_box_transparent')

    @property
    def vr_fade(self) -> bascenev1.Mesh:
        import bascenev1

        return bascenev1.getmesh(f'{_APVERID}:meshes/vr_fade')

    @property
    def vr_overlay(self) -> bascenev1.Mesh:
        import bascenev1

        return bascenev1.getmesh(f'{_APVERID}:meshes/vr_overlay')

    @property
    def window_hsmall_vmed_opaque(self) -> bascenev1.Mesh:
        import bascenev1

        return bascenev1.getmesh(f'{_APVERID}:meshes/window_hsmall_vmed_opaque')

    @property
    def window_hsmall_vmed_transparent(self) -> bascenev1.Mesh:
        import bascenev1

        return bascenev1.getmesh(
            f'{_APVERID}:meshes/window_hsmall_vmed_transparent'
        )

    @property
    def window_hsmall_vsmall_opaque(self) -> bascenev1.Mesh:
        import bascenev1

        return bascenev1.getmesh(
            f'{_APVERID}:meshes/window_hsmall_vsmall_opaque'
        )

    @property
    def window_hsmall_vsmall_transparent(self) -> bascenev1.Mesh:
        import bascenev1

        return bascenev1.getmesh(
            f'{_APVERID}:meshes/window_hsmall_vsmall_transparent'
        )

    @property
    def wing(self) -> bascenev1.Mesh:
        import bascenev1

        return bascenev1.getmesh(f'{_APVERID}:meshes/wing')


meshes = _Meshes()


class _Textures:
    @property
    def action_buttons(self) -> bascenev1.Texture:
        import bascenev1

        return bascenev1.gettexture(f'{_APVERID}:textures/action_buttons')

    @property
    def arrow(self) -> bascenev1.Texture:
        import bascenev1

        return bascenev1.gettexture(f'{_APVERID}:textures/arrow')

    @property
    def back_icon(self) -> bascenev1.Texture:
        import bascenev1

        return bascenev1.gettexture(f'{_APVERID}:textures/back_icon')

    @property
    def black(self) -> bascenev1.Texture:
        import bascenev1

        return bascenev1.gettexture(f'{_APVERID}:textures/black')

    @property
    def bomb_button(self) -> bascenev1.Texture:
        import bascenev1

        return bascenev1.gettexture(f'{_APVERID}:textures/bomb_button')

    @property
    def boxing_gloves_color(self) -> bascenev1.Texture:
        import bascenev1

        return bascenev1.gettexture(f'{_APVERID}:textures/boxing_gloves_color')

    @property
    def button_square(self) -> bascenev1.Texture:
        import bascenev1

        return bascenev1.gettexture(f'{_APVERID}:textures/button_square')

    @property
    def button_square_wide(self) -> bascenev1.Texture:
        import bascenev1

        return bascenev1.gettexture(f'{_APVERID}:textures/button_square_wide')

    @property
    def character_icon_mask(self) -> bascenev1.Texture:
        import bascenev1

        return bascenev1.gettexture(f'{_APVERID}:textures/character_icon_mask')

    @property
    def circle(self) -> bascenev1.Texture:
        import bascenev1

        return bascenev1.gettexture(f'{_APVERID}:textures/circle')

    @property
    def circle_no_alpha(self) -> bascenev1.Texture:
        import bascenev1

        return bascenev1.gettexture(f'{_APVERID}:textures/circle_no_alpha')

    @property
    def circle_outline(self) -> bascenev1.Texture:
        import bascenev1

        return bascenev1.gettexture(f'{_APVERID}:textures/circle_outline')

    @property
    def circle_outline_no_alpha(self) -> bascenev1.Texture:
        import bascenev1

        return bascenev1.gettexture(
            f'{_APVERID}:textures/circle_outline_no_alpha'
        )

    @property
    def circle_shadow(self) -> bascenev1.Texture:
        import bascenev1

        return bascenev1.gettexture(f'{_APVERID}:textures/circle_shadow')

    @property
    def circle_soft(self) -> bascenev1.Texture:
        import bascenev1

        return bascenev1.gettexture(f'{_APVERID}:textures/circle_soft')

    @property
    def cursor(self) -> bascenev1.Texture:
        import bascenev1

        return bascenev1.gettexture(f'{_APVERID}:textures/cursor')

    @property
    def explosion(self) -> bascenev1.Texture:
        import bascenev1

        return bascenev1.gettexture(f'{_APVERID}:textures/explosion')

    @property
    def eye_color(self) -> bascenev1.Texture:
        import bascenev1

        return bascenev1.gettexture(f'{_APVERID}:textures/eye_color')

    @property
    def eye_color_tint_mask(self) -> bascenev1.Texture:
        import bascenev1

        return bascenev1.gettexture(f'{_APVERID}:textures/eye_color_tint_mask')

    @property
    def flag_pole_color(self) -> bascenev1.Texture:
        import bascenev1

        return bascenev1.gettexture(f'{_APVERID}:textures/flag_pole_color')

    @property
    def font_big(self) -> bascenev1.Texture:
        import bascenev1

        return bascenev1.gettexture(f'{_APVERID}:textures/font_big')

    @property
    def font_extras(self) -> bascenev1.Texture:
        import bascenev1

        return bascenev1.gettexture(f'{_APVERID}:textures/font_extras')

    @property
    def font_extras2(self) -> bascenev1.Texture:
        import bascenev1

        return bascenev1.gettexture(f'{_APVERID}:textures/font_extras2')

    @property
    def font_extras3(self) -> bascenev1.Texture:
        import bascenev1

        return bascenev1.gettexture(f'{_APVERID}:textures/font_extras3')

    @property
    def font_extras4(self) -> bascenev1.Texture:
        import bascenev1

        return bascenev1.gettexture(f'{_APVERID}:textures/font_extras4')

    @property
    def font_extras5(self) -> bascenev1.Texture:
        import bascenev1

        return bascenev1.gettexture(f'{_APVERID}:textures/font_extras5')

    @property
    def font_small0(self) -> bascenev1.Texture:
        import bascenev1

        return bascenev1.gettexture(f'{_APVERID}:textures/font_small0')

    @property
    def font_small1(self) -> bascenev1.Texture:
        import bascenev1

        return bascenev1.gettexture(f'{_APVERID}:textures/font_small1')

    @property
    def font_small2(self) -> bascenev1.Texture:
        import bascenev1

        return bascenev1.gettexture(f'{_APVERID}:textures/font_small2')

    @property
    def font_small3(self) -> bascenev1.Texture:
        import bascenev1

        return bascenev1.gettexture(f'{_APVERID}:textures/font_small3')

    @property
    def font_small4(self) -> bascenev1.Texture:
        import bascenev1

        return bascenev1.gettexture(f'{_APVERID}:textures/font_small4')

    @property
    def font_small5(self) -> bascenev1.Texture:
        import bascenev1

        return bascenev1.gettexture(f'{_APVERID}:textures/font_small5')

    @property
    def font_small6(self) -> bascenev1.Texture:
        import bascenev1

        return bascenev1.gettexture(f'{_APVERID}:textures/font_small6')

    @property
    def font_small7(self) -> bascenev1.Texture:
        import bascenev1

        return bascenev1.gettexture(f'{_APVERID}:textures/font_small7')

    @property
    def fuse(self) -> bascenev1.Texture:
        import bascenev1

        return bascenev1.gettexture(f'{_APVERID}:textures/fuse')

    @property
    def glow(self) -> bascenev1.Texture:
        import bascenev1

        return bascenev1.gettexture(f'{_APVERID}:textures/glow')

    @property
    def light(self) -> bascenev1.Texture:
        import bascenev1

        return bascenev1.gettexture(f'{_APVERID}:textures/light')

    @property
    def light_sharp(self) -> bascenev1.Texture:
        import bascenev1

        return bascenev1.gettexture(f'{_APVERID}:textures/light_sharp')

    @property
    def light_soft(self) -> bascenev1.Texture:
        import bascenev1

        return bascenev1.gettexture(f'{_APVERID}:textures/light_soft')

    @property
    def menu_button(self) -> bascenev1.Texture:
        import bascenev1

        return bascenev1.gettexture(f'{_APVERID}:textures/menu_button')

    @property
    def nub(self) -> bascenev1.Texture:
        import bascenev1

        return bascenev1.gettexture(f'{_APVERID}:textures/nub')

    @property
    def ouya_abutton(self) -> bascenev1.Texture:
        import bascenev1

        return bascenev1.gettexture(f'{_APVERID}:textures/ouya_abutton')

    @property
    def page_left_right(self) -> bascenev1.Texture:
        import bascenev1

        return bascenev1.gettexture(f'{_APVERID}:textures/page_left_right')

    @property
    def rgb_stripes(self) -> bascenev1.Texture:
        import bascenev1

        return bascenev1.gettexture(f'{_APVERID}:textures/rgb_stripes')

    @property
    def scorch(self) -> bascenev1.Texture:
        import bascenev1

        return bascenev1.gettexture(f'{_APVERID}:textures/scorch')

    @property
    def scorch_big(self) -> bascenev1.Texture:
        import bascenev1

        return bascenev1.gettexture(f'{_APVERID}:textures/scorch_big')

    @property
    def scroll_widget(self) -> bascenev1.Texture:
        import bascenev1

        return bascenev1.gettexture(f'{_APVERID}:textures/scroll_widget')

    @property
    def scroll_widget_glow(self) -> bascenev1.Texture:
        import bascenev1

        return bascenev1.gettexture(f'{_APVERID}:textures/scroll_widget_glow')

    @property
    def shadow(self) -> bascenev1.Texture:
        import bascenev1

        return bascenev1.gettexture(f'{_APVERID}:textures/shadow')

    @property
    def shadow_sharp(self) -> bascenev1.Texture:
        import bascenev1

        return bascenev1.gettexture(f'{_APVERID}:textures/shadow_sharp')

    @property
    def shadow_soft(self) -> bascenev1.Texture:
        import bascenev1

        return bascenev1.gettexture(f'{_APVERID}:textures/shadow_soft')

    @property
    def shield(self) -> bascenev1.Texture:
        import bascenev1

        return bascenev1.gettexture(f'{_APVERID}:textures/shield')

    @property
    def shrapnel1_color(self) -> bascenev1.Texture:
        import bascenev1

        return bascenev1.gettexture(f'{_APVERID}:textures/shrapnel1_color')

    @property
    def smoke(self) -> bascenev1.Texture:
        import bascenev1

        return bascenev1.gettexture(f'{_APVERID}:textures/smoke')

    @property
    def soft_rect(self) -> bascenev1.Texture:
        import bascenev1

        return bascenev1.gettexture(f'{_APVERID}:textures/soft_rect')

    @property
    def soft_rect2(self) -> bascenev1.Texture:
        import bascenev1

        return bascenev1.gettexture(f'{_APVERID}:textures/soft_rect2')

    @property
    def soft_rect_vertical(self) -> bascenev1.Texture:
        import bascenev1

        return bascenev1.gettexture(f'{_APVERID}:textures/soft_rect_vertical')

    @property
    def sparks(self) -> bascenev1.Texture:
        import bascenev1

        return bascenev1.gettexture(f'{_APVERID}:textures/sparks')

    @property
    def spinner(self) -> bascenev1.Texture:
        import bascenev1

        return bascenev1.gettexture(f'{_APVERID}:textures/spinner')

    @property
    def spinner0(self) -> bascenev1.Texture:
        import bascenev1

        return bascenev1.gettexture(f'{_APVERID}:textures/spinner0')

    @property
    def spinner1(self) -> bascenev1.Texture:
        import bascenev1

        return bascenev1.gettexture(f'{_APVERID}:textures/spinner1')

    @property
    def spinner10(self) -> bascenev1.Texture:
        import bascenev1

        return bascenev1.gettexture(f'{_APVERID}:textures/spinner10')

    @property
    def spinner11(self) -> bascenev1.Texture:
        import bascenev1

        return bascenev1.gettexture(f'{_APVERID}:textures/spinner11')

    @property
    def spinner2(self) -> bascenev1.Texture:
        import bascenev1

        return bascenev1.gettexture(f'{_APVERID}:textures/spinner2')

    @property
    def spinner3(self) -> bascenev1.Texture:
        import bascenev1

        return bascenev1.gettexture(f'{_APVERID}:textures/spinner3')

    @property
    def spinner4(self) -> bascenev1.Texture:
        import bascenev1

        return bascenev1.gettexture(f'{_APVERID}:textures/spinner4')

    @property
    def spinner5(self) -> bascenev1.Texture:
        import bascenev1

        return bascenev1.gettexture(f'{_APVERID}:textures/spinner5')

    @property
    def spinner6(self) -> bascenev1.Texture:
        import bascenev1

        return bascenev1.gettexture(f'{_APVERID}:textures/spinner6')

    @property
    def spinner7(self) -> bascenev1.Texture:
        import bascenev1

        return bascenev1.gettexture(f'{_APVERID}:textures/spinner7')

    @property
    def spinner8(self) -> bascenev1.Texture:
        import bascenev1

        return bascenev1.gettexture(f'{_APVERID}:textures/spinner8')

    @property
    def spinner9(self) -> bascenev1.Texture:
        import bascenev1

        return bascenev1.gettexture(f'{_APVERID}:textures/spinner9')

    @property
    def start_button(self) -> bascenev1.Texture:
        import bascenev1

        return bascenev1.gettexture(f'{_APVERID}:textures/start_button')

    @property
    def text_clear_button(self) -> bascenev1.Texture:
        import bascenev1

        return bascenev1.gettexture(f'{_APVERID}:textures/text_clear_button')

    @property
    def touch_arrows(self) -> bascenev1.Texture:
        import bascenev1

        return bascenev1.gettexture(f'{_APVERID}:textures/touch_arrows')

    @property
    def touch_arrows_actions(self) -> bascenev1.Texture:
        import bascenev1

        return bascenev1.gettexture(f'{_APVERID}:textures/touch_arrows_actions')

    @property
    def ui_atlas(self) -> bascenev1.Texture:
        import bascenev1

        return bascenev1.gettexture(f'{_APVERID}:textures/ui_atlas')

    @property
    def ui_atlas2(self) -> bascenev1.Texture:
        import bascenev1

        return bascenev1.gettexture(f'{_APVERID}:textures/ui_atlas2')

    @property
    def users_button(self) -> bascenev1.Texture:
        import bascenev1

        return bascenev1.gettexture(f'{_APVERID}:textures/users_button')

    @property
    def white(self) -> bascenev1.Texture:
        import bascenev1

        return bascenev1.gettexture(f'{_APVERID}:textures/white')

    @property
    def window_hsmall_vmed(self) -> bascenev1.Texture:
        import bascenev1

        return bascenev1.gettexture(f'{_APVERID}:textures/window_hsmall_vmed')

    @property
    def window_hsmall_vsmall(self) -> bascenev1.Texture:
        import bascenev1

        return bascenev1.gettexture(f'{_APVERID}:textures/window_hsmall_vsmall')

    @property
    def wings(self) -> bascenev1.Texture:
        import bascenev1

        return bascenev1.gettexture(f'{_APVERID}:textures/wings')


textures = _Textures()
