# Released under the MIT License. See LICENSE for details.
#
"""Defines base Actor class."""

from __future__ import annotations

import weakref
import logging
from typing import TYPE_CHECKING, overload

import babase

import _bascenev1
from bascenev1._messages import (
    DieMessage,
    DeathType,
    OutOfBoundsMessage,
    UNHANDLED,
)

if TYPE_CHECKING:
    from typing import Any, Literal, Self

    import bascenev1


class Actor:
    """High level logical entities in an :class:`~bascenev1.Activity`.

    Actors act as controllers, combining some number of
    :class:`~bascenev1.Node`, :class:`~bascenev1.Texture`,
    :class:`~bascenev1.Sound`, and other type objects into a high-level
    cohesive unit.

    Some example actors include the :class:`~bascenev1lib.actor.bomb.Bomb`,
    :class:`~bascenev1lib.actor.flag.Flag`, and
    :class:`~bascenev1lib.actor.spaz.Spaz`, classes that live in the
    :mod:`bascenev1lib.actor` package.

    One key feature of actors is that they generally 'die' (killing off
    or transitioning out their nodes) when the last Python reference to
    them disappears, so you can use logic such as::

        # Create a flag actor in our game activity (self):
        from bascenev1lib.actor.flag import Flag

        self.flag = Flag(position=(0, 10, 0))

        # Later, destroy the flag (provided nothing else is holding a
        # reference to it). We could also just assign a new flag to this
        # value. Either way, the old flag should disappear.
        self.flag = None

    This is in contrast to the behavior of the more low level
    :class:`~bascenev1.Node` class, which is always explicitly created
    and destroyed and doesn't care how many Python references to it
    exist.

    Note, however, that you can use the :meth:`~bascenev1.Actor.autoretain()`
    method if you want an actor to stick around until explicitly killed
    regardless of references.

    Another key feature of actors is their
    :meth:`~bascenev1.Actor.handlemessage()` method, which takes a single
    arbitrary object as an argument. This provides a safe way to communicate
    between :class:`~bascenev1.Actor`, :class:`~bascenev1.Activity`,
    :class:`~bascenev1.Session`, and any other class providing a
    ``handlemessage()`` method. The most universally handled
    message type for actors is the :class:`~bascenev1.DieMessage`.

    Another way to kill the flag from the example above:
    We can safely call this on any type with a ``handlemessage`` method
    (though its not guaranteed to always have a meaningful effect).
    In this case the actor instance will still be around, but its
    :meth:`~bascenev1.Actor.exists()` and :meth:`~bascenev1.Actor.is_alive()`
    methods will both return False::

        self.flag.handlemessage(bascenev1.DieMessage())
    """

    def __init__(self) -> None:
        """Instantiates an Actor in the current bascenev1.Activity."""

        if __debug__:
            self._root_actor_init_called = True
        activity = _bascenev1.getactivity()
        self._activity = weakref.ref(activity)
        activity.add_actor_weak_ref(self)

    def __del__(self) -> None:
        try:
            # Unexpired Actors send themselves a DieMessage when going down.
            # That way we can treat DieMessage handling as the single
            # point-of-action for death.
            if not self.expired:
                self.handlemessage(DieMessage())
        except Exception:
            logging.exception(
                'Error in bascenev1.Actor.__del__() for %s.', self
            )

    def handlemessage(self, msg: Any) -> Any:
        """General message handling; can be passed any message object."""
        assert not self.expired

        # By default, actors going out-of-bounds simply kill themselves.
        if isinstance(msg, OutOfBoundsMessage):
            return self.handlemessage(DieMessage(how=DeathType.OUT_OF_BOUNDS))

        return UNHANDLED

    def autoretain(self) -> Self:
        """Keep this actor alive without needing to hold a reference to it.

        This keeps the actor in existence by storing a reference to it
        with the :class:`~bascenev1.Activity` it was created in. The
        reference is lazily released once
        :meth:`~bascenev1.Actor.exists()` returns False for the actor or
        when the :class:`~bascenev1.Activity` is set as expired. This
        can be a convenient alternative to storing references explicitly
        just to keep an actor from dying. For convenience, this method
        returns the actor it is called with, enabling chained statements
        such as: ``myflag = bascenev1.Flag().autoretain()``
        """
        activity = self._activity()
        if activity is None:
            raise babase.ActivityNotFoundError()
        activity.retain_actor(self)
        return self

    def on_expire(self) -> None:
        """Called for remaining actors when their activity dies.

        Actors can use this opportunity to clear callbacks or other
        references which have the potential of keeping the
        :class:`~bascenev1.Activity` alive inadvertently (activities can
        not exit cleanly while any Python references to them remain.)

        Once an actor is expired (see :attr:`~bascenev1.Actor.expired`)
        it should no longer perform any game-affecting operations
        (creating, modifying, or deleting nodes, media, timers, etc.)
        Attempts to do so will likely result in errors.
        """

    @property
    def expired(self) -> bool:
        """Whether the actor is expired.

        (see :meth:`~bascenev1.Actor.on_expire()`)
        """
        activity = self.getactivity(doraise=False)
        return True if activity is None else activity.expired

    def exists(self) -> bool:
        """Returns whether the actor is still present in a meaningful way.

        Note that a dying character should still return True here as long as
        their corpse is visible; this is about presence, not being 'alive'
        (see :meth:`~bascenev1.Actor.is_alive()` for that).

        If this returns False, it is assumed the actor can be completely
        deleted without affecting the game; this call is often used when
        pruning lists of actors, such as with
        :meth:`bascenev1.Actor.autoretain()`

        The default implementation of this method always return True.

        Note that the boolean operator for the actor class calls this method,
        so a simple ``if myactor`` test will conveniently do the right thing
        even if myactor is set to None.
        """
        return True

    def __bool__(self) -> bool:
        # Cleaner way to test existence; friendlier to None values.
        return self.exists()

    def is_alive(self) -> bool:
        """Returns whether the actor is 'alive'.

        What this means is up to the actor. It is not a requirement for
        actors to be able to die; just that they report whether they
        consider themselves to be alive or not. In cases where
        dead/alive is irrelevant, True should be returned.
        """
        return True

    @property
    def activity(self) -> bascenev1.Activity:
        """The activity this actor was created in.

        Raises a :class:`~bascenev1.ActivityNotFoundError` if the
        activity no longer exists.
        """
        activity = self._activity()
        if activity is None:
            raise babase.ActivityNotFoundError()
        return activity

    # Overloads to convey our exact return type depending on 'doraise' value.

    @overload
    def getactivity(
        self, doraise: Literal[True] = True
    ) -> bascenev1.Activity: ...

    @overload
    def getactivity(
        self, doraise: Literal[False]
    ) -> bascenev1.Activity | None: ...

    def getactivity(self, doraise: bool = True) -> bascenev1.Activity | None:
        """Return the activity this actor is associated with.

        If the activity no longer exists, raises a
        :class:`~bascenev1.ActivityNotFoundError` or returns None
        depending on whether ``doraise`` is True.
        """
        activity = self._activity()
        if activity is None and doraise:
            raise babase.ActivityNotFoundError()
        return activity
