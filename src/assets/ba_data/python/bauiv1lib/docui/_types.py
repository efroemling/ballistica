# Released under the MIT License. See LICENSE for details.
#
"""Shared public types for doc-ui."""

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import bauiv1 as bui

    from bacommon.docui.routes import DocUIState

    from bauiv1lib.docui._window import DocUIWindow
    from bauiv1lib.docui._popupwindow import DocUIPopupWindow


@dataclass
class DocUILocalAction:
    """Context for a local-action."""

    name: str
    args: dict
    widget: bui.Widget | None

    #: The window the action belongs to. For one pressed in a popup,
    #: that is the window the popup is over (see ``popup``).
    window: DocUIWindow

    #: State key of the input row whose change fired us, if that is
    #: what did.
    trigger: str | None = None

    #: The popup the action was pressed in, if it was (the page it acts
    #: on is then the popup's, and :meth:`state` reads its state).
    #:
    #: :meta private:
    popup: DocUIPopupWindow | None = None

    def state[T: DocUIState](self, statetype: type[T]) -> T | None:
        """The page's current state, as a given state type.

        None if the page has no state or its state is of some other
        type. Input rows write their values here as they change, so
        this is the live value for an action fired mid-interaction
        (a slider's ``on_drag``, say).
        """
        host = self.window if self.popup is None else self.popup
        return statetype.decode(host.page_state)
