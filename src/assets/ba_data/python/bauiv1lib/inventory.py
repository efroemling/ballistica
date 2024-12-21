# Released under the MIT License. See LICENSE for details.
#
"""Provides help related ui."""

from __future__ import annotations

from typing import override

import bauiv1 as bui


class InventoryWindow(bui.MainWindow):
    """Shows what you got."""

    def __init__(
        self,
        transition: str | None = 'in_right',
        origin_widget: bui.Widget | None = None,
    ):

        bui.set_analytics_screen('Help Window')

        assert bui.app.classic is not None
        uiscale = bui.app.ui_v1.uiscale
        width = 1050 if uiscale is bui.UIScale.SMALL else 750
        height = (
            500
            if uiscale is bui.UIScale.SMALL
            else 530 if uiscale is bui.UIScale.MEDIUM else 600
        )
        xoffs = 70 if uiscale is bui.UIScale.SMALL else 0
        yoffs = -45 if uiscale is bui.UIScale.SMALL else 0

        super().__init__(
            root_widget=bui.containerwidget(
                size=(width, height),
                toolbar_visibility=(
                    'menu_minimal'
                    if uiscale is bui.UIScale.SMALL
                    else 'menu_full'
                ),
                scale=(
                    1.55
                    if uiscale is bui.UIScale.SMALL
                    else 1.15 if uiscale is bui.UIScale.MEDIUM else 1.0
                ),
                stack_offset=(
                    (0, 0)
                    if uiscale is bui.UIScale.SMALL
                    else (0, 15) if uiscale is bui.UIScale.MEDIUM else (0, 0)
                ),
            ),
            transition=transition,
            origin_widget=origin_widget,
        )

        bui.textwidget(
            parent=self._root_widget,
            position=(0, height - 45 + yoffs),
            size=(width, 25),
            text='INVENTORY',
            color=bui.app.ui_v1.title_color,
            h_align='center',
            v_align='center',
        )

        if uiscale is bui.UIScale.SMALL:
            bui.containerwidget(
                edit=self._root_widget, on_cancel_call=self.main_window_back
            )
        else:
            btn = bui.buttonwidget(
                parent=self._root_widget,
                position=(xoffs + 50, height - 55 + yoffs),
                size=(60, 55),
                scale=0.8,
                label=bui.charstr(bui.SpecialChar.BACK),
                button_type='backSmall',
                extra_touch_border_scale=2.0,
                autoselect=True,
                on_activate_call=self.main_window_back,
            )
            bui.containerwidget(edit=self._root_widget, cancel_button=btn)

        bui.textwidget(
            parent=self._root_widget,
            position=(0, height - 120 + yoffs),
            size=(width, 25),
            text='(under construction)',
            scale=0.7,
            h_align='center',
            v_align='center',
        )

        button_width = 300
        self._player_profiles_button = btn = bui.buttonwidget(
            parent=self._root_widget,
            position=((width - button_width) * 0.5, height - 200 + yoffs),
            autoselect=True,
            size=(button_width, 60),
            label=bui.Lstr(resource='playerProfilesWindow.titleText'),
            color=(0.55, 0.5, 0.6),
            icon=bui.gettexture('cuteSpaz'),
            textcolor=(0.75, 0.7, 0.8),
            on_activate_call=self._player_profiles_press,
        )

    def _player_profiles_press(self) -> None:
        # pylint: disable=cyclic-import
        from bauiv1lib.profile.browser import ProfileBrowserWindow

        # no-op if our underlying widget is dead or on its way out.
        if not self._root_widget or self._root_widget.transitioning_out:
            return

        self.main_window_replace(
            ProfileBrowserWindow(origin_widget=self._player_profiles_button)
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
