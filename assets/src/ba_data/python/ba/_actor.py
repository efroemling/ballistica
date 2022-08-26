# Released under the MIT License. See LICENSE for details.
#
"""Defines base Actor class."""

from __future__ import annotations

import weakref
from typing import TYPE_CHECKING, TypeVar, overload

import _ba
from ba._messages import DieMessage, DeathType, OutOfBoundsMessage, UNHANDLED
from ba._error import print_exception, ActivityNotFoundError

if TYPE_CHECKING:
    from typing import Any, Literal
    import ba

ActorT = TypeVar('ActorT', bound='Actor')


class Actor:
    """High level logical entities in a ba.Activity.

    Category: **Gameplay Classes**

    Actors act as controllers, combining some number of ba.Nodes,
    ba.Textures, ba.Sounds, etc. into a high-level cohesive unit.

    Some example actors include the Bomb, Flag, and Spaz classes that
    live in the bastd.actor.* modules.

    One key feature of Actors is that they generally 'die'
    (killing off or transitioning out their nodes) when the last Python
    reference to them disappears, so you can use logic such as:

    ##### Example
    >>> # Create a flag Actor in our game activity:
    ... from bastd.actor.flag import Flag
    ... self.flag = Flag(position=(0, 10, 0))
    ...
    ... # Later, destroy the flag.
    ... # (provided nothing else is holding a reference to it)
    ... # We could also just assign a new flag to this value.
    ... # Either way, the old flag disappears.
    ... self.flag = None

    This is in contrast to the behavior of the more low level ba.Nodes,
    which are always explicitly created and destroyed and don't care
    how many Python references to them exist.

    Note, however, that you can use the ba.Actor.autoretain() method
    if you want an Actor to stick around until explicitly killed
    regardless of references.

    Another key feature of ba.Actor is its ba.Actor.handlemessage() method,
    which takes a single arbitrary object as an argument. This provides a safe
    way to communicate between ba.Actor, ba.Activity, ba.Session, and any other
    class providing a handlemessage() method. The most universally handled
    message type for Actors is the ba.DieMessage.

    Another way to kill the flag from the example above:
    We can safely call this on any type with a 'handlemessage' method
    (though its not guaranteed to always have a meaningful effect).
    In this case the Actor instance will still be around, but its
    ba.Actor.exists() and ba.Actor.is_alive() methods will both return False.
    >>> self.flag.handlemessage(ba.DieMessage())
    """

    def __init__(self) -> None:
        """Instantiates an Actor in the current ba.Activity."""

        if __debug__:
            self._root_actor_init_called = True
        activity = _ba.getactivity()
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
            print_exception('exception in ba.Actor.__del__() for', self)

    def handlemessage(self, msg: Any) -> Any:
        """General message handling; can be passed any message object."""
        assert not self.expired

        # By default, actors going out-of-bounds simply kill themselves.
        if isinstance(msg, OutOfBoundsMessage):
            return self.handlemessage(DieMessage(how=DeathType.OUT_OF_BOUNDS))

        return UNHANDLED

    def autoretain(self: ActorT) -> ActorT:
        """Keep this Actor alive without needing to hold a reference to it.

        This keeps the ba.Actor in existence by storing a reference to it
        with the ba.Activity it was created in. The reference is lazily
        released once ba.Actor.exists() returns False for it or when the
        Activity is set as expired.  This can be a convenient alternative
        to storing references explicitly just to keep a ba.Actor from dying.
        For convenience, this method returns the ba.Actor it is called with,
        enabling chained statements such as:  myflag = ba.Flag().autoretain()
        """
        activity = self._activity()
        if activity is None:
            raise ActivityNotFoundError()
        activity.retain_actor(self)
        return self

    def on_expire(self) -> None:
        """Called for remaining `ba.Actor`s when their ba.Activity shuts down.

        Actors can use this opportunity to clear callbacks or other
        references which have the potential of keeping the ba.Activity
        alive inadvertently (Activities can not exit cleanly while
        any Python references to them remain.)

        Once an actor is expired (see ba.Actor.is_expired()) it should no
        longer perform any game-affecting operations (creating, modifying,
        or deleting nodes, media, timers, etc.) Attempts to do so will
        likely result in errors.
        """

    @property
    def expired(self) -> bool:
        """Whether the Actor is expired.

        (see ba.Actor.on_expire())
        """
        activity = self.getactivity(doraise=False)
        return True if activity is None else activity.expired

    def exists(self) -> bool:
        """Returns whether the Actor is still present in a meaningful way.

        Note that a dying character should still return True here as long as
        their corpse is visible; this is about presence, not being 'alive'
        (see ba.Actor.is_alive() for that).

        If this returns False, it is assumed the Actor can be completely
        deleted without affecting the game; this call is often used
        when pruning lists of Actors, such as with ba.Actor.autoretain()

        The default implementation of this method always return True.

        Note that the boolean operator for the Actor class calls this method,
        so a simple "if myactor" test will conveniently do the right thing
        even if myactor is set to None.
        """
        return True

    def __bool__(self) -> bool:
        # Cleaner way to test existence; friendlier to None values.
        return self.exists()

    def is_alive(self) -> bool:
        """Returns whether the Actor is 'alive'.

        What this means is up to the Actor.
        It is not a requirement for Actors to be able to die;
        just that they report whether they consider themselves
        to be alive or not. In cases where dead/alive is
        irrelevant, True should be returned.
        """
        return True

    @property
    def activity(self) -> ba.Activity:
        """The Activity this Actor was created in.

        Raises a ba.ActivityNotFoundError if the Activity no longer exists.
        """
        activity = self._activity()
        if activity is None:
            raise ActivityNotFoundError()
        return activity

    # Overloads to convey our exact return type depending on 'doraise' value.

    @overload
    def getactivity(self, doraise: Literal[True] = True) -> ba.Activity:
        ...

    @overload
    def getactivity(self, doraise: Literal[False]) -> ba.Activity | None:
        ...

    def getactivity(self, doraise: bool = True) -> ba.Activity | None:
        """Return the ba.Activity this Actor is associated with.

        If the Activity no longer exists, raises a ba.ActivityNotFoundError
        or returns None depending on whether 'doraise' is True.
        """
        activity = self._activity()
        if activity is None and doraise:
            raise ActivityNotFoundError()
        return activity
