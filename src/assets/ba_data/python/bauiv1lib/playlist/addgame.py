# Released under the MIT License. See LICENSE for details.
#
"""Provides a window for selecting a game type to add to a playlist."""

from __future__ import annotations

from typing import TYPE_CHECKING, override

import bascenev1 as bs
import bauiv1 as bui

if TYPE_CHECKING:
    from bauiv1lib.playlist.editcontroller import PlaylistEditController


class PlaylistAddGameWindow(bui.MainWindow):
    """Window for selecting a game type to add to a playlist."""

    def __init__(
        self,
        editcontroller: PlaylistEditController,
        transition: str | None = 'in_right',
        origin_widget: bui.Widget | None = None,
    ):
        self._editcontroller = editcontroller
        self._r = 'addGameWindow'
        assert bui.app.classic is not None
        uiscale = bui.app.ui_v1.uiscale
        self._width = 750 if uiscale is bui.UIScale.SMALL else 650
        x_inset = 50 if uiscale is bui.UIScale.SMALL else 0
        yoffs = -44 if uiscale is bui.UIScale.SMALL else 0

        self._height = (
            400
            if uiscale is bui.UIScale.SMALL
            else 400 if uiscale is bui.UIScale.MEDIUM else 460
        )
        self._scroll_width = 210

        super().__init__(
            root_widget=bui.containerwidget(
                size=(self._width, self._height),
                scale=(
                    1.95
                    if uiscale is bui.UIScale.SMALL
                    else 1.5 if uiscale is bui.UIScale.MEDIUM else 1.0
                ),
                stack_offset=(0, 1) if uiscale is bui.UIScale.SMALL else (0, 0),
                toolbar_visibility='menu_minimal',
            ),
            transition=transition,
            origin_widget=origin_widget,
        )

        if uiscale is bui.UIScale.SMALL:
            self._back_button = bui.get_special_widget('back_button')
        else:
            self._back_button = bui.buttonwidget(
                parent=self._root_widget,
                position=(58 + x_inset, self._height - 53 + yoffs),
                size=(60, 48),
                label=bui.charstr(bui.SpecialChar.BACK),
                autoselect=True,
                button_type='backSmall',
                on_activate_call=self.main_window_back,
            )
        self._select_button = select_button = bui.buttonwidget(
            parent=self._root_widget,
            position=(self._width - (172 + x_inset), self._height - 50 + yoffs),
            autoselect=True,
            size=(160, 60),
            scale=0.75,
            text_scale=1.2,
            label=bui.Lstr(resource='selectText'),
            on_activate_call=self._add,
        )

        bui.widget(
            edit=select_button,
            right_widget=bui.get_special_widget('squad_button'),
        )

        bui.textwidget(
            parent=self._root_widget,
            position=(self._width * 0.5, self._height - 28 + yoffs),
            size=(0, 0),
            scale=1.0,
            text=bui.Lstr(resource=f'{self._r}.titleText'),
            h_align='center',
            color=bui.app.ui_v1.title_color,
            maxwidth=250,
            v_align='center',
        )
        v = self._height - 64 + yoffs

        self._selected_title_text = bui.textwidget(
            parent=self._root_widget,
            position=(x_inset + self._scroll_width + 50 + 30, v - 15),
            size=(0, 0),
            scale=1.0,
            color=(0.7, 1.0, 0.7, 1.0),
            maxwidth=self._width - self._scroll_width - 150 - x_inset * 2,
            h_align='left',
            v_align='center',
        )
        v -= 30

        self._selected_description_text = bui.textwidget(
            parent=self._root_widget,
            position=(x_inset + self._scroll_width + 50 + 30, v),
            size=(0, 0),
            scale=0.7,
            color=(0.5, 0.8, 0.5, 1.0),
            maxwidth=self._width - self._scroll_width - 150 - x_inset * 2,
            h_align='left',
        )

        scroll_height = self._height - (
            160 if uiscale is bui.UIScale.SMALL else 100
        )

        v = self._height - 60 + yoffs

        self._scrollwidget = bui.scrollwidget(
            parent=self._root_widget,
            position=(x_inset + 61, v - scroll_height),
            size=(self._scroll_width, scroll_height),
            highlight=False,
            border_opacity=0.4,
        )
        bui.widget(
            edit=self._scrollwidget,
            up_widget=self._back_button,
            left_widget=self._back_button,
            right_widget=select_button,
        )
        self._column: bui.Widget | None = None

        v -= 35

        if uiscale is bui.UIScale.SMALL:
            bui.containerwidget(
                edit=self._root_widget, on_cancel_call=self.main_window_back
            )
        else:
            bui.containerwidget(
                edit=self._root_widget,
                cancel_button=self._back_button,
            )
        bui.containerwidget(edit=self._root_widget, start_button=select_button)

        self._selected_game_type: type[bs.GameActivity] | None = None

        bui.containerwidget(
            edit=self._root_widget, selected_child=self._scrollwidget
        )

        self._game_types: list[type[bs.GameActivity]] = []

        # Get actual games loading in the bg.
        bui.app.meta.load_exported_classes(
            bs.GameActivity,
            self._on_game_types_loaded,
            completion_cb_in_bg_thread=True,
        )

        # Refresh with our initial empty list. We'll refresh again once
        # game loading is complete.
        self._refresh()

    @override
    def get_main_window_state(self) -> bui.MainWindowState:
        # Support recreating our window for back/refresh purposes.
        cls = type(self)

        # Avoid dereferencing self from the lambda or we'll keep
        # ourself alive indefinitely.
        editcontroller = self._editcontroller

        return bui.BasicMainWindowState(
            create_call=lambda transition, origin_widget: cls(
                transition=transition,
                origin_widget=origin_widget,
                editcontroller=editcontroller,
            )
        )

    def _on_game_types_loaded(
        self, gametypes: list[type[bs.GameActivity]]
    ) -> None:
        assert bui.app.classic is not None
        store = bui.app.classic.store

        # We asked for a bg thread completion cb so we can do some
        # filtering here in the bg thread where its not gonna cause hitches.
        assert not bui.in_logic_thread()
        sessiontype = self._editcontroller.get_session_type()
        unowned = store.get_unowned_game_types()
        self._game_types = [
            gt
            for gt in gametypes
            if gt not in unowned and gt.supports_session_type(sessiontype)
        ]

        # Sort in the current language.
        self._game_types.sort(key=lambda g: g.get_display_string().evaluate())

        # Tell ourself to refresh back in the logic thread.
        bui.pushcall(self._refresh, from_other_thread=True)

    def _refresh(self, select_get_more_games_button: bool = False) -> None:
        if self._column is not None:
            self._column.delete()

        self._column = bui.columnwidget(
            parent=self._scrollwidget, border=2, margin=0
        )

        for i, gametype in enumerate(self._game_types):

            def _doit() -> None:
                if self._select_button:
                    bui.apptimer(0.1, self._select_button.activate)

            txt = bui.textwidget(
                parent=self._column,
                position=(0, 0),
                size=(self._scroll_width * 1.1, 24),
                text=gametype.get_display_string(),
                h_align='left',
                v_align='center',
                color=(0.8, 0.8, 0.8, 1.0),
                maxwidth=self._scroll_width * 0.8,
                on_select_call=bui.Call(self._set_selected_game_type, gametype),
                always_highlight=True,
                selectable=True,
                on_activate_call=_doit,
            )
            if i == 0:
                bui.widget(edit=txt, up_widget=self._back_button)

        self._get_more_games_button = bui.buttonwidget(
            parent=self._column,
            autoselect=True,
            label=bui.Lstr(resource=f'{self._r}.getMoreGamesText'),
            color=(0.54, 0.52, 0.67),
            textcolor=(0.7, 0.65, 0.7),
            on_activate_call=self._on_get_more_games_press,
            size=(178, 50),
        )
        if select_get_more_games_button:
            bui.containerwidget(
                edit=self._column,
                selected_child=self._get_more_games_button,
                visible_child=self._get_more_games_button,
            )

    def _on_get_more_games_press(self) -> None:
        from bauiv1lib.account.signin import show_sign_in_prompt
        from bauiv1lib.store.browser import StoreBrowserWindow

        # No-op if we're not in control.
        if self.main_window_has_control():
            return

        plus = bui.app.plus
        assert plus is not None

        if plus.get_v1_account_state() != 'signed_in':
            show_sign_in_prompt()
            return

        self.main_window_replace(
            StoreBrowserWindow(
                show_tab=StoreBrowserWindow.TabID.MINIGAMES,
                origin_widget=self._get_more_games_button,
                minimal_toolbars=True,
            )
        )

    def _add(self) -> None:
        bui.lock_all_input()  # Make sure no more commands happen.
        bui.apptimer(0.1, bui.unlock_all_input)
        assert self._selected_game_type is not None
        self._editcontroller.add_game_type_selected(
            self._selected_game_type, from_window=self
        )

    def _set_selected_game_type(self, gametype: type[bs.GameActivity]) -> None:
        self._selected_game_type = gametype
        bui.textwidget(
            edit=self._selected_title_text, text=gametype.get_display_string()
        )
        bui.textwidget(
            edit=self._selected_description_text,
            text=gametype.get_description_display_string(
                self._editcontroller.get_session_type()
            ),
        )
