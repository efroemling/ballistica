# Released under the MIT License. See LICENSE for details.
#
"""Settings UI related to gamepad functionality."""

from typing import TYPE_CHECKING, override

import bascenev1 as bs
import bauiv1 as bui
from bauiv1 import _commonassets, _classicassets

from bauiv1 import _uiv1assets

if TYPE_CHECKING:
    from typing import Any


_ctlstrs = _classicassets.strings.settings.controllers


class GamepadSelectWindow(bui.MainWindow):
    """Window for selecting a gamepad to configure."""

    def __init__(
        self,
        transition: str | None = 'in_right',
        origin_widget: bui.Widget | None = None,
    ) -> None:
        from typing import cast

        spacing = 40
        self._r = 'configGamepadSelectWindow'

        assert bui.app.classic is not None
        uiscale = bui.app.ui_v1.uiscale

        # At small ui-scale we fill the screen and lean on the toolbar's
        # back button; elsewhere we're a small floating panel.
        width = 1200.0 if uiscale is bui.UIScale.SMALL else 480.0
        height = 800.0 if uiscale is bui.UIScale.SMALL else 170.0

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
        target_height = min(height - 70, screensize[1] / scale)

        # To get top/left coords, go to the center of our window and
        # offset by half the width/height of our target area.
        yoffs = 0.5 * height + 0.5 * target_height + 30.0

        super().__init__(
            root_widget=bui.containerwidget(
                scale=scale,
                size=(width, height),
                toolbar_visibility=(
                    'menu_minimal'
                    if uiscale is bui.UIScale.SMALL
                    else 'menu_full'
                ),
            ),
            transition=transition,
            origin_widget=origin_widget,
            # We're affected by screen size only at small ui-scale.
            refresh_on_screen_size_changes=uiscale is bui.UIScale.SMALL,
        )

        btn: bui.Widget | None
        if uiscale is bui.UIScale.SMALL:
            # The toolbar's back button serves here.
            btn = None
            bui.containerwidget(
                edit=self._root_widget, on_cancel_call=self.main_window_back
            )
        else:
            btn = bui.buttonwidget(
                parent=self._root_widget,
                position=(20, height - 60),
                size=(60, 60),
                label=bui.charstr(bui.SpecialChar.BACK),
                button_type='backSmall',
                scale=0.8,
                on_activate_call=self.main_window_back,
            )
            bui.containerwidget(edit=self._root_widget, cancel_button=btn)

        # Let's not have anything selected by default; its misleading
        # looking for the controller getting configured.
        bui.containerwidget(
            edit=self._root_widget,
            selected_child=cast(bui.Widget, 0),
        )

        # At small ui-scale the title rides at the top of the visible
        # screen area and the body sits centered in all that space; at
        # other scales we're a short panel, so both stay packed together
        # near its top as before.
        show_android_note = bui.app.classic.platform == 'android'
        content_height: float = spacing
        if show_android_note:
            content_height += spacing * 1.24

        v: float
        if uiscale is bui.UIScale.SMALL:
            title_y = yoffs - 52
            v = height * 0.5 + content_height * 0.5
        else:
            title_y = height - 50
            v = height - 60 - spacing

        bui.textwidget(
            parent=self._root_widget,
            position=(width * 0.5, title_y),
            size=(0, 0),
            text=_ctlstrs.configure_controllers,
            maxwidth=250,
            color=bui.app.ui_v1.title_color,
            h_align='center',
            v_align='center',
        )
        bui.textwidget(
            parent=self._root_widget,
            position=(15, v),
            size=(width - 30, 30),
            scale=0.8,
            text=_ctlstrs.press_any_button_to_configure,
            maxwidth=min(width * 0.95, 420.0),
            color=bui.app.ui_v1.infotextcolor,
            h_align='center',
            v_align='top',
        )
        v -= spacing * 1.24
        if show_android_note:
            bui.textwidget(
                parent=self._root_widget,
                position=(15, v),
                size=(width - 30, 30),
                scale=0.46,
                text=_ctlstrs.android_note,
                maxwidth=min(width * 0.95, 420.0),
                color=(0.7, 0.9, 0.7, 0.5),
                h_align='center',
                v_align='top',
            )

        bs.capture_game_controller_input(
            bui.WeakCallPartial(self.gamepad_configure_callback)
        )

    def __del__(self) -> None:
        bs.release_game_controller_input()

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
        # Not really needed here.
        return False

    def gamepad_configure_callback(self, event: dict[str, Any]) -> None:
        """Respond to a gamepad button press during config selection."""
        from bauiv1lib.settings.gamepad import GamepadSettingsWindow

        # Ignore all but button-presses.
        if event['type'] not in ['BUTTONDOWN', 'HATMOTION']:
            return

        bs.release_game_controller_input()

        assert bui.app.classic is not None

        _classicassets.audio.activate_beep.get().play()
        _uiv1assets.audio.swish.get().play()
        device = event['input_device']
        assert isinstance(device, bs.InputDevice)

        # No matter where we redirect to, we want their back
        # functionality to skip over us and go to our parent.
        assert self.main_window_back_state is not None
        back_state = self.main_window_back_state

        if device.allows_configuring:
            self.main_window_replace(
                lambda: GamepadSettingsWindow(device), back_state=back_state
            )
        else:
            self.main_window_replace(
                lambda: _NotConfigurableWindow(device), back_state=back_state
            )


class _NotConfigurableWindow(bui.MainWindow):

    def __init__(
        self,
        device: bs.InputDevice,
        transition: str | None = 'in_right',
        origin_widget: bui.Widget | None = None,
    ) -> None:
        width = 700
        height = 200
        button_width = 80
        uiscale = bui.app.ui_v1.uiscale
        super().__init__(
            root_widget=bui.containerwidget(
                scale=(
                    1.7
                    if uiscale is bui.UIScale.SMALL
                    else (1.4 if uiscale is bui.UIScale.MEDIUM else 1.0)
                ),
                size=(width, height),
            ),
            transition=transition,
            origin_widget=origin_widget,
        )
        self.device = device

        if device.allows_configuring_in_system_settings:
            msg = _ctlstrs.configure_in_system_settings(device=device.name)
        elif device.is_controller_app:
            msg = _ctlstrs.remote_configured_in_app(
                remote_app_name=_classicassets.strings.ui.remote_app_name
            )
        else:
            msg = _ctlstrs.cant_configure_device(device=device.name)
        bui.textwidget(
            parent=self._root_widget,
            position=(0, height - 80),
            size=(width, 25),
            text=msg,
            scale=0.8,
            h_align='center',
            v_align='top',
        )

        btn = bui.buttonwidget(
            parent=self._root_widget,
            position=((width - button_width) / 2, 20),
            size=(button_width, 60),
            label=_commonassets.strings.actions.ok,
            on_activate_call=self.main_window_back,
        )
        bui.containerwidget(edit=self._root_widget, cancel_button=btn)

    @override
    def get_main_window_state(self) -> bui.MainWindowState:
        # Support recreating our window for back/refresh purposes.
        cls = type(self)

        # Pull stuff out of self here; if we do it in the lambda we'll
        # keep self alive which we don't want.
        device = self.device

        return bui.BasicMainWindowState(
            create_call=lambda transition, origin_widget: cls(
                device=device,
                transition=transition,
                origin_widget=origin_widget,
            )
        )
