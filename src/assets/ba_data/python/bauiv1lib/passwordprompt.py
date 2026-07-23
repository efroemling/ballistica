# Released under the MIT License. See LICENSE for details.
#
"""A minimal password-entry prompt dialog."""

from typing import TYPE_CHECKING, cast

import bauiv1 as bui
from bauiv1 import classicassets

if TYPE_CHECKING:
    from typing import Callable


class PasswordPromptWindow:
    """Small modal overlay window prompting for a password.

    Calls ``on_result`` exactly once: the entered password on submit or
    None on cancel (via the cancel button, back press, or an external
    :meth:`dismiss`).
    """

    def __init__(
        self,
        *,
        description: str | bui.Lstr | bui.LangStr | None = None,
        on_result: Callable[[str | None], None] | None = None,
    ):
        ui = bui.app.ui_v1

        # Make sure our widgets have globally unique ids.
        self._id_prefix = ui.new_id_prefix('passwordprompt')

        self._on_result = on_result
        self._result_sent = False

        if description is None:
            description = classicassets.strings.gather.party_requires_password

        width = 420.0
        height = 200.0
        uiscale = ui.uiscale
        self._root_widget = bui.containerwidget(
            size=(width, height),
            transition='in_scale',
            toolbar_visibility='menu_minimal_no_back',
            parent=bui.get_special_widget('overlay_stack'),
            scale=(
                1.9
                if uiscale is bui.UIScale.SMALL
                else 1.5 if uiscale is bui.UIScale.MEDIUM else 1.0
            ),
            darken_behind=True,
        )
        bui.textwidget(
            parent=self._root_widget,
            position=(width * 0.5, height - 40),
            size=(0, 0),
            h_align='center',
            v_align='center',
            text=description,
            maxwidth=width * 0.9,
        )
        self._text_field = bui.textwidget(
            parent=self._root_widget,
            id=f'{self._id_prefix}|password',
            editable=True,
            size=(width - 80, 40),
            position=(40, height - 110),
            text='',
            maxwidth=width - 100,
            max_chars=100,
            autoselect=True,
            v_align='center',
            password=True,
            description=(
                description
                if isinstance(description, (str, bui.Lstr))
                else description.evaluate()
            ),
            on_return_press_call=self._submit,
        )
        cbtn = bui.buttonwidget(
            parent=self._root_widget,
            id=f'{self._id_prefix}|cancel',
            autoselect=True,
            position=(20, 20),
            size=(150, 50),
            label=classicassets.strings.ui.cancel,
            on_activate_call=self._cancel,
        )
        okbtn = bui.buttonwidget(
            parent=self._root_widget,
            id=f'{self._id_prefix}|ok',
            autoselect=True,
            position=(width - 175, 20),
            size=(150, 50),
            label=classicassets.strings.ui.ok,
            on_activate_call=self._submit,
        )
        bui.containerwidget(
            edit=self._root_widget,
            cancel_button=cbtn,
            start_button=okbtn,
            selected_child=self._text_field,
        )

    def dismiss(self) -> None:
        """Externally dismiss the prompt (counts as a cancel). Idempotent."""
        self._cancel()

    def _send_result(self, result: str | None) -> None:
        if self._result_sent:
            return
        self._result_sent = True
        if self._on_result is not None:
            self._on_result(result)

    def _submit(self) -> None:
        if not self._root_widget:
            return
        password = cast(str, bui.textwidget(query=self._text_field))
        bui.containerwidget(edit=self._root_widget, transition='out_scale')
        self._send_result(password)

    def _cancel(self) -> None:
        if self._root_widget:
            bui.containerwidget(edit=self._root_widget, transition='out_scale')
        self._send_result(None)
