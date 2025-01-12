# Released under the MIT License. See LICENSE for details.
#
"""Provides UI functionality for watching replays."""

from __future__ import annotations

import os
import logging
from enum import Enum
from typing import TYPE_CHECKING, cast, override

import bascenev1 as bs
import bauiv1 as bui

if TYPE_CHECKING:
    from typing import Any


class WatchWindow(bui.MainWindow):
    """Window for watching replays."""

    class TabID(Enum):
        """Our available tab types."""

        MY_REPLAYS = 'my_replays'
        TEST_TAB = 'test_tab'

    def __init__(
        self,
        transition: str | None = 'in_right',
        origin_widget: bui.Widget | None = None,
    ):
        # pylint: disable=too-many-locals
        from bauiv1lib.tabs import TabRow

        bui.set_analytics_screen('Watch Window')
        self._tab_data: dict[str, Any] = {}
        self._my_replays_scroll_width: float | None = None
        self._my_replays_watch_replay_button: bui.Widget | None = None
        self._scrollwidget: bui.Widget | None = None
        self._columnwidget: bui.Widget | None = None
        self._my_replay_selected: str | None = None
        self._my_replays_rename_window: bui.Widget | None = None
        self._my_replay_rename_text: bui.Widget | None = None
        self._r = 'watchWindow'
        uiscale = bui.app.ui_v1.uiscale
        self._width = 1440 if uiscale is bui.UIScale.SMALL else 1040
        x_inset = 200 if uiscale is bui.UIScale.SMALL else 0
        self._height = (
            570
            if uiscale is bui.UIScale.SMALL
            else 670 if uiscale is bui.UIScale.MEDIUM else 800
        )
        self._current_tab: WatchWindow.TabID | None = None
        extra_top = 20 if uiscale is bui.UIScale.SMALL else 0

        super().__init__(
            root_widget=bui.containerwidget(
                size=(self._width, self._height + extra_top),
                toolbar_visibility=(
                    'menu_minimal'
                    if uiscale is bui.UIScale.SMALL
                    else 'menu_full'
                ),
                scale=(
                    1.32
                    if uiscale is bui.UIScale.SMALL
                    else 0.85 if uiscale is bui.UIScale.MEDIUM else 0.65
                ),
                stack_offset=(
                    (0, 30)
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
            self._back_button = btn = bui.buttonwidget(
                parent=self._root_widget,
                autoselect=True,
                position=(70 + x_inset, self._height - 74),
                size=(60, 60),
                scale=1.1,
                label=bui.charstr(bui.SpecialChar.BACK),
                button_type='backSmall',
                on_activate_call=self.main_window_back,
            )
            bui.containerwidget(edit=self._root_widget, cancel_button=btn)

        bui.textwidget(
            parent=self._root_widget,
            position=(
                self._width * 0.5,
                self._height - (65 if uiscale is bui.UIScale.SMALL else 38),
            ),
            size=(0, 0),
            color=bui.app.ui_v1.title_color,
            scale=0.7 if uiscale is bui.UIScale.SMALL else 1.5,
            h_align='center',
            v_align='center',
            text=(
                ''
                if uiscale is bui.UIScale.SMALL
                else bui.Lstr(resource=f'{self._r}.titleText')
            ),
            maxwidth=400,
        )

        tabdefs = [
            (
                self.TabID.MY_REPLAYS,
                bui.Lstr(resource=f'{self._r}.myReplaysText'),
            ),
            # (self.TabID.TEST_TAB, bui.Lstr(value='Testing')),
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

        first_tab = self._tab_row.tabs[tabdefs[0][0]]
        last_tab = self._tab_row.tabs[tabdefs[-1][0]]
        bui.widget(
            edit=last_tab.button,
            right_widget=bui.get_special_widget('squad_button'),
        )
        if uiscale is bui.UIScale.SMALL:
            bbtn = bui.get_special_widget('back_button')
            bui.widget(edit=first_tab.button, up_widget=bbtn, left_widget=bbtn)

        self._scroll_width = self._width - scroll_buffer_h
        self._scroll_height = self._height - 180

        # Not actually using a scroll widget anymore; just an image.
        scroll_left = (self._width - self._scroll_width) * 0.5
        scroll_bottom = self._height - self._scroll_height - 79 - 48
        buffer_h = 10
        buffer_v = 4
        bui.imagewidget(
            parent=self._root_widget,
            position=(scroll_left - buffer_h, scroll_bottom - buffer_v),
            size=(
                self._scroll_width + 2 * buffer_h,
                self._scroll_height + 2 * buffer_v,
            ),
            texture=bui.gettexture('scrollWidget'),
            mesh_transparent=bui.getmesh('softEdgeOutside'),
            opacity=0.4,
        )
        self._tab_container: bui.Widget | None = None

        self._restore_state()

    @override
    def get_main_window_state(self) -> bui.MainWindowState:
        # Support recreating our window for back/refresh purposes.
        cls = type(self)
        return bui.BasicMainWindowState(
            create_call=lambda transition, origin_widget: cls(
                transition=transition, origin_widget=origin_widget
            )
        )

    @override
    def on_main_window_close(self) -> None:
        self._save_state()

    def _set_tab(self, tab_id: TabID) -> None:
        # pylint: disable=too-many-locals

        if self._current_tab == tab_id:
            return
        self._current_tab = tab_id

        # Preserve our current tab between runs.
        cfg = bui.app.config
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

        assert bui.app.classic is not None
        uiscale = bui.app.ui_v1.uiscale
        if tab_id is self.TabID.MY_REPLAYS:
            c_width = self._scroll_width
            c_height = self._scroll_height - 20
            sub_scroll_height = c_height - 63
            self._my_replays_scroll_width = sub_scroll_width = (
                680 if uiscale is bui.UIScale.SMALL else 640
            )

            self._tab_container = cnt = bui.containerwidget(
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
            bui.textwidget(
                parent=cnt,
                position=(c_width * 0.5, v),
                color=(0.6, 1.0, 0.6),
                scale=0.7,
                size=(0, 0),
                maxwidth=c_width * 0.9,
                h_align='center',
                v_align='center',
                text=bui.Lstr(
                    resource='replayRenameWarningText',
                    subs=[
                        (
                            '${REPLAY}',
                            bui.Lstr(resource='replayNameDefaultText'),
                        )
                    ],
                ),
            )

            b_width = 140 if uiscale is bui.UIScale.SMALL else 178
            b_height = (
                107
                if uiscale is bui.UIScale.SMALL
                else 142 if uiscale is bui.UIScale.MEDIUM else 190
            )
            b_space_extra = (
                0
                if uiscale is bui.UIScale.SMALL
                else -2 if uiscale is bui.UIScale.MEDIUM else -5
            )

            b_color = (0.6, 0.53, 0.63)
            b_textcolor = (0.75, 0.7, 0.8)
            btnv = (
                c_height
                - (
                    48
                    if uiscale is bui.UIScale.SMALL
                    else 45 if uiscale is bui.UIScale.MEDIUM else 40
                )
                - b_height
            )
            btnh = 40 if uiscale is bui.UIScale.SMALL else 40
            smlh = 190 if uiscale is bui.UIScale.SMALL else 225
            tscl = 1.0 if uiscale is bui.UIScale.SMALL else 1.2
            self._my_replays_watch_replay_button = btn1 = bui.buttonwidget(
                parent=cnt,
                size=(b_width, b_height),
                position=(btnh, btnv),
                button_type='square',
                color=b_color,
                textcolor=b_textcolor,
                on_activate_call=self._on_my_replay_play_press,
                text_scale=tscl,
                label=bui.Lstr(resource=f'{self._r}.watchReplayButtonText'),
                autoselect=True,
            )
            bui.widget(edit=btn1, up_widget=self._tab_row.tabs[tab_id].button)
            assert bui.app.classic is not None
            if uiscale is bui.UIScale.SMALL:
                bui.widget(
                    edit=btn1,
                    left_widget=bui.get_special_widget('back_button'),
                )
            btnv -= b_height + b_space_extra
            bui.buttonwidget(
                parent=cnt,
                size=(b_width, b_height),
                position=(btnh, btnv),
                button_type='square',
                color=b_color,
                textcolor=b_textcolor,
                on_activate_call=self._on_my_replay_rename_press,
                text_scale=tscl,
                label=bui.Lstr(resource=f'{self._r}.renameReplayButtonText'),
                autoselect=True,
            )
            btnv -= b_height + b_space_extra
            bui.buttonwidget(
                parent=cnt,
                size=(b_width, b_height),
                position=(btnh, btnv),
                button_type='square',
                color=b_color,
                textcolor=b_textcolor,
                on_activate_call=self._on_my_replay_delete_press,
                text_scale=tscl,
                label=bui.Lstr(resource=f'{self._r}.deleteReplayButtonText'),
                autoselect=True,
            )

            v -= sub_scroll_height + 23
            self._scrollwidget = scrlw = bui.scrollwidget(
                parent=cnt,
                position=(smlh, v),
                size=(sub_scroll_width, sub_scroll_height),
            )
            bui.containerwidget(edit=cnt, selected_child=scrlw)
            self._columnwidget = bui.columnwidget(
                parent=scrlw, left_border=10, border=2, margin=0
            )

            bui.widget(
                edit=scrlw,
                autoselect=True,
                left_widget=btn1,
                up_widget=self._tab_row.tabs[tab_id].button,
            )
            bui.widget(
                edit=self._tab_row.tabs[tab_id].button, down_widget=scrlw
            )

            self._my_replay_selected = None
            self._refresh_my_replays()

    def _no_replay_selected_error(self) -> None:
        bui.screenmessage(
            bui.Lstr(resource=f'{self._r}.noReplaySelectedErrorText'),
            color=(1, 0, 0),
        )
        bui.getsound('error').play()

    def _on_my_replay_play_press(self) -> None:
        if self._my_replay_selected is None:
            self._no_replay_selected_error()
            return
        bui.increment_analytics_count('Replay watch')

        # Save our place in the UI so we return there when done.
        if bui.app.classic is not None:
            bui.app.classic.save_ui_state()

        def do_it() -> None:
            try:
                # Reset to normal speed.
                bs.set_replay_speed_exponent(0)
                bui.fade_screen(True)
                assert self._my_replay_selected is not None
                bs.new_replay_session(
                    f'{bui.get_replays_dir()}/{self._my_replay_selected}'
                )
            except Exception:
                logging.exception('Error running replay session.')

                # Drop back into a fresh main menu session
                # in case we half-launched or something.
                from bascenev1lib import mainmenu

                bs.new_host_session(mainmenu.MainMenuSession)

        bui.fade_screen(False, endcall=bui.Call(bui.pushcall, do_it))
        bui.containerwidget(edit=self._root_widget, transition='out_left')

    def _on_my_replay_rename_press(self) -> None:
        if self._my_replay_selected is None:
            self._no_replay_selected_error()
            return
        c_width = 600
        c_height = 250
        assert bui.app.classic is not None
        uiscale = bui.app.ui_v1.uiscale
        self._my_replays_rename_window = cnt = bui.containerwidget(
            scale=(
                1.8
                if uiscale is bui.UIScale.SMALL
                else 1.55 if uiscale is bui.UIScale.MEDIUM else 1.0
            ),
            size=(c_width, c_height),
            transition='in_scale',
        )
        dname = self._get_replay_display_name(self._my_replay_selected)
        bui.textwidget(
            parent=cnt,
            size=(0, 0),
            h_align='center',
            v_align='center',
            text=bui.Lstr(
                resource=f'{self._r}.renameReplayText',
                subs=[('${REPLAY}', dname)],
            ),
            maxwidth=c_width * 0.8,
            position=(c_width * 0.5, c_height - 60),
        )
        self._my_replay_rename_text = txt = bui.textwidget(
            parent=cnt,
            size=(c_width * 0.8, 40),
            h_align='left',
            v_align='center',
            text=dname,
            editable=True,
            description=bui.Lstr(resource=f'{self._r}.replayNameText'),
            position=(c_width * 0.1, c_height - 140),
            autoselect=True,
            maxwidth=c_width * 0.7,
            max_chars=200,
        )
        cbtn = bui.buttonwidget(
            parent=cnt,
            label=bui.Lstr(resource='cancelText'),
            on_activate_call=bui.Call(
                lambda c: bui.containerwidget(edit=c, transition='out_scale'),
                cnt,
            ),
            size=(180, 60),
            position=(30, 30),
            autoselect=True,
        )
        okb = bui.buttonwidget(
            parent=cnt,
            label=bui.Lstr(resource=f'{self._r}.renameText'),
            size=(180, 60),
            position=(c_width - 230, 30),
            on_activate_call=bui.Call(
                self._rename_my_replay, self._my_replay_selected
            ),
            autoselect=True,
        )
        bui.widget(edit=cbtn, right_widget=okb)
        bui.widget(edit=okb, left_widget=cbtn)
        bui.textwidget(edit=txt, on_return_press_call=okb.activate)
        bui.containerwidget(edit=cnt, cancel_button=cbtn, start_button=okb)

    def _rename_my_replay(self, replay: str) -> None:
        new_name = None
        try:
            if not self._my_replay_rename_text:
                return
            new_name_raw = cast(
                str, bui.textwidget(query=self._my_replay_rename_text)
            )
            new_name = new_name_raw + '.brp'

            # Ignore attempts to change it to what it already is
            # (or what it looks like to the user).
            if (
                replay != new_name
                and self._get_replay_display_name(replay) != new_name_raw
            ):
                old_name_full = (bui.get_replays_dir() + '/' + replay).encode(
                    'utf-8'
                )
                new_name_full = (bui.get_replays_dir() + '/' + new_name).encode(
                    'utf-8'
                )
                # False alarm; bui.textwidget can return non-None val.
                # pylint: disable=unsupported-membership-test
                if os.path.exists(new_name_full):
                    bui.getsound('error').play()
                    bui.screenmessage(
                        bui.Lstr(
                            resource=self._r
                            + '.replayRenameErrorAlreadyExistsText'
                        ),
                        color=(1, 0, 0),
                    )
                elif any(char in new_name_raw for char in ['/', '\\', ':']):
                    bui.getsound('error').play()
                    bui.screenmessage(
                        bui.Lstr(
                            resource=f'{self._r}.replayRenameErrorInvalidName'
                        ),
                        color=(1, 0, 0),
                    )
                else:
                    bui.increment_analytics_count('Replay rename')
                    os.rename(old_name_full, new_name_full)
                    self._refresh_my_replays()
                    bui.getsound('gunCocking').play()
        except Exception:
            logging.exception(
                "Error renaming replay '%s' to '%s'.", replay, new_name
            )
            bui.getsound('error').play()
            bui.screenmessage(
                bui.Lstr(resource=f'{self._r}.replayRenameErrorText'),
                color=(1, 0, 0),
            )

        bui.containerwidget(
            edit=self._my_replays_rename_window, transition='out_scale'
        )

    def _on_my_replay_delete_press(self) -> None:
        from bauiv1lib import confirm

        if self._my_replay_selected is None:
            self._no_replay_selected_error()
            return
        confirm.ConfirmWindow(
            bui.Lstr(
                resource=f'{self._r}.deleteConfirmText',
                subs=[
                    (
                        '${REPLAY}',
                        self._get_replay_display_name(self._my_replay_selected),
                    )
                ],
            ),
            bui.Call(self._delete_replay, self._my_replay_selected),
            450,
            150,
        )

    def _get_replay_display_name(self, replay: str) -> str:
        if replay.endswith('.brp'):
            replay = replay[:-4]
        if replay == '__lastReplay':
            return bui.Lstr(resource='replayNameDefaultText').evaluate()
        return replay

    def _delete_replay(self, replay: str) -> None:
        try:
            bui.increment_analytics_count('Replay delete')
            os.remove((bui.get_replays_dir() + '/' + replay).encode('utf-8'))
            self._refresh_my_replays()
            bui.getsound('shieldDown').play()
            if replay == self._my_replay_selected:
                self._my_replay_selected = None
        except Exception:
            logging.exception("Error deleting replay '%s'.", replay)
            bui.getsound('error').play()
            bui.screenmessage(
                bui.Lstr(resource=f'{self._r}.replayDeleteErrorText'),
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
            names = os.listdir(bui.get_replays_dir())

            # Ignore random other files in there.
            names = [n for n in names if n.endswith('.brp')]
            names.sort(key=lambda x: x.lower())
        except Exception:
            logging.exception('Error listing replays dir.')
            names = []

        assert self._my_replays_scroll_width is not None
        assert self._my_replays_watch_replay_button is not None
        for i, name in enumerate(names):
            txt = bui.textwidget(
                parent=self._columnwidget,
                size=(self._my_replays_scroll_width / t_scale, 30),
                selectable=True,
                color=(
                    (1.0, 1, 0.4) if name == '__lastReplay.brp' else (1, 1, 1)
                ),
                always_highlight=True,
                on_select_call=bui.Call(self._on_my_replay_select, name),
                on_activate_call=self._my_replays_watch_replay_button.activate,
                text=self._get_replay_display_name(name),
                h_align='left',
                v_align='center',
                corner_scale=t_scale,
                maxwidth=(self._my_replays_scroll_width / t_scale) * 0.93,
            )
            if i == 0:
                bui.widget(
                    edit=txt,
                    up_widget=self._tab_row.tabs[self.TabID.MY_REPLAYS].button,
                )
                self._my_replay_selected = name

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
            assert bui.app.classic is not None
            bui.app.ui_v1.window_states[type(self)] = {'sel_name': sel_name}
        except Exception:
            logging.exception('Error saving state for %s.', self)

    def _restore_state(self) -> None:
        try:
            sel: bui.Widget | None
            assert bui.app.classic is not None
            sel_name = bui.app.ui_v1.window_states.get(type(self), {}).get(
                'sel_name'
            )
            assert isinstance(sel_name, (str, type(None)))
            try:
                current_tab = self.TabID(bui.app.config.get('Watch Tab'))
            except ValueError:
                current_tab = self.TabID.MY_REPLAYS
            self._set_tab(current_tab)

            if sel_name == 'Back':
                sel = self._back_button
            elif sel_name == 'TabContainer':
                sel = self._tab_container
            elif isinstance(sel_name, str) and sel_name.startswith('Tab:'):
                try:
                    sel_tab_id = self.TabID(sel_name.split(':')[-1])
                except ValueError:
                    sel_tab_id = self.TabID.MY_REPLAYS
                sel = self._tab_row.tabs[sel_tab_id].button
            else:
                if self._tab_container is not None:
                    sel = self._tab_container
                else:
                    sel = self._tab_row.tabs[current_tab].button
            bui.containerwidget(edit=self._root_widget, selected_child=sel)
        except Exception:
            logging.exception('Error restoring state for %s.', self)
