# Released under the MIT License. See LICENSE for details.
#
"""Settings UI related to gamepad functionality."""

from __future__ import annotations

from typing import TYPE_CHECKING, override

import bascenev1 as bs
import bauiv1 as bui

if TYPE_CHECKING:
    from typing import Any


class GamepadSelectWindow(bui.MainWindow):
    """Window for selecting a gamepad to configure."""

    def __init__(
        self,
        transition: str | None = 'in_right',
        origin_widget: bui.Widget | None = None,
    ) -> None:
        from typing import cast

        width = 480
        height = 170
        spacing = 40
        self._r = 'configGamepadSelectWindow'

        assert bui.app.classic is not None
        uiscale = bui.app.ui_v1.uiscale
        super().__init__(
            root_widget=bui.containerwidget(
                scale=(
                    2.3
                    if uiscale is bui.UIScale.SMALL
                    else 1.5 if uiscale is bui.UIScale.MEDIUM else 1.0
                ),
                size=(width, height),
            ),
            transition=transition,
            origin_widget=origin_widget,
        )

        btn = bui.buttonwidget(
            parent=self._root_widget,
            position=(20, height - 60),
            size=(130, 60),
            label=bui.Lstr(resource='backText'),
            button_type='back',
            scale=0.8,
            on_activate_call=self.main_window_back,
        )

        # Let's not have anything selected by default; its misleading
        # looking for the controller getting configured.
        bui.containerwidget(
            edit=self._root_widget,
            cancel_button=btn,
            selected_child=cast(bui.Widget, 0),
        )
        bui.textwidget(
            parent=self._root_widget,
            position=(20, height - 50),
            size=(width, 25),
            text=bui.Lstr(resource=f'{self._r}.titleText'),
            maxwidth=250,
            color=bui.app.ui_v1.title_color,
            h_align='center',
            v_align='center',
        )

        bui.buttonwidget(
            edit=btn,
            button_type='backSmall',
            size=(60, 60),
            label=bui.charstr(bui.SpecialChar.BACK),
        )

        v: float = height - 60
        v -= spacing
        bui.textwidget(
            parent=self._root_widget,
            position=(15, v),
            size=(width - 30, 30),
            scale=0.8,
            text=bui.Lstr(resource=f'{self._r}.pressAnyButtonText'),
            maxwidth=width * 0.95,
            color=bui.app.ui_v1.infotextcolor,
            h_align='center',
            v_align='top',
        )
        v -= spacing * 1.24
        if bui.app.classic.platform == 'android':
            bui.textwidget(
                parent=self._root_widget,
                position=(15, v),
                size=(width - 30, 30),
                scale=0.46,
                text=bui.Lstr(resource=f'{self._r}.androidNoteText'),
                maxwidth=width * 0.95,
                color=(0.7, 0.9, 0.7, 0.5),
                h_align='center',
                v_align='top',
            )

        bs.capture_gamepad_input(bui.WeakCall(self.gamepad_configure_callback))

    def __del__(self) -> None:
        bs.release_gamepad_input()

    @override
    def get_main_window_state(self) -> bui.MainWindowState:
        # Support recreating our window for back/refresh purposes.
        cls = type(self)
        return bui.BasicMainWindowState(
            create_call=lambda transition, origin_widget: cls(
                transition=transition, origin_widget=origin_widget
            )
        )

    def gamepad_configure_callback(self, event: dict[str, Any]) -> None:
        """Respond to a gamepad button press during config selection."""
        from bauiv1lib.settings.gamepad import GamepadSettingsWindow

        if not self.main_window_has_control():
            return

        # Ignore all but button-presses.
        if event['type'] not in ['BUTTONDOWN', 'HATMOTION']:
            return
        bs.release_gamepad_input()

        assert bui.app.classic is not None

        bui.getsound('activateBeep').play()
        bui.getsound('swish').play()
        device = event['input_device']
        assert isinstance(device, bs.InputDevice)

        # No matter where we redirect to, we want their back
        # functionality to skip over us and go to our parent.
        assert self.main_window_back_state is not None
        back_state = self.main_window_back_state

        if device.allows_configuring:
            self.main_window_replace(
                GamepadSettingsWindow(device), back_state=back_state
            )
        else:
            self.main_window_replace(
                _NotConfigurableWindow(device), back_state=back_state
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
            msg = bui.Lstr(
                resource='configureDeviceInSystemSettingsText',
                subs=[('${DEVICE}', device.name)],
            )
        elif device.is_controller_app:
            msg = bui.Lstr(
                resource='bsRemoteConfigureInAppText',
                subs=[
                    (
                        '${REMOTE_APP_NAME}',
                        bui.get_remote_app_name(),
                    )
                ],
            )
        else:
            msg = bui.Lstr(
                resource='cantConfigureDeviceText',
                subs=[('${DEVICE}', device.name)],
            )
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
            label=bui.Lstr(resource='okText'),
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
