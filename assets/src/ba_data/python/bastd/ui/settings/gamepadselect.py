# Released under the MIT License. See LICENSE for details.
#
"""Settings UI related to gamepad functionality."""

from __future__ import annotations

from typing import TYPE_CHECKING

import ba
import ba.internal

if TYPE_CHECKING:
    from typing import Any


def gamepad_configure_callback(event: dict[str, Any]) -> None:
    """Respond to a gamepad button press during config selection."""
    from ba.internal import get_remote_app_name
    from bastd.ui.settings import gamepad

    # Ignore all but button-presses.
    if event['type'] not in ['BUTTONDOWN', 'HATMOTION']:
        return
    ba.internal.release_gamepad_input()
    try:
        ba.app.ui.clear_main_menu_window(transition='out_left')
    except Exception:
        ba.print_exception('Error transitioning out main_menu_window.')
    ba.playsound(ba.getsound('activateBeep'))
    ba.playsound(ba.getsound('swish'))
    inputdevice = event['input_device']
    assert isinstance(inputdevice, ba.InputDevice)
    if inputdevice.allows_configuring:
        ba.app.ui.set_main_menu_window(
            gamepad.GamepadSettingsWindow(inputdevice).get_root_widget()
        )
    else:
        width = 700
        height = 200
        button_width = 100
        uiscale = ba.app.ui.uiscale
        dlg = ba.containerwidget(
            scale=(
                1.7
                if uiscale is ba.UIScale.SMALL
                else 1.4
                if uiscale is ba.UIScale.MEDIUM
                else 1.0
            ),
            size=(width, height),
            transition='in_right',
        )
        ba.app.ui.set_main_menu_window(dlg)
        device_name = inputdevice.name
        if device_name == 'iDevice':
            msg = ba.Lstr(
                resource='bsRemoteConfigureInAppText',
                subs=[('${REMOTE_APP_NAME}', get_remote_app_name())],
            )
        else:
            msg = ba.Lstr(
                resource='cantConfigureDeviceText',
                subs=[('${DEVICE}', device_name)],
            )
        ba.textwidget(
            parent=dlg,
            position=(0, height - 80),
            size=(width, 25),
            text=msg,
            scale=0.8,
            h_align='center',
            v_align='top',
        )

        def _ok() -> None:
            from bastd.ui.settings import controls

            ba.containerwidget(edit=dlg, transition='out_right')
            ba.app.ui.set_main_menu_window(
                controls.ControlsSettingsWindow(
                    transition='in_left'
                ).get_root_widget()
            )

        ba.buttonwidget(
            parent=dlg,
            position=((width - button_width) / 2, 20),
            size=(button_width, 60),
            label=ba.Lstr(resource='okText'),
            on_activate_call=_ok,
        )


class GamepadSelectWindow(ba.Window):
    """Window for selecting a gamepad to configure."""

    def __init__(self) -> None:
        from typing import cast

        width = 480
        height = 170
        spacing = 40
        self._r = 'configGamepadSelectWindow'

        uiscale = ba.app.ui.uiscale
        super().__init__(
            root_widget=ba.containerwidget(
                scale=(
                    2.3
                    if uiscale is ba.UIScale.SMALL
                    else 1.5
                    if uiscale is ba.UIScale.MEDIUM
                    else 1.0
                ),
                size=(width, height),
                transition='in_right',
            )
        )

        btn = ba.buttonwidget(
            parent=self._root_widget,
            position=(20, height - 60),
            size=(130, 60),
            label=ba.Lstr(resource='backText'),
            button_type='back',
            scale=0.8,
            on_activate_call=self._back,
        )
        # Let's not have anything selected by default; its misleading looking
        # for the controller getting configured.
        ba.containerwidget(
            edit=self._root_widget,
            cancel_button=btn,
            selected_child=cast(ba.Widget, 0),
        )
        ba.textwidget(
            parent=self._root_widget,
            position=(20, height - 50),
            size=(width, 25),
            text=ba.Lstr(resource=self._r + '.titleText'),
            maxwidth=250,
            color=ba.app.ui.title_color,
            h_align='center',
            v_align='center',
        )

        ba.buttonwidget(
            edit=btn,
            button_type='backSmall',
            size=(60, 60),
            label=ba.charstr(ba.SpecialChar.BACK),
        )

        v: float = height - 60
        v -= spacing
        ba.textwidget(
            parent=self._root_widget,
            position=(15, v),
            size=(width - 30, 30),
            scale=0.8,
            text=ba.Lstr(resource=self._r + '.pressAnyButtonText'),
            maxwidth=width * 0.95,
            color=ba.app.ui.infotextcolor,
            h_align='center',
            v_align='top',
        )
        v -= spacing * 1.24
        if ba.app.platform == 'android':
            ba.textwidget(
                parent=self._root_widget,
                position=(15, v),
                size=(width - 30, 30),
                scale=0.46,
                text=ba.Lstr(resource=self._r + '.androidNoteText'),
                maxwidth=width * 0.95,
                color=(0.7, 0.9, 0.7, 0.5),
                h_align='center',
                v_align='top',
            )

        ba.internal.capture_gamepad_input(gamepad_configure_callback)

    def _back(self) -> None:
        from bastd.ui.settings import controls

        ba.internal.release_gamepad_input()
        ba.containerwidget(edit=self._root_widget, transition='out_right')
        ba.app.ui.set_main_menu_window(
            controls.ControlsSettingsWindow(
                transition='in_left'
            ).get_root_widget()
        )
