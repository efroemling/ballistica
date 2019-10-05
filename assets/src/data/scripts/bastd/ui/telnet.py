"""UI functionality for telnet access."""

from __future__ import annotations

import _ba
import ba


class TelnetAccessRequestWindow(ba.OldWindow):
    """Window asking the user whether to allow a telnet connection."""

    def __init__(self) -> None:
        width = 400
        height = 100
        text = ba.Lstr(resource='telnetAccessText')

        super().__init__(root_widget=ba.containerwidget(
            size=(width, height + 40),
            transition='in_right',
            scale=1.7 if ba.app.small_ui else 1.3 if ba.app.med_ui else 1.0))
        padding = 20
        ba.textwidget(parent=self._root_widget,
                      position=(padding, padding + 33),
                      size=(width - 2 * padding, height - 2 * padding),
                      h_align="center",
                      v_align="top",
                      text=text)
        btn = ba.buttonwidget(parent=self._root_widget,
                              position=(20, 20),
                              size=(140, 50),
                              label=ba.Lstr(resource='denyText'),
                              on_activate_call=self._cancel)
        ba.containerwidget(edit=self._root_widget, cancel_button=btn)
        ba.containerwidget(edit=self._root_widget, selected_child=btn)

        ba.buttonwidget(parent=self._root_widget,
                        position=(width - 155, 20),
                        size=(140, 50),
                        label=ba.Lstr(resource='allowText'),
                        on_activate_call=self._ok)

    def _cancel(self) -> None:
        ba.containerwidget(edit=self._root_widget, transition='out_right')
        _ba.set_telnet_access_enabled(False)

    def _ok(self) -> None:
        ba.containerwidget(edit=self._root_widget, transition='out_left')
        _ba.set_telnet_access_enabled(True)
        ba.screenmessage(ba.Lstr(resource='telnetAccessGrantedText'))
