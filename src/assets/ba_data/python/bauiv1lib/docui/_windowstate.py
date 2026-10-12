# Released under the MIT License. See LICENSE for details.
#
"""Recreating doc-ui windows (back navigation and the like)."""

from dataclasses import replace
from typing import TYPE_CHECKING, override

import bauiv1 as bui

if TYPE_CHECKING:
    from typing import Callable, Literal

    from bacommon.docui import DocUIRequest


class DocUIMainWindowState(bui.MainWindowState):
    """Recreates a doc-ui window (for back navigation and the like).

    Holds the request the window will re-fetch its page with, so values
    can be handed back into its page state before it returns (see
    :attr:`bacommon.docui.v2.Local.return_sets`).

    :meta private:
    """

    def __init__(
        self,
        create_call: Callable[
            [
                Literal['in_right', 'in_left', 'in_scale'] | None,
                bui.Widget | None,
                DocUIRequest,
            ],
            bui.MainWindow,
        ],
        request: DocUIRequest,
        uiopenstate: bui.UIOpenState | None,
    ) -> None:
        super().__init__()
        self.create_call = create_call
        self.request = request

        # We simply need to hold on to this to keep the ui-open-state
        # alive.
        self.uiopenstate = uiopenstate

    def apply_return_sets(self, values: dict) -> None:
        """Assign handed-back values into our page's state.

        Ignored (with a warning) unless our page has state of the type
        the values are for.
        """
        import bacommon.docui.v2 as dui2

        request = self.request
        statetype = values.get('_t')
        if (
            not isinstance(request, dui2.Request)
            or request.state is None
            or request.state.get('_t') != statetype
        ):
            bui.uilog.warning(
                'Ignoring doc-ui return values for state %r;'
                ' the page returned to has no such state.',
                statetype,
            )
            return
        self.request = replace(request, state={**request.state, **values})

    @override
    def get_ui_open_states(self) -> list[bui.UIOpenState]:
        return [] if self.uiopenstate is None else [self.uiopenstate]

    @override
    def create_window(
        self,
        transition: Literal['in_right', 'in_left', 'in_scale'] | None = None,
        origin_widget: bui.Widget | None = None,
    ) -> bui.MainWindow:
        return self.create_call(transition, origin_widget, self.request)
