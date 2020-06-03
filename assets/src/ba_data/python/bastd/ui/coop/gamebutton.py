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
"""Defines button for co-op games."""

from __future__ import annotations

import random
from typing import TYPE_CHECKING

import _ba
import ba

if TYPE_CHECKING:
    from typing import Optional, List, Tuple
    from bastd.ui.coop.browser import CoopBrowserWindow


class GameButton:
    """Button for entering co-op games."""

    def __init__(self, window: CoopBrowserWindow, parent: ba.Widget, game: str,
                 x: float, y: float, select: bool, row: str):
        # pylint: disable=too-many-statements
        # pylint: disable=too-many-locals
        from ba.internal import (get_achievements_for_coop_level, getcampaign)
        self._game = game
        sclx = 195.0
        scly = 195.0

        campaignname, levelname = game.split(':')

        # Hack: The Last Stand doesn't actually exist in the easy
        # tourney. We just want it for display purposes. Map it to
        # the hard-mode version.
        if game == 'Easy:The Last Stand':
            campaignname = 'Default'

        rating: Optional[float]
        campaign = getcampaign(campaignname)
        rating = campaign.getlevel(levelname).rating

        if game == 'Easy:The Last Stand':
            rating = None

        if rating is None or rating == 0.0:
            stars = 0
        elif rating >= 9.5:
            stars = 3
        elif rating >= 7.5:
            stars = 2
        else:
            stars = 1

        self._button = btn = ba.buttonwidget(
            parent=parent,
            position=(x + 23, y + 4),
            size=(sclx, scly),
            label='',
            on_activate_call=ba.Call(window.run, game),
            button_type='square',
            autoselect=True,
            on_select_call=ba.Call(window.sel_change, row, game))
        ba.widget(edit=btn,
                  show_buffer_bottom=50,
                  show_buffer_top=50,
                  show_buffer_left=400,
                  show_buffer_right=200)
        if select:
            ba.containerwidget(edit=parent,
                               selected_child=btn,
                               visible_child=btn)
        image_width = sclx * 0.85 * 0.75
        self._preview_widget = ba.imagewidget(
            parent=parent,
            draw_controller=btn,
            position=(x + 21 + sclx * 0.5 - image_width * 0.5, y + scly - 104),
            size=(image_width, image_width * 0.5),
            model_transparent=window.lsbt,
            model_opaque=window.lsbo,
            texture=campaign.getlevel(levelname).get_preview_texture(),
            mask_texture=ba.gettexture('mapPreviewMask'))

        translated = campaign.getlevel(levelname).displayname
        self._achievements = (get_achievements_for_coop_level(game))

        self._name_widget = ba.textwidget(parent=parent,
                                          draw_controller=btn,
                                          position=(x + 20 + sclx * 0.5,
                                                    y + scly - 27),
                                          size=(0, 0),
                                          h_align='center',
                                          text=translated,
                                          v_align='center',
                                          maxwidth=sclx * 0.76,
                                          scale=0.85)
        xscl = x + (67 if self._achievements else 50)
        yscl = y + scly - (137 if self._achievements else 157)

        starscale = 35.0 if self._achievements else 45.0

        self._star_widgets: List[ba.Widget] = []
        for _i in range(stars):
            imw = ba.imagewidget(parent=parent,
                                 draw_controller=btn,
                                 position=(xscl, yscl),
                                 size=(starscale, starscale),
                                 texture=window.star_tex)
            self._star_widgets.append(imw)
            xscl += starscale
        for _i in range(3 - stars):
            ba.imagewidget(parent=parent,
                           draw_controller=btn,
                           position=(xscl, yscl),
                           size=(starscale, starscale),
                           color=(0, 0, 0),
                           texture=window.star_tex,
                           opacity=0.3)
            xscl += starscale

        xach = x + 69
        yach = y + scly - 168
        a_scale = 30.0
        self._achievement_widgets: List[Tuple[ba.Widget, ba.Widget]] = []
        for ach in self._achievements:
            a_complete = ach.complete
            imw = ba.imagewidget(
                parent=parent,
                draw_controller=btn,
                position=(xach, yach),
                size=(a_scale, a_scale),
                color=tuple(ach.get_icon_color(a_complete)[:3])
                if a_complete else (1.2, 1.2, 1.2),
                texture=ach.get_icon_texture(a_complete))
            imw2 = ba.imagewidget(parent=parent,
                                  draw_controller=btn,
                                  position=(xach, yach),
                                  size=(a_scale, a_scale),
                                  color=(2, 1.4, 0.4),
                                  texture=window.a_outline_tex,
                                  model_transparent=window.a_outline_model)
            self._achievement_widgets.append((imw, imw2))
            # if a_complete:
            xach += a_scale * 1.2

        # if not unlocked:
        self._lock_widget = ba.imagewidget(parent=parent,
                                           draw_controller=btn,
                                           position=(x - 8 + sclx * 0.5,
                                                     y + scly * 0.5 - 20),
                                           size=(60, 60),
                                           opacity=0.0,
                                           texture=ba.gettexture('lock'))

        # give a quasi-random update increment to spread the load..
        self._update_timer = ba.Timer(0.001 * (900 + random.randrange(200)),
                                      ba.WeakCall(self._update),
                                      repeat=True,
                                      timetype=ba.TimeType.REAL)
        self._update()

    def get_button(self) -> ba.Widget:
        """Return the underlying button ba.Widget."""
        return self._button

    def _update(self) -> None:
        # pylint: disable=too-many-boolean-expressions
        from ba.internal import have_pro, getcampaign
        game = self._game
        campaignname, levelname = game.split(':')

        # Hack - The Last Stand doesn't actually exist in the
        # easy tourney; we just want it for display purposes. Map it to
        # the hard-mode version.
        if game == 'Easy:The Last Stand':
            campaignname = 'Default'

        campaign = getcampaign(campaignname)

        # If this campaign is sequential, make sure we've unlocked
        # everything up to here.
        unlocked = True
        if campaign.sequential:
            for level in campaign.levels:
                if level.name == levelname:
                    break
                if not level.complete:
                    unlocked = False
                    break

        # We never actually allow playing last-stand on easy mode.
        if game == 'Easy:The Last Stand':
            unlocked = False

        # Hard-code games we haven't unlocked.
        if ((game in ('Challenges:Infinite Runaround',
                      'Challenges:Infinite Onslaught') and not have_pro())
                or (game in ('Challenges:Meteor Shower', )
                    and not _ba.get_purchased('games.meteor_shower'))
                or (game in ('Challenges:Target Practice',
                             'Challenges:Target Practice B')
                    and not _ba.get_purchased('games.target_practice'))
                or (game in ('Challenges:Ninja Fight', )
                    and not _ba.get_purchased('games.ninja_fight'))
                or (game in ('Challenges:Pro Ninja Fight', )
                    and not _ba.get_purchased('games.ninja_fight'))
                or (game in ('Challenges:Easter Egg Hunt',
                             'Challenges:Pro Easter Egg Hunt')
                    and not _ba.get_purchased('games.easter_egg_hunt'))):
            unlocked = False

        # Let's tint levels a slightly different color when easy mode
        # is selected.
        unlocked_color = (0.85, 0.95,
                          0.5) if game.startswith('Easy:') else (0.5, 0.7, 0.2)

        ba.buttonwidget(edit=self._button,
                        color=unlocked_color if unlocked else (0.5, 0.5, 0.5))

        ba.imagewidget(edit=self._lock_widget,
                       opacity=0.0 if unlocked else 1.0)
        ba.imagewidget(edit=self._preview_widget,
                       opacity=1.0 if unlocked else 0.3)
        ba.textwidget(edit=self._name_widget,
                      color=(0.8, 1.0, 0.8, 1.0) if unlocked else
                      (0.7, 0.7, 0.7, 0.7))
        for widget in self._star_widgets:
            ba.imagewidget(edit=widget,
                           opacity=1.0 if unlocked else 0.3,
                           color=(2.2, 1.2, 0.3) if unlocked else (1, 1, 1))
        for i, ach in enumerate(self._achievements):
            a_complete = ach.complete
            ba.imagewidget(edit=self._achievement_widgets[i][0],
                           opacity=1.0 if (a_complete and unlocked) else 0.3)
            ba.imagewidget(edit=self._achievement_widgets[i][1],
                           opacity=(1.0 if (a_complete and unlocked) else
                                    0.2 if a_complete else 0.0))
