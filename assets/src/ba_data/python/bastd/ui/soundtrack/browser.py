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
"""Provides UI for browsing soundtracks."""

from __future__ import annotations

import copy
from typing import TYPE_CHECKING

import _ba
import ba

if TYPE_CHECKING:
    from typing import Any, Optional, List, Tuple, Dict


class SoundtrackBrowserWindow(ba.Window):
    """Window for browsing soundtracks."""

    def __init__(self,
                 transition: str = 'in_right',
                 origin_widget: ba.Widget = None):
        # pylint: disable=too-many-locals
        # pylint: disable=too-many-statements

        # If they provided an origin-widget, scale up from that.
        scale_origin: Optional[Tuple[float, float]]
        if origin_widget is not None:
            self._transition_out = 'out_scale'
            scale_origin = origin_widget.get_screen_space_center()
            transition = 'in_scale'
        else:
            self._transition_out = 'out_right'
            scale_origin = None

        self._r = 'editSoundtrackWindow'
        uiscale = ba.app.ui.uiscale
        self._width = 800 if uiscale is ba.UIScale.SMALL else 600
        x_inset = 100 if uiscale is ba.UIScale.SMALL else 0
        self._height = (340 if uiscale is ba.UIScale.SMALL else
                        370 if uiscale is ba.UIScale.MEDIUM else 440)
        spacing = 40.0
        v = self._height - 40.0
        v -= spacing * 1.0

        super().__init__(root_widget=ba.containerwidget(
            size=(self._width, self._height),
            transition=transition,
            toolbar_visibility='menu_minimal',
            scale_origin_stack_offset=scale_origin,
            scale=(2.3 if uiscale is ba.UIScale.SMALL else
                   1.6 if uiscale is ba.UIScale.MEDIUM else 1.0),
            stack_offset=(0, -18) if uiscale is ba.UIScale.SMALL else (0, 0)))

        if ba.app.ui.use_toolbars and uiscale is ba.UIScale.SMALL:
            self._back_button = None
        else:
            self._back_button = ba.buttonwidget(
                parent=self._root_widget,
                position=(45 + x_inset, self._height - 60),
                size=(120, 60),
                scale=0.8,
                label=ba.Lstr(resource='backText'),
                button_type='back',
                autoselect=True)
            ba.buttonwidget(edit=self._back_button,
                            button_type='backSmall',
                            size=(60, 60),
                            label=ba.charstr(ba.SpecialChar.BACK))
        ba.textwidget(parent=self._root_widget,
                      position=(self._width * 0.5, self._height - 35),
                      size=(0, 0),
                      maxwidth=300,
                      text=ba.Lstr(resource=self._r + '.titleText'),
                      color=ba.app.ui.title_color,
                      h_align='center',
                      v_align='center')

        h = 43 + x_inset
        v = self._height - 60
        b_color = (0.6, 0.53, 0.63)
        b_textcolor = (0.75, 0.7, 0.8)
        lock_tex = ba.gettexture('lock')
        self._lock_images: List[ba.Widget] = []

        scl = (1.0 if uiscale is ba.UIScale.SMALL else
               1.13 if uiscale is ba.UIScale.MEDIUM else 1.4)
        v -= 60.0 * scl
        self._new_button = btn = ba.buttonwidget(
            parent=self._root_widget,
            position=(h, v),
            size=(100, 55.0 * scl),
            on_activate_call=self._new_soundtrack,
            color=b_color,
            button_type='square',
            autoselect=True,
            textcolor=b_textcolor,
            text_scale=0.7,
            label=ba.Lstr(resource=self._r + '.newText'))
        self._lock_images.append(
            ba.imagewidget(parent=self._root_widget,
                           size=(30, 30),
                           draw_controller=btn,
                           position=(h - 10, v + 55.0 * scl - 28),
                           texture=lock_tex))

        if self._back_button is None:
            ba.widget(edit=btn,
                      left_widget=_ba.get_special_widget('back_button'))
        v -= 60.0 * scl

        self._edit_button = btn = ba.buttonwidget(
            parent=self._root_widget,
            position=(h, v),
            size=(100, 55.0 * scl),
            on_activate_call=self._edit_soundtrack,
            color=b_color,
            button_type='square',
            autoselect=True,
            textcolor=b_textcolor,
            text_scale=0.7,
            label=ba.Lstr(resource=self._r + '.editText'))
        self._lock_images.append(
            ba.imagewidget(parent=self._root_widget,
                           size=(30, 30),
                           draw_controller=btn,
                           position=(h - 10, v + 55.0 * scl - 28),
                           texture=lock_tex))
        if self._back_button is None:
            ba.widget(edit=btn,
                      left_widget=_ba.get_special_widget('back_button'))
        v -= 60.0 * scl

        self._duplicate_button = btn = ba.buttonwidget(
            parent=self._root_widget,
            position=(h, v),
            size=(100, 55.0 * scl),
            on_activate_call=self._duplicate_soundtrack,
            button_type='square',
            autoselect=True,
            color=b_color,
            textcolor=b_textcolor,
            text_scale=0.7,
            label=ba.Lstr(resource=self._r + '.duplicateText'))
        self._lock_images.append(
            ba.imagewidget(parent=self._root_widget,
                           size=(30, 30),
                           draw_controller=btn,
                           position=(h - 10, v + 55.0 * scl - 28),
                           texture=lock_tex))
        if self._back_button is None:
            ba.widget(edit=btn,
                      left_widget=_ba.get_special_widget('back_button'))
        v -= 60.0 * scl

        self._delete_button = btn = ba.buttonwidget(
            parent=self._root_widget,
            position=(h, v),
            size=(100, 55.0 * scl),
            on_activate_call=self._delete_soundtrack,
            color=b_color,
            button_type='square',
            autoselect=True,
            textcolor=b_textcolor,
            text_scale=0.7,
            label=ba.Lstr(resource=self._r + '.deleteText'))
        self._lock_images.append(
            ba.imagewidget(parent=self._root_widget,
                           size=(30, 30),
                           draw_controller=btn,
                           position=(h - 10, v + 55.0 * scl - 28),
                           texture=lock_tex))
        if self._back_button is None:
            ba.widget(edit=btn,
                      left_widget=_ba.get_special_widget('back_button'))

        # Keep our lock images up to date/etc.
        self._update_timer = ba.Timer(1.0,
                                      ba.WeakCall(self._update),
                                      timetype=ba.TimeType.REAL,
                                      repeat=True)
        self._update()

        v = self._height - 65
        scroll_height = self._height - 105
        v -= scroll_height
        self._scrollwidget = scrollwidget = ba.scrollwidget(
            parent=self._root_widget,
            position=(152 + x_inset, v),
            highlight=False,
            size=(self._width - (205 + 2 * x_inset), scroll_height))
        ba.widget(edit=self._scrollwidget,
                  left_widget=self._new_button,
                  right_widget=_ba.get_special_widget('party_button')
                  if ba.app.ui.use_toolbars else self._scrollwidget)
        self._col = ba.columnwidget(parent=scrollwidget, border=2, margin=0)

        self._soundtracks: Optional[Dict[str, Any]] = None
        self._selected_soundtrack: Optional[str] = None
        self._selected_soundtrack_index: Optional[int] = None
        self._soundtrack_widgets: List[ba.Widget] = []
        self._allow_changing_soundtracks = False
        self._refresh()
        if self._back_button is not None:
            ba.buttonwidget(edit=self._back_button,
                            on_activate_call=self._back)
            ba.containerwidget(edit=self._root_widget,
                               cancel_button=self._back_button)
        else:
            ba.containerwidget(edit=self._root_widget,
                               on_cancel_call=self._back)

    def _update(self) -> None:
        from ba.internal import have_pro_options
        have = have_pro_options()
        for lock in self._lock_images:
            ba.imagewidget(edit=lock, opacity=0.0 if have else 1.0)

    def _do_delete_soundtrack(self) -> None:
        cfg = ba.app.config
        soundtracks = cfg.setdefault('Soundtracks', {})
        if self._selected_soundtrack in soundtracks:
            del soundtracks[self._selected_soundtrack]
        cfg.commit()
        ba.playsound(ba.getsound('shieldDown'))
        assert self._selected_soundtrack_index is not None
        assert self._soundtracks is not None
        if self._selected_soundtrack_index >= len(self._soundtracks):
            self._selected_soundtrack_index = len(self._soundtracks)
        self._refresh()

    def _delete_soundtrack(self) -> None:
        # pylint: disable=cyclic-import
        from ba.internal import have_pro_options
        from bastd.ui import purchase
        from bastd.ui import confirm
        if not have_pro_options():
            purchase.PurchaseWindow(items=['pro'])
            return
        if self._selected_soundtrack is None:
            return
        if self._selected_soundtrack == '__default__':
            ba.playsound(ba.getsound('error'))
            ba.screenmessage(ba.Lstr(resource=self._r +
                                     '.cantDeleteDefaultText'),
                             color=(1, 0, 0))
        else:
            confirm.ConfirmWindow(
                ba.Lstr(resource=self._r + '.deleteConfirmText',
                        subs=[('${NAME}', self._selected_soundtrack)]),
                self._do_delete_soundtrack, 450, 150)

    def _duplicate_soundtrack(self) -> None:
        # pylint: disable=cyclic-import
        from ba.internal import have_pro_options
        from bastd.ui import purchase
        if not have_pro_options():
            purchase.PurchaseWindow(items=['pro'])
            return
        cfg = ba.app.config
        cfg.setdefault('Soundtracks', {})

        if self._selected_soundtrack is None:
            return
        sdtk: Dict[str, Any]
        if self._selected_soundtrack == '__default__':
            sdtk = {}
        else:
            sdtk = cfg['Soundtracks'][self._selected_soundtrack]

        # Find a valid dup name that doesn't exist.
        test_index = 1
        copy_text = ba.Lstr(resource='copyOfText').evaluate()
        # Get just 'Copy' or whatnot.
        copy_word = copy_text.replace('${NAME}', '').strip()
        base_name = self._get_soundtrack_display_name(
            self._selected_soundtrack).evaluate()
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
        music = ba.app.music
        self._selected_soundtrack_index = index
        self._selected_soundtrack = name
        cfg = ba.app.config
        current_soundtrack = cfg.setdefault('Soundtrack', '__default__')

        # If it varies from current, commit and play.
        if current_soundtrack != name and self._allow_changing_soundtracks:
            ba.playsound(ba.getsound('gunCocking'))
            cfg['Soundtrack'] = self._selected_soundtrack
            cfg.commit()

            # Just play whats already playing.. this'll grab it from the
            # new soundtrack.
            music.do_play_music(music.music_types[ba.MusicPlayMode.REGULAR])

    def _back(self) -> None:
        # pylint: disable=cyclic-import
        from bastd.ui.settings import audio
        self._save_state()
        ba.containerwidget(edit=self._root_widget,
                           transition=self._transition_out)
        ba.app.ui.set_main_menu_window(
            audio.AudioSettingsWindow(transition='in_left').get_root_widget())

    def _edit_soundtrack_with_sound(self) -> None:
        # pylint: disable=cyclic-import
        from ba.internal import have_pro_options
        from bastd.ui import purchase
        if not have_pro_options():
            purchase.PurchaseWindow(items=['pro'])
            return
        ba.playsound(ba.getsound('swish'))
        self._edit_soundtrack()

    def _edit_soundtrack(self) -> None:
        # pylint: disable=cyclic-import
        from ba.internal import have_pro_options
        from bastd.ui import purchase
        from bastd.ui.soundtrack import edit as stedit
        if not have_pro_options():
            purchase.PurchaseWindow(items=['pro'])
            return
        if self._selected_soundtrack is None:
            return
        if self._selected_soundtrack == '__default__':
            ba.playsound(ba.getsound('error'))
            ba.screenmessage(ba.Lstr(resource=self._r +
                                     '.cantEditDefaultText'),
                             color=(1, 0, 0))
            return

        self._save_state()
        ba.containerwidget(edit=self._root_widget, transition='out_left')
        ba.app.ui.set_main_menu_window(
            stedit.SoundtrackEditWindow(
                existing_soundtrack=self._selected_soundtrack).get_root_widget(
                ))

    def _get_soundtrack_display_name(self, soundtrack: str) -> ba.Lstr:
        if soundtrack == '__default__':
            return ba.Lstr(resource=self._r + '.defaultSoundtrackNameText')
        return ba.Lstr(value=soundtrack)

    def _refresh(self, select_soundtrack: str = None) -> None:
        self._allow_changing_soundtracks = False
        old_selection = self._selected_soundtrack

        # If there was no prev selection, look in prefs.
        if old_selection is None:
            old_selection = ba.app.config.get('Soundtrack')
        old_selection_index = self._selected_soundtrack_index

        # Delete old.
        while self._soundtrack_widgets:
            self._soundtrack_widgets.pop().delete()

        self._soundtracks = ba.app.config.get('Soundtracks', {})
        assert self._soundtracks is not None
        items = list(self._soundtracks.items())
        items.sort(key=lambda x: x[0].lower())
        items = [('__default__', None)] + items  # default is always first
        index = 0
        for pname, _pval in items:
            assert pname is not None
            txtw = ba.textwidget(
                parent=self._col,
                size=(self._width - 40, 24),
                text=self._get_soundtrack_display_name(pname),
                h_align='left',
                v_align='center',
                maxwidth=self._width - 110,
                always_highlight=True,
                on_select_call=ba.WeakCall(self._select, pname, index),
                on_activate_call=self._edit_soundtrack_with_sound,
                selectable=True)
            if index == 0:
                ba.widget(edit=txtw, up_widget=self._back_button)
            self._soundtrack_widgets.append(txtw)

            # Select this one if the user requested it
            if select_soundtrack is not None:
                if pname == select_soundtrack:
                    ba.columnwidget(edit=self._col,
                                    selected_child=txtw,
                                    visible_child=txtw)
            else:
                # Select this one if it was previously selected.
                # Go by index if there's one.
                if old_selection_index is not None:
                    if index == old_selection_index:
                        ba.columnwidget(edit=self._col,
                                        selected_child=txtw,
                                        visible_child=txtw)
                else:  # Otherwise look by name.
                    if pname == old_selection:
                        ba.columnwidget(edit=self._col,
                                        selected_child=txtw,
                                        visible_child=txtw)
            index += 1

        # Explicitly run select callback on current one and re-enable
        # callbacks.

        # Eww need to run this in a timer so it happens after our select
        # callbacks. With a small-enough time sometimes it happens before
        # anyway. Ew. need a way to just schedule a callable i guess.
        ba.timer(0.1,
                 ba.WeakCall(self._set_allow_changing),
                 timetype=ba.TimeType.REAL)

    def _set_allow_changing(self) -> None:
        self._allow_changing_soundtracks = True
        assert self._selected_soundtrack is not None
        assert self._selected_soundtrack_index is not None
        self._select(self._selected_soundtrack,
                     self._selected_soundtrack_index)

    def _new_soundtrack(self) -> None:
        # pylint: disable=cyclic-import
        from ba.internal import have_pro_options
        from bastd.ui import purchase
        from bastd.ui.soundtrack import edit as stedit
        if not have_pro_options():
            purchase.PurchaseWindow(items=['pro'])
            return
        self._save_state()
        ba.containerwidget(edit=self._root_widget, transition='out_left')
        stedit.SoundtrackEditWindow(existing_soundtrack=None)

    def _create_done(self, new_soundtrack: str) -> None:
        if new_soundtrack is not None:
            ba.playsound(ba.getsound('gunCocking'))
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
            ba.app.ui.window_states[self.__class__.__name__] = sel_name
        except Exception:
            ba.print_exception(f'Error saving state for {self}.')

    def _restore_state(self) -> None:
        try:
            sel_name = ba.app.ui.window_states.get(self.__class__.__name__)
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
            ba.containerwidget(edit=self._root_widget, selected_child=sel)
        except Exception:
            ba.print_exception(f'Error restoring state for {self}.')
