# Released under the MIT License. See LICENSE for details.
#
"""Live page-state bookkeeping for doc-ui windows."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Any, Callable


class DocUIPageState:
    """Live values for the page a doc-ui window is showing.

    Holds the wire-form state dict (see
    :attr:`bacommon.docui.v2.Page.state`) along with the hooks input
    rows register to keep what they show and what it says in step.
    (State values are arbitrary json, hence the Anys here.)

    :meta private:
    """

    def __init__(self) -> None:
        self.values: dict | None = None

        # Calls pushing values out to the input rows showing them.
        self._pushers: dict[str, Callable[[Any], None]] = {}

        # Calls fetching values from input rows that don't report
        # every change as it happens (text being typed, say).
        self._pullers: dict[str, Callable[[], Any]] = {}

    def adopt(self, values: dict | None) -> None:
        """Take on the state of a newly arrived page.

        Hooks registered by the previous page's rows are dropped.
        """
        self.values = values
        self._pushers = {}
        self._pullers = {}

    def register_pusher(self, key: str, pusher: Callable[[Any], None]) -> None:
        """Register a call updating whatever is showing a value."""
        self._pushers[key] = pusher

    def register_puller(self, key: str, puller: Callable[[], Any]) -> None:
        """Register a call fetching a value from whatever edits it.

        For input rows that do not report every change as it happens;
        we don't hear about each character typed into a text field.
        """
        self._pullers[key] = puller

    def set_values(self, values: dict, *, push: bool) -> None:
        """Assign values, optionally pushing them to rows showing them."""
        assert self.values is not None
        for key, value in values.items():
            self.values[key] = value
            if push:
                pusher = self._pushers.get(key)
                if pusher is not None:
                    pusher(value)

    def pull_changed(self) -> dict:
        """Return pulled values differing from what we currently hold."""
        if self.values is None:
            return {}
        pulled = {key: pull() for key, pull in self._pullers.items()}
        return {
            key: val
            for key, val in pulled.items()
            if self.values.get(key) != val
        }
