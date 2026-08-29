# Released under the MIT License. See LICENSE for details.
#
"""Provides audio settings UI."""

from typing import TYPE_CHECKING, override

import bauiv1 as bui
from bauiv1 import _commonassets, _classicassets

from bauiv1 import _builtinassets

if TYPE_CHECKING:
    pass


_audstrs = _classicassets.strings.settings.audio


class AudioSettingsWindow(bui.MainWindow):
    """Window for editing audio settings."""

    def __init__(
        self,
        transition: str | None = 'in_right',
        origin_widget: bui.Widget | None = None,
    ):
        # pylint: disable=cyclic-import
        from bauiv1lib.config import ConfigSlider

        assert bui.app.classic is not None
        music = bui.app.classic.music

        self._r = 'audioSettingsWindow'

        spacing = 50.0
        uiscale = bui.app.ui_v1.uiscale

        width = 1200.0 if uiscale is bui.UIScale.SMALL else 620.0
        height = 800.0 if uiscale is bui.UIScale.SMALL else 350.0

        show_soundtracks = False
        if music.have_music_player():
            show_soundtracks = True

        # Do some fancy math to fill all available screen area up to the
        # size of our backing container. This lets us fit to the exact
        # screen shape at small ui scale.
        screensize = bui.get_virtual_screen_size()
        scale = (
            2.0
            if uiscale is bui.UIScale.SMALL
            else 1.5 if uiscale is bui.UIScale.MEDIUM else 1.0
        )
        # Calc screen size in our local container space and clamp to a
        # bit smaller than our container size.
        # target_width = min(width - 60, screensize[0] / scale)
        target_height = min(height - 70, screensize[1] / scale)

        # To get top/left coords, go to the center of our window and
        # offset by half the width/height of our target area.
        yoffs = 0.5 * height + 0.5 * target_height + 30.0

        super().__init__(
            root_widget=bui.containerwidget(
                size=(width, height),
                scale=scale,
                toolbar_visibility=(
                    'menu_full' if bui.in_main_menu() else 'menu_minimal'
                ),
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
                id=f'{self.main_window_id_prefix}|back',
                position=(35, yoffs - 55),
                size=(60, 60),
                scale=0.8,
                text_scale=1.2,
                label=bui.charstr(bui.SpecialChar.BACK),
                button_type='backSmall',
                on_activate_call=self.main_window_back,
                autoselect=True,
            )
            bui.containerwidget(
                edit=self._root_widget, cancel_button=self._back_button
            )

        bui.textwidget(
            parent=self._root_widget,
            position=(
                width * 0.5,
                yoffs - (48 if uiscale is bui.UIScale.SMALL else 32),
            ),
            size=(0, 0),
            text=_audstrs.title,
            color=bui.app.ui_v1.title_color,
            maxwidth=180,
            h_align='center',
            v_align='center',
        )

        # Roughly center everything else in our window. The offset is half
        # the width of a settings row: its label starts here and its
        # controls end 440 out (230 to the controls, plus a 200 slider and
        # the 10 xoffset below).
        x = width * 0.5 - 220
        y = height * 0.5 + (100 if show_soundtracks else 70)
        y -= spacing * 1.0

        swish = _builtinassets.audio.swish.get()
        self._sound_volume_slider = svs = ConfigSlider(
            parent=self._root_widget,
            idprefix=f'{self.main_window_id_prefix}|soundvolume',
            position=(x, y),
            xoffset=10,
            width=200.0,
            configkey='Sound Volume',
            displayname=_audstrs.sound_volume,
            minval=0.0,
            maxval=1.0,
            increment=0.05,
            as_percent=True,
            # Fires once per applied value -- the throttled cadence while
            # dragging, and always for the value settled on -- so the
            # level being set is audible as it is set.
            callback=lambda _v: swish.play(),
            # Slower than music's: each apply here is an audible blip, and
            # they run together if they come much faster than this.
            drag_apply_interval=1.0 / 3.0,
        )
        y -= spacing
        self._music_volume_slider = ConfigSlider(
            parent=self._root_widget,
            idprefix=f'{self.main_window_id_prefix}|musicvolume',
            position=(x, y),
            xoffset=10,
            width=200.0,
            configkey='Music Volume',
            displayname=_audstrs.music_volume,
            minval=0.0,
            maxval=1.0,
            increment=0.05,
            callback=music.music_volume_changed,
            # Faster than the default: nothing audible accompanies an
            # apply here, so this is free to track a drag more closely.
            drag_apply_interval=0.25,
            as_percent=True,
        )

        y -= 0.5 * spacing

        self._soundtrack_button: bui.Widget | None
        if show_soundtracks:
            y -= 1.2 * spacing
            self._soundtrack_button = bui.buttonwidget(
                parent=self._root_widget,
                id=f'{self.main_window_id_prefix}|soundtrack',
                position=(width * 0.5 - 155, y),
                size=(310, 50),
                autoselect=True,
                label=_audstrs.soundtracks,
                on_activate_call=self._do_soundtracks,
            )
            y -= spacing * 0.3
            bui.textwidget(
                parent=self._root_widget,
                position=(0.5 * width, y),
                size=(0.0, 0.0),
                text=_audstrs.soundtrack_description,
                flatness=1.0,
                h_align='center',
                v_align='center',
                maxwidth=400,
                scale=0.5,
                color=(0.7, 0.8, 0.7, 1.0),
            )
        else:
            self._soundtrack_button = None

        # Tweak a few navigation bits. Note that sliders consume left and
        # right to adjust their value, so only the vertical links here do
        # anything -- horizontal ones would never be followed.
        if self._back_button is not None:
            bui.widget(edit=self._back_button, down_widget=svs.slider)
        else:
            spback = bui.get_special_widget('back_button')
            bui.widget(edit=svs.slider, up_widget=spback)

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
    def main_window_should_preserve_selection(self) -> bool:
        return True

    def _do_soundtracks(self) -> None:
        # pylint: disable=cyclic-import
        from bauiv1lib.soundtrack.browser import SoundtrackBrowserWindow

        # no-op if we're not in control.
        if not self.main_window_has_control():
            return

        # We require disk access for soundtracks; request it if we don't
        # have it.
        if not bui.have_permission(bui.Permission.STORAGE):
            _builtinassets.audio.ding.get().play()
            bui.screenmessage(
                _commonassets.strings.status.storage_permission_needed,
                color=(0.5, 1, 0.5),
            )
            bui.apptimer(
                1.0,
                bui.CallStrict(bui.request_permission, bui.Permission.STORAGE),
            )
            return

        self.main_window_replace(
            lambda: SoundtrackBrowserWindow(
                origin_widget=self._soundtrack_button
            )
        )
