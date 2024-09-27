# Released under the MIT License. See LICENSE for details.
#
"""Provides a popup window to view achievements."""

from __future__ import annotations

from typing import override

# from bauiv1lib.popup import PopupWindow
import bauiv1 as bui


class InboxWindow(bui.MainWindow):
    """Popup window to show account messages."""

    def __init__(
        self,
        transition: str | None = 'in_right',
        origin_widget: bui.Widget | None = None,
    ):
        assert bui.app.classic is not None
        uiscale = bui.app.ui_v1.uiscale
        self._width = 600 if uiscale is bui.UIScale.SMALL else 450
        self._height = (
            380
            if uiscale is bui.UIScale.SMALL
            else 370 if uiscale is bui.UIScale.MEDIUM else 450
        )
        yoffs = -45 if uiscale is bui.UIScale.SMALL else 0

        super().__init__(
            root_widget=bui.containerwidget(
                size=(self._width, self._height),
                toolbar_visibility=(
                    'menu_minimal'
                    if uiscale is bui.UIScale.SMALL
                    else 'menu_full'
                ),
                scale=(
                    2.3
                    if uiscale is bui.UIScale.SMALL
                    else 1.65 if uiscale is bui.UIScale.MEDIUM else 1.23
                ),
                stack_offset=(
                    (0, 0)
                    if uiscale is bui.UIScale.SMALL
                    else (0, 0) if uiscale is bui.UIScale.MEDIUM else (0, 0)
                ),
            ),
            transition=transition,
            origin_widget=origin_widget,
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
                position=(50, self._height - 38 + yoffs),
                size=(60, 60),
                scale=0.6,
                label=bui.charstr(bui.SpecialChar.BACK),
                button_type='backSmall',
                on_activate_call=self.main_window_back,
            )
            bui.containerwidget(
                edit=self._root_widget, cancel_button=self._back_button
            )

        self._title_text = bui.textwidget(
            parent=self._root_widget,
            position=(
                self._width * 0.5,
                self._height
                - (27 if uiscale is bui.UIScale.SMALL else 20)
                + yoffs,
            ),
            size=(0, 0),
            h_align='center',
            v_align='center',
            scale=0.6,
            text='INBOX (UNDER CONSTRUCTION)',
            maxwidth=200,
            color=bui.app.ui_v1.title_color,
        )

        self._scrollwidget = bui.scrollwidget(
            parent=self._root_widget,
            size=(
                self._width - 60,
                self._height - (150 if uiscale is bui.UIScale.SMALL else 70),
            ),
            position=(
                30,
                (110 if uiscale is bui.UIScale.SMALL else 30) + yoffs,
            ),
            capture_arrows=True,
            simple_culling_v=10,
        )
        bui.widget(edit=self._scrollwidget, autoselect=True)
        if uiscale is bui.UIScale.SMALL:
            bui.widget(
                edit=self._scrollwidget,
                left_widget=bui.get_special_widget('back_button'),
            )

        bui.containerwidget(
            edit=self._root_widget, cancel_button=self._back_button
        )

        entries: list[str] = []
        incr = 20
        sub_width = self._width - 90
        sub_height = 40 + len(entries) * incr

        self._subcontainer = bui.containerwidget(
            parent=self._scrollwidget,
            size=(sub_width, sub_height),
            background=False,
        )

        for i, entry in enumerate(entries):
            bui.textwidget(
                parent=self._subcontainer,
                position=(sub_width * 0.08 - 5, sub_height - 20 - incr * i),
                maxwidth=20,
                scale=0.5,
                flatness=1.0,
                shadow=0.0,
                text=entry,
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

    # def _on_cancel_press(self) -> None:
    #     self._transition_out()

    # def _transition_out(self) -> None:
    #     if not self._transitioning_out:
    #         self._transitioning_out = True
    #         bui.containerwidget(
    # edit=self._root_widget, transition='out_scale')

    # @override
    # def on_popup_cancel(self) -> None:
    #     bui.getsound('swish').play()
    #     self._transition_out()
