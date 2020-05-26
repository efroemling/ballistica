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
"""Collision related functionality."""

from __future__ import annotations

from typing import TYPE_CHECKING

import _ba
from ba._error import NodeNotFoundError

if TYPE_CHECKING:
    import ba


class Collision:
    """A class providing info about occurring collisions."""

    @property
    def position(self) -> ba.Vec3:
        """The position of the current collision."""
        return _ba.Vec3(_ba.get_collision_info('position'))

    @property
    def sourcenode(self) -> ba.Node:
        """The node containing the material triggering the current callback.

        Throws a ba.NodeNotFoundError if the node does not exist, though
        the node should always exist (at least at the start of the collision
        callback).
        """
        node = _ba.get_collision_info('sourcenode')
        assert isinstance(node, (_ba.Node, type(None)))
        if not node:
            raise NodeNotFoundError()
        return node

    @property
    def opposingnode(self) -> ba.Node:
        """The node the current callback material node is hitting.

        Throws a ba.NodeNotFoundError if the node does not exist.
        This can be expected in some cases such as in 'disconnect'
        callbacks triggered by deleting a currently-colliding node.
        """
        node = _ba.get_collision_info('opposingnode')
        assert isinstance(node, (_ba.Node, type(None)))
        if not node:
            raise NodeNotFoundError()
        return node

    @property
    def opposingbody(self) -> int:
        """The body index on the opposing node in the current collision."""
        body = _ba.get_collision_info('opposingbody')
        assert isinstance(body, int)
        return body


# Simply recycle one instance...
_collision = Collision()


def getcollision() -> Collision:
    """Return the in-progress collision."""
    return _collision
