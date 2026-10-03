# Released under the MIT License. See LICENSE for details.
#
"""Shared public types for doc-ui."""

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import bauiv1 as bui

    from bacommon.docui.routes import DocUIState

    from bauiv1lib.docui._window import DocUIWindow


@dataclass
class DocUILocalAction:
    """Context for a local-action."""

    name: str
    args: dict
    widget: bui.Widget | None
    window: DocUIWindow

    #: State key of the input row whose change fired us, if that is
    #: what did.
    trigger: str | None = None

    def state[T: DocUIState](self, statetype: type[T]) -> T | None:
        """The window's current page state, as a given state type.

        None if the page has no state or its state is of some other
        type. Input rows write their values here as they change, so
        this is the live value for an action fired mid-interaction
        (a slider's ``on_drag``, say).
        """
        return statetype.decode(self.window.page_state)
