# Released under the MIT License. See LICENSE for details.
#
"""Provides UI for browsing soundtracks."""

from __future__ import annotations

import copy
import logging
from typing import TYPE_CHECKING, override

import bauiv1 as bui

if TYPE_CHECKING:
    from typing import Any

REQUIRE_PRO = False


class SoundtrackBrowserWindow(bui.MainWindow):
    """Window for browsing soundtracks."""

    def __init__(
        self,
        transition: str | None = 'in_right',
        origin_widget: bui.Widget | None = None,
    ):
        # pylint: disable=too-many-statements
        # pylint: disable=too-many-locals

        self._r = 'editSoundtrackWindow'
        assert bui.app.classic is not None
        uiscale = bui.app.ui_v1.uiscale
        self._width = 800 if uiscale is bui.UIScale.SMALL else 600
        x_inset = 100 if uiscale is bui.UIScale.SMALL else 0
        yoffs = -30 if uiscale is bui.UIScale.SMALL else 0
        self._height = (
            400
            if uiscale is bui.UIScale.SMALL
            else 370 if uiscale is bui.UIScale.MEDIUM else 440
        )
        spacing = 40.0
        v = self._height - 40.0 + yoffs
        v -= spacing * 1.0

        super().__init__(
            root_widget=bui.containerwidget(
                size=(self._width, self._height),
                toolbar_visibility=(
                    'menu_minimal'
                    if uiscale is bui.UIScale.SMALL
                    else 'menu_full'
                ),
                scale=(
                    2.1
                    if uiscale is bui.UIScale.SMALL
                    else 1.6 if uiscale is bui.UIScale.MEDIUM else 1.0
                ),
                stack_offset=(
                    (0, 0) if uiscale is bui.UIScale.SMALL else (0, 0)
                ),
            ),
            transition=transition,
            origin_widget=origin_widget,
        )

        assert bui.app.classic is not None
        if uiscale is bui.UIScale.SMALL:
            self._back_button = None
        else:
            self._back_button = bui.buttonwidget(
                parent=self._root_widget,
                position=(45 + x_inset, self._height - 60 + yoffs),
                size=(120, 60),
                scale=0.8,
                label=bui.Lstr(resource='backText'),
                button_type='back',
                autoselect=True,
            )
            bui.buttonwidget(
                edit=self._back_button,
                button_type='backSmall',
                size=(60, 60),
                label=bui.charstr(bui.SpecialChar.BACK),
            )
        bui.textwidget(
            parent=self._root_widget,
            position=(
                self._width * 0.5,
                self._height
                - (46 if uiscale is bui.UIScale.SMALL else 35)
                + yoffs,
            ),
            size=(0, 0),
            maxwidth=300,
            text=bui.Lstr(resource=f'{self._r}.titleText'),
            color=bui.app.ui_v1.title_color,
            h_align='center',
            v_align='center',
        )

        h = 43 + x_inset
        v = self._height - 60 + yoffs
        b_color = (0.6, 0.53, 0.63)
        b_textcolor = (0.75, 0.7, 0.8)
        lock_tex = bui.gettexture('lock')
        self._lock_images: list[bui.Widget] = []

        scl = (
            1.0
            if uiscale is bui.UIScale.SMALL
            else 1.13 if uiscale is bui.UIScale.MEDIUM else 1.4
        )
        v -= 60.0 * scl
        self._new_button = btn = bui.buttonwidget(
            parent=self._root_widget,
            position=(h, v),
            size=(100, 55.0 * scl),
            on_activate_call=self._new_soundtrack,
            color=b_color,
            button_type='square',
            autoselect=True,
            textcolor=b_textcolor,
            text_scale=0.7,
            label=bui.Lstr(resource=f'{self._r}.newText'),
        )
        self._lock_images.append(
            bui.imagewidget(
                parent=self._root_widget,
                size=(30, 30),
                draw_controller=btn,
                position=(h - 10, v + 55.0 * scl - 28),
                texture=lock_tex,
            )
        )

        if self._back_button is None:
            bui.widget(
                edit=btn,
                left_widget=bui.get_special_widget('back_button'),
            )
        v -= 60.0 * scl

        self._edit_button = btn = bui.buttonwidget(
            parent=self._root_widget,
            position=(h, v),
            size=(100, 55.0 * scl),
            on_activate_call=self._edit_soundtrack,
            color=b_color,
            button_type='square',
            autoselect=True,
            textcolor=b_textcolor,
            text_scale=0.7,
            label=bui.Lstr(resource=f'{self._r}.editText'),
        )
        self._lock_images.append(
            bui.imagewidget(
                parent=self._root_widget,
                size=(30, 30),
                draw_controller=btn,
                position=(h - 10, v + 55.0 * scl - 28),
                texture=lock_tex,
            )
        )
        if self._back_button is None:
            bui.widget(
                edit=btn,
                left_widget=bui.get_special_widget('back_button'),
            )
        v -= 60.0 * scl

        self._duplicate_button = btn = bui.buttonwidget(
            parent=self._root_widget,
            position=(h, v),
            size=(100, 55.0 * scl),
            on_activate_call=self._duplicate_soundtrack,
            button_type='square',
            autoselect=True,
            color=b_color,
            textcolor=b_textcolor,
            text_scale=0.7,
            label=bui.Lstr(resource=f'{self._r}.duplicateText'),
        )
        self._lock_images.append(
            bui.imagewidget(
                parent=self._root_widget,
                size=(30, 30),
                draw_controller=btn,
                position=(h - 10, v + 55.0 * scl - 28),
                texture=lock_tex,
            )
        )
        if self._back_button is None:
            bui.widget(
                edit=btn,
                left_widget=bui.get_special_widget('back_button'),
            )
        v -= 60.0 * scl

        self._delete_button = btn = bui.buttonwidget(
            parent=self._root_widget,
            position=(h, v),
            size=(100, 55.0 * scl),
            on_activate_call=self._delete_soundtrack,
            color=b_color,
            button_type='square',
            autoselect=True,
            textcolor=b_textcolor,
            text_scale=0.7,
            label=bui.Lstr(resource=f'{self._r}.deleteText'),
        )
        self._lock_images.append(
            bui.imagewidget(
                parent=self._root_widget,
                size=(30, 30),
                draw_controller=btn,
                position=(h - 10, v + 55.0 * scl - 28),
                texture=lock_tex,
            )
        )
        if self._back_button is None:
            bui.widget(
                edit=btn,
                left_widget=bui.get_special_widget('back_button'),
            )

        # Keep our lock images up to date/etc.
        self._update_timer = bui.AppTimer(
            1.0, bui.WeakCall(self._update), repeat=True
        )
        self._update()

        v = self._height - 65 + yoffs
        scroll_height = self._height - (
            160 if uiscale is bui.UIScale.SMALL else 105
        )
        v -= scroll_height
        self._scrollwidget = scrollwidget = bui.scrollwidget(
            parent=self._root_widget,
            position=(152 + x_inset, v),
            highlight=False,
            size=(self._width - (205 + 2 * x_inset), scroll_height),
        )
        bui.widget(
            edit=self._scrollwidget,
            left_widget=self._new_button,
            right_widget=bui.get_special_widget('squad_button'),
        )
        self._col = bui.columnwidget(parent=scrollwidget, border=2, margin=0)

        self._soundtracks: dict[str, Any] | None = None
        self._selected_soundtrack: str | None = None
        self._selected_soundtrack_index: int | None = None
        self._soundtrack_widgets: list[bui.Widget] = []
        self._allow_changing_soundtracks = False
        self._refresh()
        if self._back_button is not None:
            bui.buttonwidget(
                edit=self._back_button, on_activate_call=self.main_window_back
            )
            bui.containerwidget(
                edit=self._root_widget, cancel_button=self._back_button
            )
        else:
            bui.containerwidget(
                edit=self._root_widget, on_cancel_call=self.main_window_back
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

    @override
    def on_main_window_close(self) -> None:
        self._save_state()

    def _update(self) -> None:
        have_pro = (
            bui.app.classic is None
            or bui.app.classic.accounts.have_pro_options()
        )
        for lock in self._lock_images:
            bui.imagewidget(
                edit=lock, opacity=0.0 if (have_pro or not REQUIRE_PRO) else 1.0
            )

    def _do_delete_soundtrack(self) -> None:
        cfg = bui.app.config
        soundtracks = cfg.setdefault('Soundtracks', {})
        if self._selected_soundtrack in soundtracks:
            del soundtracks[self._selected_soundtrack]
        cfg.commit()
        bui.getsound('shieldDown').play()
        assert self._selected_soundtrack_index is not None
        assert self._soundtracks is not None
        self._selected_soundtrack_index = min(
            self._selected_soundtrack_index, len(self._soundtracks)
        )
        self._refresh()

    def _delete_soundtrack(self) -> None:
        # pylint: disable=cyclic-import
        from bauiv1lib.purchase import PurchaseWindow
        from bauiv1lib.confirm import ConfirmWindow

        if REQUIRE_PRO and (
            bui.app.classic is not None
            and not bui.app.classic.accounts.have_pro_options()
        ):
            PurchaseWindow(items=['pro'])
            return
        if self._selected_soundtrack is None:
            return
        if self._selected_soundtrack == '__default__':
            bui.getsound('error').play()
            bui.screenmessage(
                bui.Lstr(resource=f'{self._r}.cantDeleteDefaultText'),
                color=(1, 0, 0),
            )
        else:
            ConfirmWindow(
                bui.Lstr(
                    resource=f'{self._r}.deleteConfirmText',
                    subs=[('${NAME}', self._selected_soundtrack)],
                ),
                self._do_delete_soundtrack,
                450,
                150,
            )

    def _duplicate_soundtrack(self) -> None:
        # pylint: disable=cyclic-import
        from bauiv1lib.purchase import PurchaseWindow

        if REQUIRE_PRO and (
            bui.app.classic is not None
            and not bui.app.classic.accounts.have_pro_options()
        ):
            PurchaseWindow(items=['pro'])
            return
        cfg = bui.app.config
        cfg.setdefault('Soundtracks', {})

        if self._selected_soundtrack is None:
            return
        sdtk: dict[str, Any]
        if self._selected_soundtrack == '__default__':
            sdtk = {}
        else:
            sdtk = cfg['Soundtracks'][self._selected_soundtrack]

        # Find a valid dup name that doesn't exist.
        test_index = 1
        copy_text = bui.Lstr(resource='copyOfText').evaluate()
        # Get just 'Copy' or whatnot.
        copy_word = copy_text.replace('${NAME}', '').strip()
        base_name = self._get_soundtrack_display_name(
            self._selected_soundtrack
        ).evaluate()
        assert isinstance(base_name, str)

        # If it looks like a copy, strip digits and spaces off the end.
        if copy_word in base_name:
            while base_name[-1].isdigit() or base_name[-1] == ' ':
                base_name = base_name[:-1]
        while True:
            if copy_word in base_name:
                test_name = base_name
            else:
                test_name = copy_text.replace('${NAME}', base_name)
            if test_index > 1:
                test_name += ' ' + str(test_index)
            if test_name not in cfg['Soundtracks']:
                break
            test_index += 1

        cfg['Soundtracks'][test_name] = copy.deepcopy(sdtk)
        cfg.commit()
        self._refresh(select_soundtrack=test_name)

    def _select(self, name: str, index: int) -> None:
        assert bui.app.classic is not None
        music = bui.app.classic.music
        self._selected_soundtrack_index = index
        self._selected_soundtrack = name
        cfg = bui.app.config
        current_soundtrack = cfg.setdefault('Soundtrack', '__default__')

        # If it varies from current, commit and play.
        if current_soundtrack != name and self._allow_changing_soundtracks:
            bui.getsound('gunCocking').play()
            cfg['Soundtrack'] = self._selected_soundtrack
            cfg.commit()

            # Just play whats already playing.. this'll grab it from the
            # new soundtrack.
            music.do_play_music(
                music.music_types[bui.app.classic.MusicPlayMode.REGULAR]
            )

    def _edit_soundtrack_with_sound(self) -> None:
        # pylint: disable=cyclic-import
        from bauiv1lib.purchase import PurchaseWindow

        if REQUIRE_PRO and (
            bui.app.classic is not None
            and not bui.app.classic.accounts.have_pro_options()
        ):
            PurchaseWindow(items=['pro'])
            return
        bui.getsound('swish').play()
        self._edit_soundtrack()

    def _edit_soundtrack(self) -> None:
        # pylint: disable=cyclic-import
        from bauiv1lib.purchase import PurchaseWindow
        from bauiv1lib.soundtrack.edit import SoundtrackEditWindow

        # no-op if we don't have control.
        if not self.main_window_has_control():
            return

        if REQUIRE_PRO and (
            bui.app.classic is not None
            and not bui.app.classic.accounts.have_pro_options()
        ):
            PurchaseWindow(items=['pro'])
            return

        if self._selected_soundtrack is None:
            return

        if self._selected_soundtrack == '__default__':
            bui.getsound('error').play()
            bui.screenmessage(
                bui.Lstr(resource=f'{self._r}.cantEditDefaultText'),
                color=(1, 0, 0),
            )
            return

        self.main_window_replace(
            SoundtrackEditWindow(existing_soundtrack=self._selected_soundtrack)
        )

    def _get_soundtrack_display_name(self, soundtrack: str) -> bui.Lstr:
        if soundtrack == '__default__':
            return bui.Lstr(resource=f'{self._r}.defaultSoundtrackNameText')
        return bui.Lstr(value=soundtrack)

    def _refresh(self, select_soundtrack: str | None = None) -> None:
        from efro.util import asserttype

        self._allow_changing_soundtracks = False
        old_selection = self._selected_soundtrack

        # If there was no prev selection, look in prefs.
        if old_selection is None:
            old_selection = bui.app.config.get('Soundtrack')
        old_selection_index = self._selected_soundtrack_index

        # Delete old.
        while self._soundtrack_widgets:
            self._soundtrack_widgets.pop().delete()

        self._soundtracks = bui.app.config.get('Soundtracks', {})
        assert self._soundtracks is not None
        items = list(self._soundtracks.items())
        items.sort(key=lambda x: asserttype(x[0], str).lower())
        items = [('__default__', None)] + items  # default is always first
        index = 0
        for pname, _pval in items:
            assert pname is not None
            txtw = bui.textwidget(
                parent=self._col,
                size=(self._width - 40, 24),
                text=self._get_soundtrack_display_name(pname),
                h_align='left',
                v_align='center',
                maxwidth=self._width - 110,
                always_highlight=True,
                on_select_call=bui.WeakCall(self._select, pname, index),
                on_activate_call=self._edit_soundtrack_with_sound,
                selectable=True,
            )
            if index == 0:
                bui.widget(edit=txtw, up_widget=self._back_button)
            self._soundtrack_widgets.append(txtw)

            # Select this one if the user requested it
            if select_soundtrack is not None:
                if pname == select_soundtrack:
                    bui.columnwidget(
                        edit=self._col, selected_child=txtw, visible_child=txtw
                    )
            else:
                # Select this one if it was previously selected.
                # Go by index if there's one.
                if old_selection_index is not None:
                    if index == old_selection_index:
                        bui.columnwidget(
                            edit=self._col,
                            selected_child=txtw,
                            visible_child=txtw,
                        )
                else:  # Otherwise look by name.
                    if pname == old_selection:
                        bui.columnwidget(
                            edit=self._col,
                            selected_child=txtw,
                            visible_child=txtw,
                        )
            index += 1

        # Explicitly run select callback on current one and re-enable
        # callbacks.

        # Eww need to run this in a timer so it happens after our select
        # callbacks. With a small-enough time sometimes it happens before
        # anyway. Ew. need a way to just schedule a callable i guess.
        bui.apptimer(0.1, bui.WeakCall(self._set_allow_changing))

    def _set_allow_changing(self) -> None:
        self._allow_changing_soundtracks = True
        assert self._selected_soundtrack is not None
        assert self._selected_soundtrack_index is not None
        self._select(self._selected_soundtrack, self._selected_soundtrack_index)

    def _new_soundtrack(self) -> None:
        # pylint: disable=cyclic-import
        from bauiv1lib.purchase import PurchaseWindow
        from bauiv1lib.soundtrack.edit import SoundtrackEditWindow

        # no-op if we're not in control.
        if not self.main_window_has_control():
            return

        if REQUIRE_PRO and (
            bui.app.classic is not None
            and not bui.app.classic.accounts.have_pro_options()
        ):
            PurchaseWindow(items=['pro'])
            return

        self.main_window_replace(SoundtrackEditWindow(existing_soundtrack=None))

    def _create_done(self, new_soundtrack: str) -> None:
        if new_soundtrack is not None:
            bui.getsound('gunCocking').play()
            self._refresh(select_soundtrack=new_soundtrack)

    def _save_state(self) -> None:
        try:
            sel = self._root_widget.get_selected_child()
            if sel == self._scrollwidget:
                sel_name = 'Scroll'
            elif sel == self._new_button:
                sel_name = 'New'
            elif sel == self._edit_button:
                sel_name = 'Edit'
            elif sel == self._duplicate_button:
                sel_name = 'Duplicate'
            elif sel == self._delete_button:
                sel_name = 'Delete'
            elif sel == self._back_button:
                sel_name = 'Back'
            else:
                raise ValueError(f'unrecognized selection \'{sel}\'')
            assert bui.app.classic is not None
            bui.app.ui_v1.window_states[type(self)] = sel_name
        except Exception:
            logging.exception('Error saving state for %s.', self)

    def _restore_state(self) -> None:
        try:
            assert bui.app.classic is not None
            sel_name = bui.app.ui_v1.window_states.get(type(self))
            if sel_name == 'Scroll':
                sel = self._scrollwidget
            elif sel_name == 'New':
                sel = self._new_button
            elif sel_name == 'Edit':
                sel = self._edit_button
            elif sel_name == 'Duplicate':
                sel = self._duplicate_button
            elif sel_name == 'Delete':
                sel = self._delete_button
            else:
                sel = self._scrollwidget
            bui.containerwidget(edit=self._root_widget, selected_child=sel)
        except Exception:
            logging.exception('Error restoring state for %s.', self)
