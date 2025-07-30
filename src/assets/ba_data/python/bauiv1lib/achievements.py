# Released under the MIT License. See LICENSE for details.
#
"""Provides a popup window to view achievements."""

from __future__ import annotations

from typing import override

import bauiv1 as bui


class AchievementsWindow(bui.MainWindow):
    """Popup window to view achievements."""

    def __init__(
        self,
        transition: str | None = 'in_right',
        origin_widget: bui.Widget | None = None,
    ):
        # pylint: disable=too-many-locals
        # pylint: disable=too-many-statements
        # pylint: disable=cyclic-import
        from baclassic import (
            CHEST_APPEARANCE_DISPLAY_INFOS,
            CHEST_APPEARANCE_DISPLAY_INFO_DEFAULT,
        )

        assert bui.app.classic is not None
        uiscale = bui.app.ui_v1.uiscale

        self._width = 700 if uiscale is bui.UIScale.SMALL else 550
        self._height = (
            450
            if uiscale is bui.UIScale.SMALL
            else 370 if uiscale is bui.UIScale.MEDIUM else 450
        )

        # Do some fancy math to fill all available screen area up to the
        # size of our backing container. This lets us fit to the exact
        # screen shape at small ui scale.
        screensize = bui.get_virtual_screen_size()
        scale = (
            2.4
            if uiscale is bui.UIScale.SMALL
            else 1.5 if uiscale is bui.UIScale.MEDIUM else 1.2
        )
        # Calc screen size in our local container space and clamp to a
        # bit smaller than our container size.
        target_width = min(self._width - 60, screensize[0] / scale)
        target_height = min(self._height - 70, screensize[1] / scale)

        # To get top/left coords, go to the center of our window and
        # offset by half the width/height of our target area.
        yoffs = 0.5 * self._height + 0.5 * target_height + 30.0

        scroll_width = target_width
        scroll_height = target_height - 25
        scroll_bottom = yoffs - 54 - scroll_height

        super().__init__(
            root_widget=bui.containerwidget(
                size=(self._width, self._height),
                toolbar_visibility=(
                    # 'menu_minimal'
                    # if uiscale is bui.UIScale.SMALL
                    # else 'menu_full'
                    'menu_full'
                ),
                scale=scale,
            ),
            transition=transition,
            origin_widget=origin_widget,
            # We're affected by screen size only at small ui-scale.
            refresh_on_screen_size_changes=uiscale is bui.UIScale.SMALL,
        )

        if uiscale is bui.UIScale.SMALL:
            bui.containerwidget(
                edit=self._root_widget, on_cancel_call=self.main_window_back
            )
            self._back_button = None
        else:
            self._back_button = bui.buttonwidget(
                parent=self._root_widget,
                autoselect=True,
                position=(50, yoffs - 48),
                size=(60, 60),
                scale=0.6,
                label=bui.charstr(bui.SpecialChar.BACK),
                button_type='backSmall',
                on_activate_call=self.main_window_back,
            )
            bui.containerwidget(
                edit=self._root_widget, cancel_button=self._back_button
            )

        achievements = bui.app.classic.ach.achievements
        num_complete = len([a for a in achievements if a.complete])

        # In small UI mode when the screen is narrow enough we need to
        # go with a smaller title to avoid it overlapping with toolbar
        # bits.
        if uiscale is bui.UIScale.SMALL and target_width < 630:
            self._title_text = bui.textwidget(
                parent=self._root_widget,
                position=(self._width * 0.5, yoffs - 42),
                size=(0, 0),
                h_align='center',
                v_align='center',
                scale=0.6,
                text=bui.Lstr(
                    value='${A}: ${C}/${T}',
                    subs=[
                        ('${A}', bui.Lstr(resource='achievementsText')),
                        ('${C}', str(num_complete)),
                        ('${T}', str(len(achievements))),
                    ],
                ),
                maxwidth=86,
                color=bui.app.ui_v1.title_color,
            )
        else:
            self._title_text = bui.textwidget(
                parent=self._root_widget,
                position=(
                    self._width * 0.5,
                    yoffs - (42 if uiscale is bui.UIScale.SMALL else 30),
                ),
                size=(0, 0),
                h_align='center',
                v_align='center',
                scale=0.6,
                text=bui.Lstr(
                    resource='accountSettingsWindow.achievementProgressText',
                    subs=[
                        ('${COUNT}', str(num_complete)),
                        ('${TOTAL}', str(len(achievements))),
                    ],
                ),
                maxwidth=180,
                color=bui.app.ui_v1.title_color,
            )

        self._scrollwidget = bui.scrollwidget(
            parent=self._root_widget,
            size=(scroll_width, scroll_height),
            position=(self._width * 0.5 - scroll_width * 0.5, scroll_bottom),
            capture_arrows=True,
            simple_culling_v=10,
            border_opacity=0.4,
        )
        bui.widget(edit=self._scrollwidget, autoselect=True)
        if uiscale is bui.UIScale.SMALL:
            bui.widget(
                edit=self._scrollwidget,
                left_widget=bui.get_special_widget('back_button'),
            )

        if uiscale is bui.UIScale.SMALL:
            blotchwidth = 500.0
            blotchheight = 200.0
            bimg = bui.imagewidget(
                parent=self._root_widget,
                texture=bui.gettexture('uiAtlas'),
                mesh_transparent=bui.getmesh('windowBGBlotch'),
                position=(
                    self._width * 0.5
                    - scroll_width * 0.5
                    + 60.0
                    - blotchwidth * 0.5,
                    scroll_bottom - blotchheight * 0.5,
                ),
                size=(blotchwidth, blotchheight),
                color=(0.4, 0.37, 0.49),
                # color=(1, 0, 0),
            )
            bui.widget(edit=bimg, depth_range=(0.9, 1.0))
            bimg = bui.imagewidget(
                parent=self._root_widget,
                texture=bui.gettexture('uiAtlas'),
                mesh_transparent=bui.getmesh('windowBGBlotch'),
                position=(
                    self._width * 0.5
                    + scroll_width * 0.5
                    - 60.0
                    - blotchwidth * 0.5,
                    scroll_bottom - blotchheight * 0.5,
                ),
                size=(blotchwidth, blotchheight),
                color=(0.4, 0.37, 0.49),
                # color=(1, 0, 0),
            )
            bui.widget(edit=bimg, depth_range=(0.9, 1.0))

        bui.containerwidget(
            edit=self._root_widget, cancel_button=self._back_button
        )

        incr = 36
        sub_width = scroll_width - 25
        sub_height = 85 + len(achievements) * incr

        eq_rsrc = 'coopSelectWindow.powerRankingPointsEqualsText'
        pts_rsrc = 'coopSelectWindow.powerRankingPointsText'

        self._subcontainer = bui.containerwidget(
            parent=self._scrollwidget,
            size=(sub_width, sub_height),
            background=False,
        )

        total_pts = 0
        for i, ach in enumerate(achievements):
            complete = ach.complete
            bui.textwidget(
                parent=self._subcontainer,
                position=(sub_width * 0.08 - 5, sub_height - 20 - incr * i),
                maxwidth=20,
                scale=0.5,
                color=(0.6, 0.6, 0.7) if complete else (0.6, 0.6, 0.7, 0.2),
                flatness=1.0,
                shadow=0.0,
                text=str(i + 1),
                size=(0, 0),
                h_align='right',
                v_align='center',
            )

            bui.imagewidget(
                parent=self._subcontainer,
                position=(
                    (sub_width * 0.10 + 1, sub_height - 20 - incr * i - 9)
                    if complete
                    else (sub_width * 0.10 - 4, sub_height - 20 - incr * i - 14)
                ),
                size=(18, 18) if complete else (27, 27),
                opacity=1.0 if complete else 0.3,
                color=ach.get_icon_color(complete)[:3],
                texture=ach.get_icon_ui_texture(complete),
            )
            if complete:
                bui.imagewidget(
                    parent=self._subcontainer,
                    position=(
                        sub_width * 0.10 - 4,
                        sub_height - 25 - incr * i - 9,
                    ),
                    size=(28, 28),
                    color=(2, 1.4, 0),
                    texture=bui.gettexture('achievementOutline'),
                )
            bui.textwidget(
                parent=self._subcontainer,
                position=(sub_width * 0.19, sub_height - 19 - incr * i + 3),
                maxwidth=sub_width * 0.62,
                scale=0.6,
                flatness=1.0,
                shadow=0.0,
                color=(1, 1, 1) if complete else (1, 1, 1, 0.2),
                text=ach.display_name,
                size=(0, 0),
                h_align='left',
                v_align='center',
            )

            bui.textwidget(
                parent=self._subcontainer,
                position=(sub_width * 0.19, sub_height - 19 - incr * i - 10),
                maxwidth=sub_width * 0.62,
                scale=0.4,
                flatness=1.0,
                shadow=0.0,
                color=(0.83, 0.8, 0.85) if complete else (0.8, 0.8, 0.8, 0.2),
                text=(
                    ach.description_full_complete
                    if complete
                    else ach.description_full
                ),
                size=(0, 0),
                h_align='left',
                v_align='center',
            )
            chest_type = ach.get_award_chest_type()
            chestdisplayinfo = CHEST_APPEARANCE_DISPLAY_INFOS.get(
                chest_type, CHEST_APPEARANCE_DISPLAY_INFO_DEFAULT
            )
            chestsize = 24.0
            bui.imagewidget(
                parent=self._subcontainer,
                opacity=0.0 if complete else 1.0,
                position=(
                    sub_width * 0.92 - 40.0 - chestsize * 0.5,
                    sub_height - 20 - incr * i - chestsize * 0.5,
                ),
                size=(chestsize, chestsize),
                color=chestdisplayinfo.color,
                texture=bui.gettexture(chestdisplayinfo.texclosed),
                tint_texture=bui.gettexture(chestdisplayinfo.texclosedtint),
                tint_color=chestdisplayinfo.tint,
                tint2_color=chestdisplayinfo.tint2,
            )

            pts = ach.power_ranking_value
            bui.textwidget(
                parent=self._subcontainer,
                position=(sub_width * 0.92, sub_height - 20 - incr * i),
                maxwidth=sub_width * 0.15,
                color=(0.7, 0.8, 1.0) if complete else (0.9, 0.9, 1.0, 0.3),
                flatness=1.0,
                shadow=0.0,
                scale=0.6,
                text=bui.Lstr(
                    resource=pts_rsrc, subs=[('${NUMBER}', str(pts))]
                ),
                size=(0, 0),
                h_align='center',
                v_align='center',
            )
            if complete:
                total_pts += pts

        bui.textwidget(
            parent=self._subcontainer,
            position=(
                sub_width * 1.0,
                sub_height - 20 - incr * len(achievements),
            ),
            maxwidth=sub_width * 0.5,
            scale=0.7,
            color=(0.7, 0.8, 1.0),
            flatness=1.0,
            shadow=0.0,
            text=bui.Lstr(
                value='${A} ${B}',
                subs=[
                    ('${A}', bui.Lstr(resource='coopSelectWindow.totalText')),
                    (
                        '${B}',
                        bui.Lstr(
                            resource=eq_rsrc,
                            subs=[('${NUMBER}', str(total_pts))],
                        ),
                    ),
                ],
            ),
            size=(0, 0),
            h_align='right',
            v_align='center',
        )

    @override
    def get_main_window_state(self) -> bui.MainWindowState:
        # Support recreating our window for back/refresh purposes.
        cls = type(self)
        return bui.BasicMainWindowState(
            create_call=lambda transition, origin_widget: cls(
                transition=transition, origin_widget=origin_widget
            )
        )
