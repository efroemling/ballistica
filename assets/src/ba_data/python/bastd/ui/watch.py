# Released under the MIT License. See LICENSE for details.
#
"""Provides UI functionality for watching replays."""

from __future__ import annotations

import os
from enum import Enum
from typing import TYPE_CHECKING, cast

import ba
import ba.internal

if TYPE_CHECKING:
    from typing import Any


class WatchWindow(ba.Window):
    """Window for watching replays."""

    class TabID(Enum):
        """Our available tab types."""

        MY_REPLAYS = 'my_replays'
        TEST_TAB = 'test_tab'

    def __init__(
        self,
        transition: str | None = 'in_right',
        origin_widget: ba.Widget | None = None,
    ):
        # pylint: disable=too-many-locals
        # pylint: disable=too-many-statements
        from bastd.ui.tabs import TabRow

        ba.set_analytics_screen('Watch Window')
        scale_origin: tuple[float, float] | None
        if origin_widget is not None:
            self._transition_out = 'out_scale'
            scale_origin = origin_widget.get_screen_space_center()
            transition = 'in_scale'
        else:
            self._transition_out = 'out_right'
            scale_origin = None
        ba.app.ui.set_main_menu_location('Watch')
        self._tab_data: dict[str, Any] = {}
        self._my_replays_scroll_width: float | None = None
        self._my_replays_watch_replay_button: ba.Widget | None = None
        self._scrollwidget: ba.Widget | None = None
        self._columnwidget: ba.Widget | None = None
        self._my_replay_selected: str | None = None
        self._my_replays_rename_window: ba.Widget | None = None
        self._my_replay_rename_text: ba.Widget | None = None
        self._r = 'watchWindow'
        uiscale = ba.app.ui.uiscale
        self._width = 1240 if uiscale is ba.UIScale.SMALL else 1040
        x_inset = 100 if uiscale is ba.UIScale.SMALL else 0
        self._height = (
            578
            if uiscale is ba.UIScale.SMALL
            else 670
            if uiscale is ba.UIScale.MEDIUM
            else 800
        )
        self._current_tab: WatchWindow.TabID | None = None
        extra_top = 20 if uiscale is ba.UIScale.SMALL else 0

        super().__init__(
            root_widget=ba.containerwidget(
                size=(self._width, self._height + extra_top),
                transition=transition,
                toolbar_visibility='menu_minimal',
                scale_origin_stack_offset=scale_origin,
                scale=(
                    1.3
                    if uiscale is ba.UIScale.SMALL
                    else 0.97
                    if uiscale is ba.UIScale.MEDIUM
                    else 0.8
                ),
                stack_offset=(0, -10)
                if uiscale is ba.UIScale.SMALL
                else (0, 15)
                if uiscale is ba.UIScale.MEDIUM
                else (0, 0),
            )
        )

        if uiscale is ba.UIScale.SMALL and ba.app.ui.use_toolbars:
            ba.containerwidget(
                edit=self._root_widget, on_cancel_call=self._back
            )
            self._back_button = None
        else:
            self._back_button = btn = ba.buttonwidget(
                parent=self._root_widget,
                autoselect=True,
                position=(70 + x_inset, self._height - 74),
                size=(140, 60),
                scale=1.1,
                label=ba.Lstr(resource='backText'),
                button_type='back',
                on_activate_call=self._back,
            )
            ba.containerwidget(edit=self._root_widget, cancel_button=btn)
            ba.buttonwidget(
                edit=btn,
                button_type='backSmall',
                size=(60, 60),
                label=ba.charstr(ba.SpecialChar.BACK),
            )

        ba.textwidget(
            parent=self._root_widget,
            position=(self._width * 0.5, self._height - 38),
            size=(0, 0),
            color=ba.app.ui.title_color,
            scale=1.5,
            h_align='center',
            v_align='center',
            text=ba.Lstr(resource=self._r + '.titleText'),
            maxwidth=400,
        )

        tabdefs = [
            (
                self.TabID.MY_REPLAYS,
                ba.Lstr(resource=self._r + '.myReplaysText'),
            ),
            # (self.TabID.TEST_TAB, ba.Lstr(value='Testing')),
        ]

        scroll_buffer_h = 130 + 2 * x_inset
        tab_buffer_h = 750 + 2 * x_inset

        self._tab_row = TabRow(
            self._root_widget,
            tabdefs,
            pos=(tab_buffer_h * 0.5, self._height - 130),
            size=(self._width - tab_buffer_h, 50),
            on_select_call=self._set_tab,
        )

        if ba.app.ui.use_toolbars:
            first_tab = self._tab_row.tabs[tabdefs[0][0]]
            last_tab = self._tab_row.tabs[tabdefs[-1][0]]
            ba.widget(
                edit=last_tab.button,
                right_widget=ba.internal.get_special_widget('party_button'),
            )
            if uiscale is ba.UIScale.SMALL:
                bbtn = ba.internal.get_special_widget('back_button')
                ba.widget(
                    edit=first_tab.button, up_widget=bbtn, left_widget=bbtn
                )

        self._scroll_width = self._width - scroll_buffer_h
        self._scroll_height = self._height - 180

        # Not actually using a scroll widget anymore; just an image.
        scroll_left = (self._width - self._scroll_width) * 0.5
        scroll_bottom = self._height - self._scroll_height - 79 - 48
        buffer_h = 10
        buffer_v = 4
        ba.imagewidget(
            parent=self._root_widget,
            position=(scroll_left - buffer_h, scroll_bottom - buffer_v),
            size=(
                self._scroll_width + 2 * buffer_h,
                self._scroll_height + 2 * buffer_v,
            ),
            texture=ba.gettexture('scrollWidget'),
            model_transparent=ba.getmodel('softEdgeOutside'),
        )
        self._tab_container: ba.Widget | None = None

        self._restore_state()

    def _set_tab(self, tab_id: TabID) -> None:
        # pylint: disable=too-many-locals

        if self._current_tab == tab_id:
            return
        self._current_tab = tab_id

        # Preserve our current tab between runs.
        cfg = ba.app.config
        cfg['Watch Tab'] = tab_id.value
        cfg.commit()

        # Update tab colors based on which is selected.
        # tabs.update_tab_button_colors(self._tab_buttons, tab)
        self._tab_row.update_appearance(tab_id)

        if self._tab_container:
            self._tab_container.delete()
        scroll_left = (self._width - self._scroll_width) * 0.5
        scroll_bottom = self._height - self._scroll_height - 79 - 48

        # A place where tabs can store data to get cleared when
        # switching to a different tab
        self._tab_data = {}

        uiscale = ba.app.ui.uiscale
        if tab_id is self.TabID.MY_REPLAYS:
            c_width = self._scroll_width
            c_height = self._scroll_height - 20
            sub_scroll_height = c_height - 63
            self._my_replays_scroll_width = sub_scroll_width = (
                680 if uiscale is ba.UIScale.SMALL else 640
            )

            self._tab_container = cnt = ba.containerwidget(
                parent=self._root_widget,
                position=(
                    scroll_left,
                    scroll_bottom + (self._scroll_height - c_height) * 0.5,
                ),
                size=(c_width, c_height),
                background=False,
                selection_loops_to_parent=True,
            )

            v = c_height - 30
            ba.textwidget(
                parent=cnt,
                position=(c_width * 0.5, v),
                color=(0.6, 1.0, 0.6),
                scale=0.7,
                size=(0, 0),
                maxwidth=c_width * 0.9,
                h_align='center',
                v_align='center',
                text=ba.Lstr(
                    resource='replayRenameWarningText',
                    subs=[
                        ('${REPLAY}', ba.Lstr(resource='replayNameDefaultText'))
                    ],
                ),
            )

            b_width = 140 if uiscale is ba.UIScale.SMALL else 178
            b_height = (
                107
                if uiscale is ba.UIScale.SMALL
                else 142
                if uiscale is ba.UIScale.MEDIUM
                else 190
            )
            b_space_extra = (
                0
                if uiscale is ba.UIScale.SMALL
                else -2
                if uiscale is ba.UIScale.MEDIUM
                else -5
            )

            b_color = (0.6, 0.53, 0.63)
            b_textcolor = (0.75, 0.7, 0.8)
            btnv = (
                c_height
                - (
                    48
                    if uiscale is ba.UIScale.SMALL
                    else 45
                    if uiscale is ba.UIScale.MEDIUM
                    else 40
                )
                - b_height
            )
            btnh = 40 if uiscale is ba.UIScale.SMALL else 40
            smlh = 190 if uiscale is ba.UIScale.SMALL else 225
            tscl = 1.0 if uiscale is ba.UIScale.SMALL else 1.2
            self._my_replays_watch_replay_button = btn1 = ba.buttonwidget(
                parent=cnt,
                size=(b_width, b_height),
                position=(btnh, btnv),
                button_type='square',
                color=b_color,
                textcolor=b_textcolor,
                on_activate_call=self._on_my_replay_play_press,
                text_scale=tscl,
                label=ba.Lstr(resource=self._r + '.watchReplayButtonText'),
                autoselect=True,
            )
            ba.widget(edit=btn1, up_widget=self._tab_row.tabs[tab_id].button)
            if uiscale is ba.UIScale.SMALL and ba.app.ui.use_toolbars:
                ba.widget(
                    edit=btn1,
                    left_widget=ba.internal.get_special_widget('back_button'),
                )
            btnv -= b_height + b_space_extra
            ba.buttonwidget(
                parent=cnt,
                size=(b_width, b_height),
                position=(btnh, btnv),
                button_type='square',
                color=b_color,
                textcolor=b_textcolor,
                on_activate_call=self._on_my_replay_rename_press,
                text_scale=tscl,
                label=ba.Lstr(resource=self._r + '.renameReplayButtonText'),
                autoselect=True,
            )
            btnv -= b_height + b_space_extra
            ba.buttonwidget(
                parent=cnt,
                size=(b_width, b_height),
                position=(btnh, btnv),
                button_type='square',
                color=b_color,
                textcolor=b_textcolor,
                on_activate_call=self._on_my_replay_delete_press,
                text_scale=tscl,
                label=ba.Lstr(resource=self._r + '.deleteReplayButtonText'),
                autoselect=True,
            )

            v -= sub_scroll_height + 23
            self._scrollwidget = scrlw = ba.scrollwidget(
                parent=cnt,
                position=(smlh, v),
                size=(sub_scroll_width, sub_scroll_height),
            )
            ba.containerwidget(edit=cnt, selected_child=scrlw)
            self._columnwidget = ba.columnwidget(
                parent=scrlw, left_border=10, border=2, margin=0
            )

            ba.widget(
                edit=scrlw,
                autoselect=True,
                left_widget=btn1,
                up_widget=self._tab_row.tabs[tab_id].button,
            )
            ba.widget(edit=self._tab_row.tabs[tab_id].button, down_widget=scrlw)

            self._my_replay_selected = None
            self._refresh_my_replays()

    def _no_replay_selected_error(self) -> None:
        ba.screenmessage(
            ba.Lstr(resource=self._r + '.noReplaySelectedErrorText'),
            color=(1, 0, 0),
        )
        ba.playsound(ba.getsound('error'))

    def _on_my_replay_play_press(self) -> None:
        if self._my_replay_selected is None:
            self._no_replay_selected_error()
            return
        ba.internal.increment_analytics_count('Replay watch')

        def do_it() -> None:
            try:
                # Reset to normal speed.
                ba.internal.set_replay_speed_exponent(0)
                ba.internal.fade_screen(True)
                assert self._my_replay_selected is not None
                ba.internal.new_replay_session(
                    ba.internal.get_replays_dir()
                    + '/'
                    + self._my_replay_selected
                )
            except Exception:
                ba.print_exception('Error running replay session.')

                # Drop back into a fresh main menu session
                # in case we half-launched or something.
                from bastd import mainmenu

                ba.internal.new_host_session(mainmenu.MainMenuSession)

        ba.internal.fade_screen(False, endcall=ba.Call(ba.pushcall, do_it))
        ba.containerwidget(edit=self._root_widget, transition='out_left')

    def _on_my_replay_rename_press(self) -> None:
        if self._my_replay_selected is None:
            self._no_replay_selected_error()
            return
        c_width = 600
        c_height = 250
        uiscale = ba.app.ui.uiscale
        self._my_replays_rename_window = cnt = ba.containerwidget(
            scale=(
                1.8
                if uiscale is ba.UIScale.SMALL
                else 1.55
                if uiscale is ba.UIScale.MEDIUM
                else 1.0
            ),
            size=(c_width, c_height),
            transition='in_scale',
        )
        dname = self._get_replay_display_name(self._my_replay_selected)
        ba.textwidget(
            parent=cnt,
            size=(0, 0),
            h_align='center',
            v_align='center',
            text=ba.Lstr(
                resource=self._r + '.renameReplayText',
                subs=[('${REPLAY}', dname)],
            ),
            maxwidth=c_width * 0.8,
            position=(c_width * 0.5, c_height - 60),
        )
        self._my_replay_rename_text = txt = ba.textwidget(
            parent=cnt,
            size=(c_width * 0.8, 40),
            h_align='left',
            v_align='center',
            text=dname,
            editable=True,
            description=ba.Lstr(resource=self._r + '.replayNameText'),
            position=(c_width * 0.1, c_height - 140),
            autoselect=True,
            maxwidth=c_width * 0.7,
            max_chars=200,
        )
        cbtn = ba.buttonwidget(
            parent=cnt,
            label=ba.Lstr(resource='cancelText'),
            on_activate_call=ba.Call(
                lambda c: ba.containerwidget(edit=c, transition='out_scale'),
                cnt,
            ),
            size=(180, 60),
            position=(30, 30),
            autoselect=True,
        )
        okb = ba.buttonwidget(
            parent=cnt,
            label=ba.Lstr(resource=self._r + '.renameText'),
            size=(180, 60),
            position=(c_width - 230, 30),
            on_activate_call=ba.Call(
                self._rename_my_replay, self._my_replay_selected
            ),
            autoselect=True,
        )
        ba.widget(edit=cbtn, right_widget=okb)
        ba.widget(edit=okb, left_widget=cbtn)
        ba.textwidget(edit=txt, on_return_press_call=okb.activate)
        ba.containerwidget(edit=cnt, cancel_button=cbtn, start_button=okb)

    def _rename_my_replay(self, replay: str) -> None:
        new_name = None
        try:
            if not self._my_replay_rename_text:
                return
            new_name_raw = cast(
                str, ba.textwidget(query=self._my_replay_rename_text)
            )
            new_name = new_name_raw + '.brp'

            # Ignore attempts to change it to what it already is
            # (or what it looks like to the user).
            if (
                replay != new_name
                and self._get_replay_display_name(replay) != new_name_raw
            ):
                old_name_full = (
                    ba.internal.get_replays_dir() + '/' + replay
                ).encode('utf-8')
                new_name_full = (
                    ba.internal.get_replays_dir() + '/' + new_name
                ).encode('utf-8')
                # False alarm; ba.textwidget can return non-None val.
                # pylint: disable=unsupported-membership-test
                if os.path.exists(new_name_full):
                    ba.playsound(ba.getsound('error'))
                    ba.screenmessage(
                        ba.Lstr(
                            resource=self._r
                            + '.replayRenameErrorAlreadyExistsText'
                        ),
                        color=(1, 0, 0),
                    )
                elif any(char in new_name_raw for char in ['/', '\\', ':']):
                    ba.playsound(ba.getsound('error'))
                    ba.screenmessage(
                        ba.Lstr(
                            resource=self._r + '.replayRenameErrorInvalidName'
                        ),
                        color=(1, 0, 0),
                    )
                else:
                    ba.internal.increment_analytics_count('Replay rename')
                    os.rename(old_name_full, new_name_full)
                    self._refresh_my_replays()
                    ba.playsound(ba.getsound('gunCocking'))
        except Exception:
            ba.print_exception(
                f"Error renaming replay '{replay}' to '{new_name}'."
            )
            ba.playsound(ba.getsound('error'))
            ba.screenmessage(
                ba.Lstr(resource=self._r + '.replayRenameErrorText'),
                color=(1, 0, 0),
            )

        ba.containerwidget(
            edit=self._my_replays_rename_window, transition='out_scale'
        )

    def _on_my_replay_delete_press(self) -> None:
        from bastd.ui import confirm

        if self._my_replay_selected is None:
            self._no_replay_selected_error()
            return
        confirm.ConfirmWindow(
            ba.Lstr(
                resource=self._r + '.deleteConfirmText',
                subs=[
                    (
                        '${REPLAY}',
                        self._get_replay_display_name(self._my_replay_selected),
                    )
                ],
            ),
            ba.Call(self._delete_replay, self._my_replay_selected),
            450,
            150,
        )

    def _get_replay_display_name(self, replay: str) -> str:
        if replay.endswith('.brp'):
            replay = replay[:-4]
        if replay == '__lastReplay':
            return ba.Lstr(resource='replayNameDefaultText').evaluate()
        return replay

    def _delete_replay(self, replay: str) -> None:
        try:
            ba.internal.increment_analytics_count('Replay delete')
            os.remove(
                (ba.internal.get_replays_dir() + '/' + replay).encode('utf-8')
            )
            self._refresh_my_replays()
            ba.playsound(ba.getsound('shieldDown'))
            if replay == self._my_replay_selected:
                self._my_replay_selected = None
        except Exception:
            ba.print_exception(f"Error deleting replay '{replay}'.")
            ba.playsound(ba.getsound('error'))
            ba.screenmessage(
                ba.Lstr(resource=self._r + '.replayDeleteErrorText'),
                color=(1, 0, 0),
            )

    def _on_my_replay_select(self, replay: str) -> None:
        self._my_replay_selected = replay

    def _refresh_my_replays(self) -> None:
        assert self._columnwidget is not None
        for child in self._columnwidget.get_children():
            child.delete()
        t_scale = 1.6
        try:
            names = os.listdir(ba.internal.get_replays_dir())

            # Ignore random other files in there.
            names = [n for n in names if n.endswith('.brp')]
            names.sort(key=lambda x: x.lower())
        except Exception:
            ba.print_exception('Error listing replays dir.')
            names = []

        assert self._my_replays_scroll_width is not None
        assert self._my_replays_watch_replay_button is not None
        for i, name in enumerate(names):
            txt = ba.textwidget(
                parent=self._columnwidget,
                size=(self._my_replays_scroll_width / t_scale, 30),
                selectable=True,
                color=(1.0, 1, 0.4)
                if name == '__lastReplay.brp'
                else (1, 1, 1),
                always_highlight=True,
                on_select_call=ba.Call(self._on_my_replay_select, name),
                on_activate_call=self._my_replays_watch_replay_button.activate,
                text=self._get_replay_display_name(name),
                h_align='left',
                v_align='center',
                corner_scale=t_scale,
                maxwidth=(self._my_replays_scroll_width / t_scale) * 0.93,
            )
            if i == 0:
                ba.widget(
                    edit=txt,
                    up_widget=self._tab_row.tabs[self.TabID.MY_REPLAYS].button,
                )

    def _save_state(self) -> None:
        try:
            sel = self._root_widget.get_selected_child()
            selected_tab_ids = [
                tab_id
                for tab_id, tab in self._tab_row.tabs.items()
                if sel == tab.button
            ]
            if sel == self._back_button:
                sel_name = 'Back'
            elif selected_tab_ids:
                assert len(selected_tab_ids) == 1
                sel_name = f'Tab:{selected_tab_ids[0].value}'
            elif sel == self._tab_container:
                sel_name = 'TabContainer'
            else:
                raise ValueError(f'unrecognized selection {sel}')
            ba.app.ui.window_states[type(self)] = {'sel_name': sel_name}
        except Exception:
            ba.print_exception(f'Error saving state for {self}.')

    def _restore_state(self) -> None:
        from efro.util import enum_by_value

        try:
            sel: ba.Widget | None
            sel_name = ba.app.ui.window_states.get(type(self), {}).get(
                'sel_name'
            )
            assert isinstance(sel_name, (str, type(None)))
            try:
                current_tab = enum_by_value(
                    self.TabID, ba.app.config.get('Watch Tab')
                )
            except ValueError:
                current_tab = self.TabID.MY_REPLAYS
            self._set_tab(current_tab)

            if sel_name == 'Back':
                sel = self._back_button
            elif sel_name == 'TabContainer':
                sel = self._tab_container
            elif isinstance(sel_name, str) and sel_name.startswith('Tab:'):
                try:
                    sel_tab_id = enum_by_value(
                        self.TabID, sel_name.split(':')[-1]
                    )
                except ValueError:
                    sel_tab_id = self.TabID.MY_REPLAYS
                sel = self._tab_row.tabs[sel_tab_id].button
            else:
                if self._tab_container is not None:
                    sel = self._tab_container
                else:
                    sel = self._tab_row.tabs[current_tab].button
            ba.containerwidget(edit=self._root_widget, selected_child=sel)
        except Exception:
            ba.print_exception(f'Error restoring state for {self}.')

    def _back(self) -> None:
        from bastd.ui.mainmenu import MainMenuWindow

        self._save_state()
        ba.containerwidget(
            edit=self._root_widget, transition=self._transition_out
        )
        ba.app.ui.set_main_menu_window(
            MainMenuWindow(transition='in_left').get_root_widget()
        )
