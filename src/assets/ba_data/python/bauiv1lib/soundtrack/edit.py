# Released under the MIT License. See LICENSE for details.
#
"""Provides UI for editing a soundtrack."""

from __future__ import annotations

import copy
import os
from typing import TYPE_CHECKING, cast, override

import bascenev1 as bs
import bauiv1 as bui

if TYPE_CHECKING:
    from typing import Any


class SoundtrackEditWindow(bui.MainWindow):
    """Window for editing a soundtrack."""

    def __init__(
        self,
        existing_soundtrack: str | dict[str, Any] | None,
        transition: str | None = 'in_right',
        origin_widget: bui.Widget | None = None,
    ):
        # pylint: disable=too-many-statements
        # pylint: disable=too-many-locals

        appconfig = bui.app.config
        self._r = 'editSoundtrackWindow'
        self._folder_tex = bui.gettexture('folder')
        self._file_tex = bui.gettexture('file')
        assert bui.app.classic is not None
        uiscale = bui.app.ui_v1.uiscale
        self._width = 1200 if uiscale is bui.UIScale.SMALL else 648
        self._height = (
            800
            if uiscale is bui.UIScale.SMALL
            else 450 if uiscale is bui.UIScale.MEDIUM else 560
        )

        # Do some fancy math to fill all available screen area up to the
        # size of our backing container. This lets us fit to the exact
        # screen shape at small ui scale.
        screensize = bui.get_virtual_screen_size()
        scale = (
            1.8
            if uiscale is bui.UIScale.SMALL
            else 1.5 if uiscale is bui.UIScale.MEDIUM else 1.0
        )
        # Calc screen size in our local container space and clamp to a
        # bit smaller than our container size.
        target_width = min(self._width - 70, screensize[0] / scale)
        target_height = min(self._height - 80, screensize[1] / scale)

        # To get top/left coords, go to the center of our window and
        # offset by half the width/height of our target area.
        yoffs = (
            0.5 * self._height
            + 0.5 * target_height
            + (10.0 if uiscale is bui.UIScale.SMALL else 20)
        )

        self._scroll_width = target_width
        self._scroll_height = target_height - 113
        scroll_bottom = yoffs - 120 - self._scroll_height

        x_inset = self._width * 0.5 - 0.5 * self._scroll_width

        super().__init__(
            root_widget=bui.containerwidget(
                size=(self._width, self._height), scale=scale
            ),
            transition=transition,
            origin_widget=origin_widget,
            # We're affected by screen size only at small ui-scale.
            refresh_on_screen_size_changes=uiscale is bui.UIScale.SMALL,
        )
        cancel_button = bui.buttonwidget(
            parent=self._root_widget,
            position=(x_inset + 10, yoffs - 60),
            size=(160, 60),
            autoselect=True,
            label=bui.Lstr(resource='cancelText'),
            scale=0.8,
        )
        save_button = bui.buttonwidget(
            parent=self._root_widget,
            position=(
                self._width * 0.5
                + self._scroll_width * 0.5
                - (190 if uiscale is bui.UIScale.SMALL else 140),
                yoffs - 60,
            ),
            autoselect=True,
            size=(160, 60),
            label=bui.Lstr(resource='saveText'),
            scale=0.8,
        )
        bui.widget(edit=save_button, left_widget=cancel_button)
        bui.widget(edit=cancel_button, right_widget=save_button)
        bui.textwidget(
            parent=self._root_widget,
            position=(0, yoffs - 50),
            size=(self._width, 25),
            text=bui.Lstr(
                resource=self._r
                + (
                    '.editSoundtrackText'
                    if existing_soundtrack is not None
                    else '.newSoundtrackText'
                )
            ),
            color=bui.app.ui_v1.title_color,
            h_align='center',
            v_align='center',
            maxwidth=270,
        )
        v = yoffs - 110
        if 'Soundtracks' not in appconfig:
            appconfig['Soundtracks'] = {}

        self._soundtrack_name: str | None
        self._existing_soundtrack = existing_soundtrack
        self._existing_soundtrack_name: str | None
        if existing_soundtrack is not None:
            # if they passed just a name, pull info from that soundtrack
            if isinstance(existing_soundtrack, str):
                self._soundtrack = copy.deepcopy(
                    appconfig['Soundtracks'][existing_soundtrack]
                )
                self._soundtrack_name = existing_soundtrack
                self._existing_soundtrack_name = existing_soundtrack
                self._last_edited_song_type = None
            else:
                # Otherwise they can pass info on an in-progress edit.
                self._soundtrack = existing_soundtrack['soundtrack']
                self._soundtrack_name = existing_soundtrack['name']
                self._existing_soundtrack_name = existing_soundtrack[
                    'existing_name'
                ]
                self._last_edited_song_type = existing_soundtrack[
                    'last_edited_song_type'
                ]
        else:
            self._soundtrack_name = None
            self._existing_soundtrack_name = None
            self._soundtrack = {}
            self._last_edited_song_type = None

        bui.textwidget(
            parent=self._root_widget,
            text=bui.Lstr(resource=f'{self._r}.nameText'),
            maxwidth=80,
            scale=0.8,
            position=(105 + x_inset, v + 19),
            color=(0.8, 0.8, 0.8, 0.5),
            size=(0, 0),
            h_align='right',
            v_align='center',
        )

        # if there's no initial value, find a good initial unused name
        if existing_soundtrack is None:
            i = 1
            st_name_text = bui.Lstr(
                resource=f'{self._r}.newSoundtrackNameText'
            ).evaluate()
            if '${COUNT}' not in st_name_text:
                # make sure we insert number *somewhere*
                st_name_text = st_name_text + ' ${COUNT}'
            while True:
                self._soundtrack_name = st_name_text.replace('${COUNT}', str(i))
                if self._soundtrack_name not in appconfig['Soundtracks']:
                    break
                i += 1

        self._text_field = bui.textwidget(
            parent=self._root_widget,
            position=(120 + x_inset, v - 5),
            size=(self._width - (160 + 2 * x_inset), 43),
            text=self._soundtrack_name,
            h_align='left',
            v_align='center',
            max_chars=32,
            autoselect=True,
            description=bui.Lstr(resource=f'{self._r}.nameText'),
            editable=True,
            padding=4,
            on_return_press_call=self._do_it_with_sound,
        )

        self._scrollwidget = scrollwidget = bui.scrollwidget(
            parent=self._root_widget,
            highlight=False,
            size=(self._scroll_width, self._scroll_height),
            position=(
                self._width * 0.5 - self._scroll_width * 0.5,
                scroll_bottom,
            ),
            simple_culling_v=10,
            claims_left_right=True,
            selection_loops_to_parent=True,
            border_opacity=0.4,
        )
        bui.widget(edit=self._text_field, down_widget=self._scrollwidget)
        self._col = bui.columnwidget(
            parent=scrollwidget,
            claims_left_right=True,
            selection_loops_to_parent=True,
        )

        self._song_type_buttons: dict[str, bui.Widget] = {}
        self._refresh()
        bui.buttonwidget(edit=cancel_button, on_activate_call=self._cancel)
        bui.containerwidget(edit=self._root_widget, cancel_button=cancel_button)
        bui.buttonwidget(edit=save_button, on_activate_call=self._do_it)
        bui.containerwidget(edit=self._root_widget, start_button=save_button)
        bui.widget(edit=self._text_field, up_widget=cancel_button)
        bui.widget(edit=cancel_button, down_widget=self._text_field)

    @override
    def get_main_window_state(self) -> bui.MainWindowState:
        # Support recreating our window for back/refresh purposes.
        cls = type(self)

        # Pull this out of self here; if we do it in the lambda we'll
        # keep our window alive due to the 'self' reference.
        existing_soundtrack = {
            'name': self._soundtrack_name,
            'existing_name': self._existing_soundtrack_name,
            'soundtrack': self._soundtrack,
            'last_edited_song_type': self._last_edited_song_type,
        }

        return bui.BasicMainWindowState(
            create_call=lambda transition, origin_widget: cls(
                transition=transition,
                origin_widget=origin_widget,
                existing_soundtrack=existing_soundtrack,
            )
        )

    def _refresh(self) -> None:
        for widget in self._col.get_children():
            widget.delete()

        types = [
            'Menu',
            'CharSelect',
            'ToTheDeath',
            'Onslaught',
            'Keep Away',
            'Race',
            'Epic Race',
            'ForwardMarch',
            'FlagCatcher',
            'Survival',
            'Epic',
            'Hockey',
            'Football',
            'Flying',
            'Scary',
            'Marching',
            'GrandRomp',
            'Chosen One',
            'Scores',
            'Victory',
        ]

        # FIXME: We should probably convert this to use translations.
        type_names_translated = bui.app.lang.get_resource('soundtrackTypeNames')
        prev_type_button: bui.Widget | None = None
        prev_test_button: bui.Widget | None = None

        for index, song_type in enumerate(types):
            row = bui.rowwidget(
                parent=self._col,
                size=(self._scroll_width, 40),
                claims_left_right=True,
                selection_loops_to_parent=True,
            )
            type_name = type_names_translated.get(song_type, song_type)
            bui.textwidget(
                parent=row,
                size=(self._scroll_width - 350, 25),
                always_highlight=True,
                text=type_name,
                scale=0.7,
                h_align='left',
                v_align='center',
                maxwidth=self._scroll_width - 360,
            )

            if song_type in self._soundtrack:
                entry = self._soundtrack[song_type]
            else:
                entry = None

            if entry is not None:
                # Make sure they don't muck with this after it gets to us.
                entry = copy.deepcopy(entry)

            icon_type = self._get_entry_button_display_icon_type(entry)
            self._song_type_buttons[song_type] = btn = bui.buttonwidget(
                parent=row,
                size=(230, 32),
                label=self._get_entry_button_display_name(entry),
                text_scale=0.6,
                on_activate_call=bui.Call(
                    self._get_entry, song_type, entry, type_name
                ),
                icon=(
                    self._file_tex
                    if icon_type == 'file'
                    else self._folder_tex if icon_type == 'folder' else None
                ),
                icon_color=(
                    (1.1, 0.8, 0.2) if icon_type == 'folder' else (1, 1, 1)
                ),
                left_widget=self._text_field,
                iconscale=0.7,
                autoselect=True,
                up_widget=prev_type_button,
            )
            if index == 0:
                bui.widget(edit=btn, up_widget=self._text_field)
            bui.widget(edit=btn, down_widget=btn)

            if (
                self._last_edited_song_type is not None
                and song_type == self._last_edited_song_type
            ):
                bui.containerwidget(
                    edit=row, selected_child=btn, visible_child=btn
                )
                bui.containerwidget(
                    edit=self._col, selected_child=row, visible_child=row
                )
                bui.containerwidget(
                    edit=self._scrollwidget,
                    selected_child=self._col,
                    visible_child=self._col,
                )
                bui.containerwidget(
                    edit=self._root_widget,
                    selected_child=self._scrollwidget,
                    visible_child=self._scrollwidget,
                )

            if prev_type_button is not None:
                bui.widget(edit=prev_type_button, down_widget=btn)
            prev_type_button = btn
            bui.textwidget(parent=row, size=(10, 32), text='')  # spacing
            assert bui.app.classic is not None
            btn = bui.buttonwidget(
                parent=row,
                size=(50, 32),
                label=bui.Lstr(resource=f'{self._r}.testText'),
                text_scale=0.6,
                on_activate_call=bui.Call(self._test, bs.MusicType(song_type)),
                up_widget=(
                    prev_test_button
                    if prev_test_button is not None
                    else self._text_field
                ),
            )
            if prev_test_button is not None:
                bui.widget(edit=prev_test_button, down_widget=btn)
            bui.widget(edit=btn, down_widget=btn, right_widget=btn)
            prev_test_button = btn

    @classmethod
    def _restore_editor(
        cls, state: dict[str, Any], musictype: str, entry: Any
    ) -> None:
        assert bui.app.classic is not None
        music = bui.app.classic.music

        # Apply the change and recreate the window.
        soundtrack = state['soundtrack']
        existing_entry = (
            None if musictype not in soundtrack else soundtrack[musictype]
        )
        if existing_entry != entry:
            bui.getsound('gunCocking').play()

        # Make sure this doesn't get mucked with after we get it.
        if entry is not None:
            entry = copy.deepcopy(entry)

        entry_type = music.get_soundtrack_entry_type(entry)
        if entry_type == 'default':
            # For 'default' entries simply exclude them from the list.
            if musictype in soundtrack:
                del soundtrack[musictype]
        else:
            soundtrack[musictype] = entry

        mainwindow = bui.app.ui_v1.get_main_window()
        assert mainwindow is not None

        mainwindow.main_window_back_state = state['back_state']
        mainwindow.main_window_back()

    def _get_entry(
        self, song_type: str, entry: Any, selection_target_name: str
    ) -> None:
        assert bui.app.classic is not None
        music = bui.app.classic.music

        # no-op if we're not in control.
        if not self.main_window_has_control():
            return

        if selection_target_name != '':
            selection_target_name = "'" + selection_target_name + "'"
        state = {
            'name': self._soundtrack_name,
            'existing_name': self._existing_soundtrack_name,
            'soundtrack': self._soundtrack,
            'last_edited_song_type': song_type,
        }
        new_win = music.get_music_player().select_entry(
            bui.Call(self._restore_editor, state, song_type),
            entry,
            selection_target_name,
        )
        self.main_window_replace(new_win)

        # Once we've set the new window, grab the back-state; we'll use
        # that to jump back here after selection completes.
        assert new_win.main_window_back_state is not None
        state['back_state'] = new_win.main_window_back_state

    def _test(self, song_type: bs.MusicType) -> None:
        assert bui.app.classic is not None
        music = bui.app.classic.music

        # Warn if volume is zero.
        if bui.app.config.resolve('Music Volume') < 0.01:
            bui.getsound('error').play()
            bui.screenmessage(
                bui.Lstr(resource=f'{self._r}.musicVolumeZeroWarning'),
                color=(1, 0.5, 0),
            )
        music.set_music_play_mode(bui.app.classic.MusicPlayMode.TEST)
        music.do_play_music(
            song_type,
            mode=bui.app.classic.MusicPlayMode.TEST,
            testsoundtrack=self._soundtrack,
        )

    def _get_entry_button_display_name(self, entry: Any) -> str | bui.Lstr:
        assert bui.app.classic is not None
        music = bui.app.classic.music
        etype = music.get_soundtrack_entry_type(entry)
        ename: str | bui.Lstr
        if etype == 'default':
            ename = bui.Lstr(resource=f'{self._r}.defaultGameMusicText')
        elif etype in ('musicFile', 'musicFolder'):
            ename = os.path.basename(music.get_soundtrack_entry_name(entry))
        else:
            ename = music.get_soundtrack_entry_name(entry)
        return ename

    def _get_entry_button_display_icon_type(self, entry: Any) -> str | None:
        assert bui.app.classic is not None
        music = bui.app.classic.music
        etype = music.get_soundtrack_entry_type(entry)
        if etype == 'musicFile':
            return 'file'
        if etype == 'musicFolder':
            return 'folder'
        return None

    def _cancel(self) -> None:
        # from bauiv1lib.soundtrack.browser import SoundtrackBrowserWindow

        # no-op if our underlying widget is dead or on its way out.
        if not self._root_widget or self._root_widget.transitioning_out:
            return

        assert bui.app.classic is not None
        music = bui.app.classic.music

        # Resets music back to normal.
        music.set_music_play_mode(bui.app.classic.MusicPlayMode.REGULAR)

        self.main_window_back()

    def _do_it(self) -> None:

        # no-op if our underlying widget is dead or on its way out.
        if not self._root_widget or self._root_widget.transitioning_out:
            return

        assert bui.app.classic is not None
        music = bui.app.classic.music
        cfg = bui.app.config
        new_name = cast(str, bui.textwidget(query=self._text_field))
        if new_name != self._soundtrack_name and new_name in cfg['Soundtracks']:
            bui.screenmessage(
                bui.Lstr(resource=f'{self._r}.cantSaveAlreadyExistsText')
            )
            bui.getsound('error').play()
            return
        if not new_name:
            bui.getsound('error').play()
            return
        if (
            new_name
            == bui.Lstr(
                resource=f'{self._r}.defaultSoundtrackNameText'
            ).evaluate()
        ):
            bui.screenmessage(
                bui.Lstr(resource=f'{self._r}.cantOverwriteDefaultText')
            )
            bui.getsound('error').play()
            return

        # Make sure config exists.
        if 'Soundtracks' not in cfg:
            cfg['Soundtracks'] = {}

        # If we had an old one, delete it.
        if (
            self._existing_soundtrack_name is not None
            and self._existing_soundtrack_name in cfg['Soundtracks']
        ):
            del cfg['Soundtracks'][self._existing_soundtrack_name]
        cfg['Soundtracks'][new_name] = self._soundtrack
        cfg['Soundtrack'] = new_name

        cfg.commit()
        bui.getsound('gunCocking').play()

        # Resets music back to normal.
        music.set_music_play_mode(
            bui.app.classic.MusicPlayMode.REGULAR, force_restart=True
        )

        self.main_window_back()

    def _do_it_with_sound(self) -> None:
        bui.getsound('swish').play()
        self._do_it()
