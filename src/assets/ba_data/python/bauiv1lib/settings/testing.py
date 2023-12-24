# Released under the MIT License. See LICENSE for details.
#
"""Provides UI for test settings."""

from __future__ import annotations

import copy
from typing import TYPE_CHECKING

import bauiv1 as bui

if TYPE_CHECKING:
    from typing import Any, Callable


class TestingWindow(bui.Window):
    """Window for conveniently testing various settings."""

    def __init__(
        self,
        title: bui.Lstr,
        entries: list[dict[str, Any]],
        transition: str = 'in_right',
        back_call: Callable[[], bui.Window] | None = None,
    ):
        assert bui.app.classic is not None
        uiscale = bui.app.ui_v1.uiscale
        self._width = 600
        self._height = 324 if uiscale is bui.UIScale.SMALL else 400
        self._entries = copy.deepcopy(entries)
        self._back_call = back_call
        super().__init__(
            root_widget=bui.containerwidget(
                size=(self._width, self._height),
                transition=transition,
                scale=(
                    2.5
                    if uiscale is bui.UIScale.SMALL
                    else 1.2
                    if uiscale is bui.UIScale.MEDIUM
                    else 1.0
                ),
                stack_offset=(0, -28)
                if uiscale is bui.UIScale.SMALL
                else (0, 0),
            )
        )
        self._back_button = btn = bui.buttonwidget(
            parent=self._root_widget,
            autoselect=True,
            position=(65, self._height - 59),
            size=(130, 60),
            scale=0.8,
            text_scale=1.2,
            label=bui.Lstr(resource='backText'),
            button_type='back',
            on_activate_call=self._do_back,
        )
        bui.textwidget(
            parent=self._root_widget,
            position=(self._width * 0.5, self._height - 35),
            size=(0, 0),
            color=bui.app.ui_v1.title_color,
            h_align='center',
            v_align='center',
            maxwidth=245,
            text=title,
        )

        bui.buttonwidget(
            edit=self._back_button,
            button_type='backSmall',
            size=(60, 60),
            label=bui.charstr(bui.SpecialChar.BACK),
        )

        bui.textwidget(
            parent=self._root_widget,
            position=(self._width * 0.5, self._height - 75),
            size=(0, 0),
            color=bui.app.ui_v1.infotextcolor,
            h_align='center',
            v_align='center',
            maxwidth=self._width * 0.75,
            text=bui.Lstr(resource='settingsWindowAdvanced.forTestingText'),
        )
        bui.containerwidget(edit=self._root_widget, cancel_button=btn)
        self._scroll_width = self._width - 130
        self._scroll_height = self._height - 140
        self._scrollwidget = bui.scrollwidget(
            parent=self._root_widget,
            size=(self._scroll_width, self._scroll_height),
            highlight=False,
            position=((self._width - self._scroll_width) * 0.5, 40),
        )
        bui.containerwidget(edit=self._scrollwidget, claims_left_right=True)

        self._spacing = 50

        self._sub_width = self._scroll_width * 0.95
        self._sub_height = 50 + len(self._entries) * self._spacing + 60
        self._subcontainer = bui.containerwidget(
            parent=self._scrollwidget,
            size=(self._sub_width, self._sub_height),
            background=False,
        )

        h = 230
        v = self._sub_height - 48

        for i, entry in enumerate(self._entries):
            entry_name = entry['name']

            # If we haven't yet, record the default value for this name so
            # we can reset if we want..
            if entry_name not in bui.app.classic.value_test_defaults:
                bui.app.classic.value_test_defaults[
                    entry_name
                ] = bui.app.classic.value_test(entry_name)

            bui.textwidget(
                parent=self._subcontainer,
                position=(h, v),
                size=(0, 0),
                h_align='right',
                v_align='center',
                maxwidth=200,
                text=entry['label'],
            )
            btn = bui.buttonwidget(
                parent=self._subcontainer,
                position=(h + 20, v - 19),
                size=(40, 40),
                autoselect=True,
                repeat=True,
                left_widget=self._back_button,
                button_type='square',
                label='-',
                on_activate_call=bui.Call(self._on_minus_press, entry['name']),
            )
            if i == 0:
                bui.widget(edit=btn, up_widget=self._back_button)
            # pylint: disable=consider-using-f-string
            entry['widget'] = bui.textwidget(
                parent=self._subcontainer,
                position=(h + 100, v),
                size=(0, 0),
                h_align='center',
                v_align='center',
                maxwidth=60,
                text='%.4g' % bui.app.classic.value_test(entry_name),
            )
            btn = bui.buttonwidget(
                parent=self._subcontainer,
                position=(h + 140, v - 19),
                size=(40, 40),
                autoselect=True,
                repeat=True,
                button_type='square',
                label='+',
                on_activate_call=bui.Call(self._on_plus_press, entry['name']),
            )
            if i == 0:
                bui.widget(edit=btn, up_widget=self._back_button)
            v -= self._spacing
        v -= 35
        bui.buttonwidget(
            parent=self._subcontainer,
            autoselect=True,
            size=(200, 50),
            position=(self._sub_width * 0.5 - 100, v),
            label=bui.Lstr(resource='settingsWindowAdvanced.resetText'),
            right_widget=btn,
            on_activate_call=self._on_reset_press,
        )

    def _get_entry(self, name: str) -> dict[str, Any]:
        for entry in self._entries:
            if entry['name'] == name:
                return entry
        raise bui.NotFoundError(f'Entry not found: {name}')

    def _on_reset_press(self) -> None:
        assert bui.app.classic is not None
        for entry in self._entries:
            bui.app.classic.value_test(
                entry['name'],
                absolute=bui.app.classic.value_test_defaults[entry['name']],
            )
            # pylint: disable=consider-using-f-string
            bui.textwidget(
                edit=entry['widget'],
                text='%.4g' % bui.app.classic.value_test(entry['name']),
            )

    def _on_minus_press(self, entry_name: str) -> None:
        assert bui.app.classic is not None
        entry = self._get_entry(entry_name)
        bui.app.classic.value_test(entry['name'], change=-entry['increment'])
        # pylint: disable=consider-using-f-string
        bui.textwidget(
            edit=entry['widget'],
            text='%.4g' % bui.app.classic.value_test(entry['name']),
        )

    def _on_plus_press(self, entry_name: str) -> None:
        assert bui.app.classic is not None
        entry = self._get_entry(entry_name)
        bui.app.classic.value_test(entry['name'], change=entry['increment'])
        # pylint: disable=consider-using-f-string
        bui.textwidget(
            edit=entry['widget'],
            text='%.4g' % bui.app.classic.value_test(entry['name']),
        )

    def _do_back(self) -> None:
        # pylint: disable=cyclic-import
        from bauiv1lib.settings.advanced import AdvancedSettingsWindow

        # no-op if our underlying widget is dead or on its way out.
        if not self._root_widget or self._root_widget.transitioning_out:
            return

        bui.containerwidget(edit=self._root_widget, transition='out_right')
        backwin = (
            self._back_call()
            if self._back_call is not None
            else AdvancedSettingsWindow(transition='in_left')
        )
        assert bui.app.classic is not None
        bui.app.ui_v1.set_main_menu_window(
            backwin.get_root_widget(), from_window=self._root_widget
        )
