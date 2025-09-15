# Released under the MIT License. See LICENSE for details.
#
"""Misc UI related types."""

from __future__ import annotations

import warnings
from typing import TYPE_CHECKING, override

import babase

import _bauiv1

if TYPE_CHECKING:
    from typing import Any, Type, Literal, Callable

    import bauiv1


# REMOVE WHEN API 9 SUPPORT ENDS
def uicleanupcheck(obj: Any, widget: bauiv1.Widget) -> None:
    """
    .. deprecated:: 1.7.51
       Use :meth:`UIV1AppSubsystem.add_ui_cleanup_check()`.
       Will be removed when api 9 support ends.
    """
    warnings.warn(
        'bauiv1.uicleanupcheck() will be removed when api 9 support ends;'
        ' use ba*.app.ui_v1.add_ui_cleanup_check() instead.',
        DeprecationWarning,
        stacklevel=2,
    )
    babase.app.ui_v1.add_ui_cleanup_check(obj, widget)


class TextWidgetStringEditAdapter(babase.StringEditAdapter):
    """A StringEditAdapter subclass for editing our text widgets."""

    def __init__(self, text_widget: bauiv1.Widget) -> None:
        self.widget = text_widget

        # Ugly hacks to pull values from widgets. Really need to clean
        # up that api.
        description: Any = _bauiv1.textwidget(query_description=text_widget)
        assert isinstance(description, str)
        initial_text: Any = _bauiv1.textwidget(query=text_widget)
        assert isinstance(initial_text, str)
        max_length: Any = _bauiv1.textwidget(query_max_chars=text_widget)
        assert isinstance(max_length, int)

        screen_space_center = text_widget.get_screen_space_center()

        super().__init__(
            description, initial_text, max_length, screen_space_center
        )

    @override
    def _do_apply(self, new_text: str) -> None:
        if self.widget:
            _bauiv1.textwidget(
                edit=self.widget, text=new_text, adapter_finished=True
            )

    @override
    def _do_cancel(self) -> None:
        if self.widget:
            _bauiv1.textwidget(edit=self.widget, adapter_finished=True)


class RootUIUpdatePause:
    """Pauses updates to the root-ui while in existence."""

    def __init__(self) -> None:
        _bauiv1.root_ui_pause_updates()

    def __del__(self) -> None:
        _bauiv1.root_ui_resume_updates()
