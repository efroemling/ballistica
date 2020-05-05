# Copyright (c) 2011-2020 Eric Froemling
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
# -----------------------------------------------------------------------------
"""UI functionality related to UI items."""
from __future__ import annotations

from typing import TYPE_CHECKING

import _ba
import ba

if TYPE_CHECKING:
    from typing import Any, Tuple, Dict, Optional


def instantiate_store_item_display(item_name: str,
                                   item: Dict[str, Any],
                                   parent_widget: ba.Widget,
                                   b_pos: Tuple[float, float],
                                   b_width: float,
                                   b_height: float,
                                   boffs_h: float = 0.0,
                                   boffs_h2: float = 0.0,
                                   boffs_v2: float = 0,
                                   delay: float = 0.0,
                                   button: bool = True) -> None:
    """(internal)"""
    # pylint: disable=too-many-statements
    # pylint: disable=too-many-branches
    # pylint: disable=too-many-locals
    from ba.internal import (get_store_item, get_store_item_name_translated,
                             get_clean_price)
    del boffs_h  # unused arg
    del boffs_h2  # unused arg
    del boffs_v2  # unused arg
    item_info = get_store_item(item_name)
    title_v = 0.24
    price_v = 0.145
    base_text_scale = 1.0

    item['name'] = title = get_store_item_name_translated(item_name)

    btn: Optional[ba.Widget]
    if button:
        item['button'] = btn = ba.buttonwidget(parent=parent_widget,
                                               position=b_pos,
                                               transition_delay=delay,
                                               show_buffer_top=76.0,
                                               enable_sound=False,
                                               button_type='square',
                                               size=(b_width, b_height),
                                               autoselect=True,
                                               label='')
        ba.widget(edit=btn, show_buffer_bottom=76.0)
    else:
        btn = None

    b_offs_x = -0.015 * b_width
    check_pos = 0.76

    icon_tex = None
    tint_tex = None
    tint_color = None
    tint2_color = None
    tex_name: Optional[str] = None
    desc: Optional[str] = None
    modes: Optional[ba.Lstr] = None

    if item_name.startswith('characters.'):
        character = ba.app.spaz_appearances[item_info['character']]
        tint_color = (
            item_info['color'] if 'color' in item_info else
            character.default_color if character.default_color is not None else
            (1, 1, 1))
        tint2_color = (item_info['highlight'] if 'highlight' in item_info else
                       character.default_highlight if
                       character.default_highlight is not None else (1, 1, 1))
        icon_tex = character.icon_texture
        tint_tex = character.icon_mask_texture
        title_v = 0.255
        price_v = 0.145
    elif item_name in ['upgrades.pro', 'pro']:
        base_text_scale = 0.6
        title_v = 0.85
        price_v = 0.15
    elif item_name.startswith('maps.'):
        map_type = item_info['map_type']
        tex_name = map_type.get_preview_texture_name()
        title_v = 0.312
        price_v = 0.17

    elif item_name.startswith('games.'):
        gametype = item_info['gametype']
        modes_l = []
        if gametype.supports_session_type(ba.CoopSession):
            modes_l.append(ba.Lstr(resource='playModes.coopText'))
        if gametype.supports_session_type(ba.DualTeamSession):
            modes_l.append(ba.Lstr(resource='playModes.teamsText'))
        if gametype.supports_session_type(ba.FreeForAllSession):
            modes_l.append(ba.Lstr(resource='playModes.freeForAllText'))

        if len(modes_l) == 3:
            modes = ba.Lstr(value='${A}, ${B}, ${C}',
                            subs=[('${A}', modes_l[0]), ('${B}', modes_l[1]),
                                  ('${C}', modes_l[2])])
        elif len(modes_l) == 2:
            modes = ba.Lstr(value='${A}, ${B}',
                            subs=[('${A}', modes_l[0]), ('${B}', modes_l[1])])
        elif len(modes_l) == 1:
            modes = modes_l[0]
        else:
            raise Exception()
        desc = gametype.get_description_display_string(ba.CoopSession)
        tex_name = item_info['previewTex']
        base_text_scale = 0.8
        title_v = 0.48
        price_v = 0.17

    elif item_name.startswith('icons.'):
        base_text_scale = 1.5
        price_v = 0.2
        check_pos = 0.6

    if item_name.startswith('characters.'):
        frame_size = b_width * 0.7
        im_dim = frame_size * (100.0 / 113.0)
        im_pos = (b_pos[0] + b_width * 0.5 - im_dim * 0.5 + b_offs_x,
                  b_pos[1] + b_height * 0.57 - im_dim * 0.5)
        mask_texture = ba.gettexture('characterIconMask')
        assert icon_tex is not None
        assert tint_tex is not None
        ba.imagewidget(parent=parent_widget,
                       position=im_pos,
                       size=(im_dim, im_dim),
                       color=(1, 1, 1),
                       transition_delay=delay,
                       mask_texture=mask_texture,
                       draw_controller=btn,
                       texture=ba.gettexture(icon_tex),
                       tint_texture=ba.gettexture(tint_tex),
                       tint_color=tint_color,
                       tint2_color=tint2_color)

    if item_name in ['pro', 'upgrades.pro']:
        frame_size = b_width * 0.5
        im_dim = frame_size * (100.0 / 113.0)
        im_pos = (b_pos[0] + b_width * 0.5 - im_dim * 0.5 + b_offs_x,
                  b_pos[1] + b_height * 0.5 - im_dim * 0.5)
        ba.imagewidget(parent=parent_widget,
                       position=im_pos,
                       size=(im_dim, im_dim),
                       transition_delay=delay,
                       draw_controller=btn,
                       color=(0.3, 0.0, 0.3),
                       opacity=0.3,
                       texture=ba.gettexture('logo'))
        txt = ba.Lstr(resource='store.bombSquadProNewDescriptionText')

        # t = 'foo\nfoo\nfoo\nfoo\nfoo\nfoo'
        item['descriptionText'] = ba.textwidget(
            parent=parent_widget,
            text=txt,
            position=(b_pos[0] + b_width * 0.5, b_pos[1] + b_height * 0.69),
            transition_delay=delay,
            scale=b_width * (1.0 / 230.0) * base_text_scale * 0.75,
            maxwidth=b_width * 0.75,
            max_height=b_height * 0.2,
            size=(0, 0),
            h_align='center',
            v_align='center',
            draw_controller=btn,
            color=(0.3, 1, 0.3))

        extra_backings = item['extra_backings'] = []
        extra_images = item['extra_images'] = []
        extra_texts = item['extra_texts'] = []
        extra_texts_2 = item['extra_texts_2'] = []

        backing_color = (0.5, 0.8, 0.3) if button else (0.6, 0.5, 0.65)
        b_square_texture = ba.gettexture('buttonSquare')
        char_mask_texture = ba.gettexture('characterIconMask')

        pos = (0.17, 0.43)
        tile_size = (b_width * 0.16 * 1.2, b_width * 0.2 * 1.2)
        tile_pos = (b_pos[0] + b_width * pos[0], b_pos[1] + b_height * pos[1])
        extra_backings.append(
            ba.imagewidget(parent=parent_widget,
                           position=(tile_pos[0] - tile_size[0] * 0.5,
                                     tile_pos[1] - tile_size[1] * 0.5),
                           size=tile_size,
                           transition_delay=delay,
                           draw_controller=btn,
                           color=backing_color,
                           texture=b_square_texture))
        im_size = tile_size[0] * 0.8
        extra_images.append(
            ba.imagewidget(parent=parent_widget,
                           position=(tile_pos[0] - im_size * 0.5,
                                     tile_pos[1] - im_size * 0.4),
                           size=(im_size, im_size),
                           transition_delay=delay,
                           draw_controller=btn,
                           color=(1, 1, 1),
                           texture=ba.gettexture('ticketsMore')))
        bonus_tickets = str(
            _ba.get_account_misc_read_val('proBonusTickets', 100))
        extra_texts.append(
            ba.textwidget(parent=parent_widget,
                          draw_controller=btn,
                          position=(tile_pos[0] - tile_size[0] * 0.03,
                                    tile_pos[1] - tile_size[1] * 0.25),
                          size=(0, 0),
                          color=(0.6, 1, 0.6),
                          transition_delay=delay,
                          h_align='center',
                          v_align='center',
                          maxwidth=tile_size[0] * 0.7,
                          scale=0.55,
                          text=ba.Lstr(resource='getTicketsWindow.ticketsText',
                                       subs=[('${COUNT}', bonus_tickets)]),
                          flatness=1.0,
                          shadow=0.0))

        for charname, pos in [('Kronk', (0.32, 0.45)), ('Zoe', (0.425, 0.4)),
                              ('Jack Morgan', (0.555, 0.45)),
                              ('Mel', (0.645, 0.4))]:
            tile_size = (b_width * 0.16 * 0.9, b_width * 0.2 * 0.9)
            tile_pos = (b_pos[0] + b_width * pos[0],
                        b_pos[1] + b_height * pos[1])
            character = ba.app.spaz_appearances[charname]
            extra_backings.append(
                ba.imagewidget(parent=parent_widget,
                               position=(tile_pos[0] - tile_size[0] * 0.5,
                                         tile_pos[1] - tile_size[1] * 0.5),
                               size=tile_size,
                               transition_delay=delay,
                               draw_controller=btn,
                               color=backing_color,
                               texture=b_square_texture))
            im_size = tile_size[0] * 0.7
            extra_images.append(
                ba.imagewidget(parent=parent_widget,
                               position=(tile_pos[0] - im_size * 0.53,
                                         tile_pos[1] - im_size * 0.35),
                               size=(im_size, im_size),
                               transition_delay=delay,
                               draw_controller=btn,
                               color=(1, 1, 1),
                               texture=ba.gettexture(character.icon_texture),
                               tint_texture=ba.gettexture(
                                   character.icon_mask_texture),
                               tint_color=character.default_color,
                               tint2_color=character.default_highlight,
                               mask_texture=char_mask_texture))
            extra_texts.append(
                ba.textwidget(parent=parent_widget,
                              draw_controller=btn,
                              position=(tile_pos[0] - im_size * 0.03,
                                        tile_pos[1] - im_size * 0.51),
                              size=(0, 0),
                              color=(0.6, 1, 0.6),
                              transition_delay=delay,
                              h_align='center',
                              v_align='center',
                              maxwidth=tile_size[0] * 0.7,
                              scale=0.55,
                              text=ba.Lstr(translate=('characterNames',
                                                      charname)),
                              flatness=1.0,
                              shadow=0.0))

        # If we have a 'total-worth' item-id for this id, show that price so
        # the user knows how much this is worth.
        total_worth_item = _ba.get_account_misc_read_val('twrths',
                                                         {}).get(item_name)
        total_worth_price: Optional[str]
        if total_worth_item is not None:
            price = _ba.get_price(total_worth_item)
            total_worth_price = (get_clean_price(price)
                                 if price is not None else '??')
        else:
            total_worth_price = None

        if total_worth_price is not None:
            total_worth_text = ba.Lstr(resource='store.totalWorthText',
                                       subs=[('${TOTAL_WORTH}',
                                              total_worth_price)])
            extra_texts_2.append(
                ba.textwidget(parent=parent_widget,
                              text=total_worth_text,
                              position=(b_pos[0] + b_width * 0.5 + b_offs_x,
                                        b_pos[1] + b_height * 0.25),
                              transition_delay=delay,
                              scale=b_width * (1.0 / 230.0) * base_text_scale *
                              0.45,
                              maxwidth=b_width * 0.5,
                              size=(0, 0),
                              h_align='center',
                              v_align='center',
                              shadow=1.0,
                              flatness=1.0,
                              draw_controller=btn,
                              color=(0.3, 1, 1)))

        model_opaque = ba.getmodel('level_select_button_opaque')
        model_transparent = ba.getmodel('level_select_button_transparent')
        mask_tex = ba.gettexture('mapPreviewMask')
        for levelname, preview_tex_name, pos in [
            ('Infinite Onslaught', 'doomShroomPreview', (0.80, 0.48)),
            ('Infinite Runaround', 'towerDPreview', (0.80, 0.32))
        ]:
            tile_size = (b_width * 0.2, b_width * 0.13)
            tile_pos = (b_pos[0] + b_width * pos[0],
                        b_pos[1] + b_height * pos[1])
            im_size = tile_size[0] * 0.8
            extra_backings.append(
                ba.imagewidget(parent=parent_widget,
                               position=(tile_pos[0] - tile_size[0] * 0.5,
                                         tile_pos[1] - tile_size[1] * 0.5),
                               size=tile_size,
                               transition_delay=delay,
                               draw_controller=btn,
                               color=backing_color,
                               texture=b_square_texture))

            # Hack - gotta draw two transparent versions to avoid z issues.
            for mod in model_opaque, model_transparent:
                extra_images.append(
                    ba.imagewidget(parent=parent_widget,
                                   position=(tile_pos[0] - im_size * 0.52,
                                             tile_pos[1] - im_size * 0.2),
                                   size=(im_size, im_size * 0.5),
                                   transition_delay=delay,
                                   model_transparent=mod,
                                   mask_texture=mask_tex,
                                   draw_controller=btn,
                                   texture=ba.gettexture(preview_tex_name)))

            extra_texts.append(
                ba.textwidget(parent=parent_widget,
                              draw_controller=btn,
                              position=(tile_pos[0] - im_size * 0.03,
                                        tile_pos[1] - im_size * 0.2),
                              size=(0, 0),
                              color=(0.6, 1, 0.6),
                              transition_delay=delay,
                              h_align='center',
                              v_align='center',
                              maxwidth=tile_size[0] * 0.7,
                              scale=0.55,
                              text=ba.Lstr(translate=('coopLevelNames',
                                                      levelname)),
                              flatness=1.0,
                              shadow=0.0))

    if item_name.startswith('icons.'):
        item['icon_text'] = ba.textwidget(
            parent=parent_widget,
            text=item_info['icon'],
            position=(b_pos[0] + b_width * 0.5, b_pos[1] + b_height * 0.5),
            transition_delay=delay,
            scale=b_width * (1.0 / 230.0) * base_text_scale * 2.0,
            maxwidth=b_width * 0.9,
            max_height=b_height * 0.9,
            size=(0, 0),
            h_align='center',
            v_align='center',
            draw_controller=btn)

    if item_name.startswith('maps.'):
        frame_size = b_width * 0.9
        im_dim = frame_size * (100.0 / 113.0)
        im_pos = (b_pos[0] + b_width * 0.5 - im_dim * 0.5 + b_offs_x,
                  b_pos[1] + b_height * 0.62 - im_dim * 0.25)
        model_opaque = ba.getmodel('level_select_button_opaque')
        model_transparent = ba.getmodel('level_select_button_transparent')
        mask_tex = ba.gettexture('mapPreviewMask')
        assert tex_name is not None
        ba.imagewidget(parent=parent_widget,
                       position=im_pos,
                       size=(im_dim, im_dim * 0.5),
                       transition_delay=delay,
                       model_opaque=model_opaque,
                       model_transparent=model_transparent,
                       mask_texture=mask_tex,
                       draw_controller=btn,
                       texture=ba.gettexture(tex_name))

    if item_name.startswith('games.'):
        frame_size = b_width * 0.8
        im_dim = frame_size * (100.0 / 113.0)
        im_pos = (b_pos[0] + b_width * 0.5 - im_dim * 0.5 + b_offs_x,
                  b_pos[1] + b_height * 0.72 - im_dim * 0.25)
        model_opaque = ba.getmodel('level_select_button_opaque')
        model_transparent = ba.getmodel('level_select_button_transparent')
        mask_tex = ba.gettexture('mapPreviewMask')
        assert tex_name is not None
        ba.imagewidget(parent=parent_widget,
                       position=im_pos,
                       size=(im_dim, im_dim * 0.5),
                       transition_delay=delay,
                       model_opaque=model_opaque,
                       model_transparent=model_transparent,
                       mask_texture=mask_tex,
                       draw_controller=btn,
                       texture=ba.gettexture(tex_name))
        item['descriptionText'] = ba.textwidget(
            parent=parent_widget,
            text=desc,
            position=(b_pos[0] + b_width * 0.5, b_pos[1] + b_height * 0.36),
            transition_delay=delay,
            scale=b_width * (1.0 / 230.0) * base_text_scale * 0.78,
            maxwidth=b_width * 0.8,
            max_height=b_height * 0.14,
            size=(0, 0),
            h_align='center',
            v_align='center',
            draw_controller=btn,
            flatness=1.0,
            shadow=0.0,
            color=(0.6, 1, 0.6))
        item['gameModesText'] = ba.textwidget(
            parent=parent_widget,
            text=modes,
            position=(b_pos[0] + b_width * 0.5, b_pos[1] + b_height * 0.26),
            transition_delay=delay,
            scale=b_width * (1.0 / 230.0) * base_text_scale * 0.65,
            maxwidth=b_width * 0.8,
            size=(0, 0),
            h_align='center',
            v_align='center',
            draw_controller=btn,
            shadow=0,
            flatness=1.0,
            color=(0.6, 0.8, 0.6))

    if not item_name.startswith('icons.'):
        item['title_text'] = ba.textwidget(
            parent=parent_widget,
            text=title,
            position=(b_pos[0] + b_width * 0.5 + b_offs_x,
                      b_pos[1] + b_height * title_v),
            transition_delay=delay,
            scale=b_width * (1.0 / 230.0) * base_text_scale,
            maxwidth=b_width * 0.8,
            size=(0, 0),
            h_align='center',
            v_align='center',
            draw_controller=btn,
            color=(0.7, 0.9, 0.7, 1.0))

    item['purchase_check'] = ba.imagewidget(
        parent=parent_widget,
        position=(b_pos[0] + b_width * check_pos, b_pos[1] + b_height * 0.05),
        transition_delay=delay,
        model_transparent=ba.getmodel('checkTransparent'),
        opacity=0.0,
        size=(60, 60),
        color=(0.6, 0.5, 0.8),
        draw_controller=btn,
        texture=ba.gettexture('uiAtlas'))
    item['price_widget'] = ba.textwidget(
        parent=parent_widget,
        text='',
        position=(b_pos[0] + b_width * 0.5 + b_offs_x,
                  b_pos[1] + b_height * price_v),
        transition_delay=delay,
        scale=b_width * (1.0 / 300.0) * base_text_scale,
        maxwidth=b_width * 0.9,
        size=(0, 0),
        h_align='center',
        v_align='center',
        draw_controller=btn,
        color=(0.2, 1, 0.2, 1.0))
    item['price_widget_left'] = ba.textwidget(
        parent=parent_widget,
        text='',
        position=(b_pos[0] + b_width * 0.33 + b_offs_x,
                  b_pos[1] + b_height * price_v),
        transition_delay=delay,
        scale=b_width * (1.0 / 300.0) * base_text_scale,
        maxwidth=b_width * 0.3,
        size=(0, 0),
        h_align='center',
        v_align='center',
        draw_controller=btn,
        color=(0.2, 1, 0.2, 0.5))
    item['price_widget_right'] = ba.textwidget(
        parent=parent_widget,
        text='',
        position=(b_pos[0] + b_width * 0.66 + b_offs_x,
                  b_pos[1] + b_height * price_v),
        transition_delay=delay,
        scale=1.1 * b_width * (1.0 / 300.0) * base_text_scale,
        maxwidth=b_width * 0.3,
        size=(0, 0),
        h_align='center',
        v_align='center',
        draw_controller=btn,
        color=(0.2, 1, 0.2, 1.0))
    item['price_slash_widget'] = ba.imagewidget(
        parent=parent_widget,
        position=(b_pos[0] + b_width * 0.33 + b_offs_x - 36,
                  b_pos[1] + b_height * price_v - 35),
        transition_delay=delay,
        texture=ba.gettexture('slash'),
        opacity=0.0,
        size=(70, 70),
        draw_controller=btn,
        color=(1, 0, 0))
    badge_rad = 44
    badge_center = (b_pos[0] + b_width * 0.1 + b_offs_x,
                    b_pos[1] + b_height * 0.87)
    item['sale_bg_widget'] = ba.imagewidget(
        parent=parent_widget,
        position=(badge_center[0] - badge_rad, badge_center[1] - badge_rad),
        opacity=0.0,
        transition_delay=delay,
        texture=ba.gettexture('circleZigZag'),
        draw_controller=btn,
        size=(badge_rad * 2, badge_rad * 2),
        color=(0.5, 0, 1))
    item['sale_title_widget'] = ba.textwidget(parent=parent_widget,
                                              position=(badge_center[0],
                                                        badge_center[1] + 12),
                                              transition_delay=delay,
                                              scale=1.0,
                                              maxwidth=badge_rad * 1.6,
                                              size=(0, 0),
                                              h_align='center',
                                              v_align='center',
                                              draw_controller=btn,
                                              shadow=0.0,
                                              flatness=1.0,
                                              color=(0, 1, 0))
    item['sale_time_widget'] = ba.textwidget(parent=parent_widget,
                                             position=(badge_center[0],
                                                       badge_center[1] - 12),
                                             transition_delay=delay,
                                             scale=0.7,
                                             maxwidth=badge_rad * 1.6,
                                             size=(0, 0),
                                             h_align='center',
                                             v_align='center',
                                             draw_controller=btn,
                                             shadow=0.0,
                                             flatness=1.0,
                                             color=(0.0, 1, 0.0, 1))
