# Released under the MIT License. See LICENSE for details.
#
"""Defines NodeActor class."""

from __future__ import annotations

from typing import TYPE_CHECKING, override

from bascenev1._messages import DieMessage
from bascenev1._actor import Actor

if TYPE_CHECKING:
    from typing import Any

    import bascenev1


class NodeActor(Actor):
    """A simple bascenev1.Actor type that wraps a single bascenev1.Node.

    Category: **Gameplay Classes**

    This Actor will delete its Node when told to die, and it's
    exists() call will return whether the Node still exists or not.
    """

    def __init__(self, node: bascenev1.Node):
        super().__init__()
        self.node = node

    @override
    def handlemessage(self, msg: Any) -> Any:
        if isinstance(msg, DieMessage):
            if self.node:
                self.node.delete()
                return None
        return super().handlemessage(msg)

    @override
    def exists(self) -> bool:
        return bool(self.node)
