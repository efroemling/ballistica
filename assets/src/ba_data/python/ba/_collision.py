# Released under the MIT License. See LICENSE for details.
#
"""Collision related functionality."""

from __future__ import annotations

from typing import TYPE_CHECKING

import _ba
from ba._error import NodeNotFoundError

if TYPE_CHECKING:
    import ba


class Collision:
    """A class providing info about occurring collisions.

    Category: **Gameplay Classes**
    """

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
    """Return the in-progress collision.

    Category: **Gameplay Functions**
    """
    return _collision
