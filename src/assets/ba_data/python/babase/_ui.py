# Released under the MIT License. See LICENSE for details.
#
"""UI related bits of babase."""

from typing import TYPE_CHECKING, override

from babase._stringedit import StringEditAdapter, StringEditKind
import _babase

if TYPE_CHECKING:
    pass


class DevConsoleStringEditAdapter(StringEditAdapter):
    """Allows editing dev-console text."""

    def __init__(self) -> None:
        description = 'Dev Console Input'
        initial_text = _babase.get_dev_console_input_text()
        max_length = None
        screen_space_center = None
        super().__init__(
            description,
            initial_text,
            max_length,
            screen_space_center,
            kind=StringEditKind.CODE,
        )

    @override
    def _do_apply(self, new_text: str) -> None:
        _babase.set_dev_console_input_text(new_text)
        _babase.dev_console_input_adapter_finish()

    @override
    def _do_submit(self) -> None:
        # Runs after _do_apply, so the line we run is the one just
        # typed. Tapping away from the editor applies without
        # submitting, which fills the input in without running it.
        _babase.dev_console_exec()

    @override
    def _do_cancel(self) -> None:
        _babase.dev_console_input_adapter_finish()
