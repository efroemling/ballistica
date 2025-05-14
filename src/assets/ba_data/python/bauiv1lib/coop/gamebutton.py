# Released under the MIT License. See LICENSE for details.
#
"""Defines button for co-op games."""

from __future__ import annotations

import random
import weakref
from typing import TYPE_CHECKING

import bauiv1 as bui

if TYPE_CHECKING:
    from bauiv1lib.coop.browser import CoopBrowserWindow


class GameButton:
    """Button for entering co-op games."""

    def __init__(
        self,
        window: CoopBrowserWindow,
        parent: bui.Widget,
        game: str,
        x: float,
        y: float,
        select: bool,
        row: str,
    ):
        # pylint: disable=too-many-positional-arguments
        # pylint: disable=too-many-statements
        # pylint: disable=too-many-locals

        assert bui.app.classic is not None
        self._game = game
        sclx = 195.0
        scly = 195.0

        campaignname, levelname = game.split(':')

        # Hack: The Last Stand doesn't actually exist in the easy
        # tourney. We just want it for display purposes. Map it to
        # the hard-mode version.
        if game == 'Easy:The Last Stand':
            campaignname = 'Default'

        rating: float | None
        campaign = bui.app.classic.getcampaign(campaignname)
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

        self._window = weakref.ref(window)
        self._game = game

        self._button = btn = bui.buttonwidget(
            parent=parent,
            position=(x + 23, y + 4),
            size=(sclx, scly),
            label='',
            on_activate_call=self._on_press,
            button_type='square',
            autoselect=True,
            on_select_call=bui.Call(window.sel_change, row, game),
        )
        bui.widget(
            edit=btn,
            show_buffer_bottom=50,
            show_buffer_top=50,
            show_buffer_left=400,
            show_buffer_right=200,
        )
        if select:
            bui.containerwidget(
                edit=parent, selected_child=btn, visible_child=btn
            )
        image_width = sclx * 0.85 * 0.75
        self._preview_widget = bui.imagewidget(
            parent=parent,
            draw_controller=btn,
            position=(x + 21 + sclx * 0.5 - image_width * 0.5, y + scly - 104),
            size=(image_width, image_width * 0.5),
            mesh_transparent=window.lsbt,
            mesh_opaque=window.lsbo,
            texture=bui.gettexture(
                campaign.getlevel(levelname).preview_texture_name
            ),
            mask_texture=bui.gettexture('mapPreviewMask'),
        )

        translated = campaign.getlevel(levelname).displayname
        self._achievements = bui.app.classic.ach.achievements_for_coop_level(
            game
        )

        self._name_widget = bui.textwidget(
            parent=parent,
            draw_controller=btn,
            position=(x + 20 + sclx * 0.5, y + scly - 27),
            size=(0, 0),
            h_align='center',
            text=translated,
            v_align='center',
            maxwidth=sclx * 0.76,
            scale=0.85,
        )
        xscl = x + (67 if self._achievements else 50)
        yscl = y + scly - (137 if self._achievements else 157)

        starscale = 35.0 if self._achievements else 45.0

        self._star_widgets: list[bui.Widget] = []
        for _i in range(stars):
            imw = bui.imagewidget(
                parent=parent,
                draw_controller=btn,
                position=(xscl, yscl),
                size=(starscale, starscale),
                texture=window.star_tex,
            )
            self._star_widgets.append(imw)
            xscl += starscale
        for _i in range(3 - stars):
            bui.imagewidget(
                parent=parent,
                draw_controller=btn,
                position=(xscl, yscl),
                size=(starscale, starscale),
                color=(0, 0, 0),
                texture=window.star_tex,
                opacity=0.3,
            )
            xscl += starscale

        xach = x + 69
        yach = y + scly - 168
        a_scale = 30.0
        self._achievement_widgets: list[tuple[bui.Widget, bui.Widget]] = []
        for ach in self._achievements:
            a_complete = ach.complete
            imw = bui.imagewidget(
                parent=parent,
                draw_controller=btn,
                position=(xach, yach),
                size=(a_scale, a_scale),
                color=(
                    tuple(ach.get_icon_color(a_complete)[:3])
                    if a_complete
                    else (1.2, 1.2, 1.2)
                ),
                texture=ach.get_icon_ui_texture(a_complete),
            )
            imw2 = bui.imagewidget(
                parent=parent,
                draw_controller=btn,
                position=(xach, yach),
                size=(a_scale, a_scale),
                color=(2, 1.4, 0.4),
                texture=window.a_outline_tex,
                mesh_transparent=window.a_outline_mesh,
            )
            self._achievement_widgets.append((imw, imw2))
            # if a_complete:
            xach += a_scale * 1.2

        # if not unlocked:
        self._lock_widget = bui.imagewidget(
            parent=parent,
            draw_controller=btn,
            position=(x - 8 + sclx * 0.5, y + scly * 0.5 - 20),
            size=(60, 60),
            opacity=0.0,
            texture=bui.gettexture('lock'),
        )

        # give a quasi-random update increment to spread the load..
        self._update_timer = bui.AppTimer(
            0.001 * (900 + random.randrange(200)),
            bui.WeakCall(self._update),
            repeat=True,
        )
        self._update()

    def _on_press(self) -> None:
        window = self._window()
        if window is not None:
            window.run_game(self._game, origin_widget=self._button)

    def get_button(self) -> bui.Widget:
        """Return the underlying button bui.Widget."""
        return self._button

    def _update(self) -> None:

        plus = bui.app.plus
        assert plus is not None

        classic = bui.app.classic
        assert classic is not None

        # In case we stick around after our UI...
        if not self._button:
            return

        game = self._game
        campaignname, levelname = game.split(':')

        # Hack - The Last Stand doesn't actually exist in the
        # easy tourney; we just want it for display purposes. Map it to
        # the hard-mode version.
        if game == 'Easy:The Last Stand':
            campaignname = 'Default'

        campaign = classic.getcampaign(campaignname)

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
        assert bui.app.classic is not None
        if not bui.app.classic.is_game_unlocked(game):
            unlocked = False

        # Let's tint levels a slightly different color when easy mode
        # is selected.
        unlocked_color = (
            (0.85, 0.95, 0.5) if game.startswith('Easy:') else (0.5, 0.7, 0.2)
        )

        bui.buttonwidget(
            edit=self._button,
            color=unlocked_color if unlocked else (0.5, 0.5, 0.5),
        )

        bui.imagewidget(
            edit=self._lock_widget, opacity=0.0 if unlocked else 1.0
        )
        bui.imagewidget(
            edit=self._preview_widget, opacity=1.0 if unlocked else 0.3
        )
        bui.textwidget(
            edit=self._name_widget,
            color=(0.8, 1.0, 0.8, 1.0) if unlocked else (0.7, 0.7, 0.7, 0.7),
        )
        for widget in self._star_widgets:
            bui.imagewidget(
                edit=widget,
                opacity=1.0 if unlocked else 0.3,
                color=(2.2, 1.2, 0.3) if unlocked else (1, 1, 1),
            )
        for i, ach in enumerate(self._achievements):
            a_complete = ach.complete
            bui.imagewidget(
                edit=self._achievement_widgets[i][0],
                opacity=1.0 if (a_complete and unlocked) else 0.3,
            )
            bui.imagewidget(
                edit=self._achievement_widgets[i][1],
                opacity=(
                    1.0
                    if (a_complete and unlocked)
                    else 0.2 if a_complete else 0.0
                ),
            )
