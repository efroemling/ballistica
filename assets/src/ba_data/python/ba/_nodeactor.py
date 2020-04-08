# Copyright (c) 2011-2020 Eric Froemling
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
# -----------------------------------------------------------------------------
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

    Category: Gameplay Classes

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
