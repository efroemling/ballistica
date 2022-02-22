# Released under the MIT License. See LICENSE for details.
#
"""Defines NodeActor class."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ba._messages import DieMessage
from ba._actor import Actor

if TYPE_CHECKING:
    import ba
    from typing import Any


class NodeActor(Actor):
    """A simple ba.Actor type that wraps a single ba.Node.

    Category: **Gameplay Classes**

    This Actor will delete its Node when told to die, and it's
    exists() call will return whether the Node still exists or not.
    """

    def __init__(self, node: ba.Node):
        super().__init__()
        self.node = node

    def handlemessage(self, msg: Any) -> Any:
        if isinstance(msg, DieMessage):
            if self.node:
                self.node.delete()
                return None
        return super().handlemessage(msg)

    def exists(self) -> bool:
        return bool(self.node)
