# Released under the MIT License. See LICENSE for details.
#
"""Dialog window controlled by the master server."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Annotated

from efro.dataclassio import ioprepped, IOAttrs

import ba
import ba.internal

if TYPE_CHECKING:
    pass


@ioprepped
@dataclass
class ServerDialogData:
    """Data for ServerDialog."""

    dialog_id: Annotated[str, IOAttrs('dialogID')]
    text: Annotated[str, IOAttrs('text')]
    subs: Annotated[list[tuple[str, str]], IOAttrs('subs')] = field(
        default_factory=list
    )
    show_cancel: Annotated[bool, IOAttrs('showCancel')] = True
    copy_text: Annotated[str | None, IOAttrs('copyText')] = None


class ServerDialogWindow(ba.Window):
    """A dialog window driven by the master-server."""

    def __init__(self, data: ServerDialogData):
        self._data = data
        txt = ba.Lstr(
            translate=('serverResponses', data.text), subs=data.subs
        ).evaluate()
        txt = txt.strip()
        txt_scale = 1.5
        txt_height = (
            ba.internal.get_string_height(txt, suppress_warning=True)
            * txt_scale
        )
        self._width = 500
        self._height = 160 + min(200, txt_height)
        uiscale = ba.app.ui.uiscale
        super().__init__(
            root_widget=ba.containerwidget(
                size=(self._width, self._height),
                transition='in_scale',
                scale=(
                    1.8
                    if uiscale is ba.UIScale.SMALL
                    else 1.35
                    if uiscale is ba.UIScale.MEDIUM
                    else 1.0
                ),
            )
        )
        self._starttime = ba.time(ba.TimeType.REAL)

        ba.playsound(ba.getsound('swish'))
        ba.textwidget(
            parent=self._root_widget,
            position=(self._width * 0.5, 70 + (self._height - 70) * 0.5),
            size=(0, 0),
            color=(1.0, 3.0, 1.0),
            scale=txt_scale,
            h_align='center',
            v_align='center',
            text=txt,
            maxwidth=self._width * 0.85,
            max_height=(self._height - 110),
        )

        show_copy = data.copy_text is not None and ba.clipboard_is_supported()

        # Currently can't do both copy and cancel since they go in the same
        # spot. Cancel wins in this case since it is important functionality
        # and copy is just for convenience (and not even always available).
        if show_copy and data.show_cancel:
            logging.warning(
                'serverdialog requesting both copy and cancel;'
                ' copy will not be shown.'
            )
            show_copy = False

        self._cancel_button = (
            None
            if not data.show_cancel
            else ba.buttonwidget(
                parent=self._root_widget,
                position=(30, 30),
                size=(160, 60),
                autoselect=True,
                label=ba.Lstr(resource='cancelText'),
                on_activate_call=self._cancel_press,
            )
        )

        self._copy_button = (
            None
            if not show_copy
            else ba.buttonwidget(
                parent=self._root_widget,
                position=(30, 30),
                size=(160, 60),
                autoselect=True,
                label=ba.Lstr(resource='copyText'),
                on_activate_call=self._copy_press,
            )
        )

        self._ok_button = ba.buttonwidget(
            parent=self._root_widget,
            position=(
                (self._width - 182)
                if (data.show_cancel or show_copy)
                else (self._width * 0.5 - 80),
                30,
            ),
            size=(160, 60),
            autoselect=True,
            label=ba.Lstr(resource='okText'),
            on_activate_call=self._ok_press,
        )

        ba.containerwidget(
            edit=self._root_widget,
            cancel_button=self._cancel_button,
            start_button=self._ok_button,
            selected_child=self._ok_button,
        )

    def _copy_press(self) -> None:
        assert self._data.copy_text is not None
        ba.clipboard_set_text(self._data.copy_text)
        ba.screenmessage(ba.Lstr(resource='copyConfirmText'), color=(0, 1, 0))

    def _ok_press(self) -> None:
        if ba.time(ba.TimeType.REAL) - self._starttime < 1.0:
            ba.playsound(ba.getsound('error'))
            return
        ba.internal.add_transaction(
            {
                'type': 'DIALOG_RESPONSE',
                'dialogID': self._data.dialog_id,
                'response': 1,
            }
        )
        ba.containerwidget(edit=self._root_widget, transition='out_scale')

    def _cancel_press(self) -> None:
        if ba.time(ba.TimeType.REAL) - self._starttime < 1.0:
            ba.playsound(ba.getsound('error'))
            return
        ba.internal.add_transaction(
            {
                'type': 'DIALOG_RESPONSE',
                'dialogID': self._data.dialog_id,
                'response': 0,
            }
        )
        ba.containerwidget(edit=self._root_widget, transition='out_scale')
