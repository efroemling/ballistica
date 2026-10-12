# Released under the MIT License. See LICENSE for details.
#
"""Shared actor-hosting functionality."""

import weakref
import logging
from typing import TYPE_CHECKING

import babase

if TYPE_CHECKING:
    import bascenev1


class ActorHost:
    """Base for things that :class:`bascenev1.Actor` instances live in.

    An actor is bound at creation to whichever host is current in its
    context: a :class:`bascenev1.Activity` during normal gameplay, or a
    :class:`bascenev1.LocalDisplay`. The host holds the strong refs
    behind :meth:`bascenev1.Actor.autoretain()`, a weak ref to every
    actor created under it, and the ``expired`` flag those actors
    report; expiring the host expires all of its actors with it.
    """

    def __init__(self) -> None:
        super().__init__()
        self._expired = False

        # A handy place to put most actors; this list is pruned of dead
        # actors regularly and these actors are insta-killed as the host
        # is dying.
        self._actor_refs: list[bascenev1.Actor] = []
        self._actor_weak_refs: list[weakref.ref[bascenev1.Actor]] = []

    @property
    def expired(self) -> bool:
        """Whether this host is expired.

        A host is set as expired when shutting down. At this point no
        new nodes, timers, etc should be made, run, etc, and the host
        should be considered a 'zombie'.
        """
        return self._expired

    def _get_activity(self) -> bascenev1.Activity | None:
        """Return this host as an activity, if it is one.

        Lets :class:`bascenev1.Actor` resolve its activity without the
        actor module depending on the activity one.
        """
        return None

    def retain_actor(self, actor: bascenev1.Actor) -> None:
        """Add a strong-ref to a :class:`bascenev1.Actor` to this host.

        The reference will be lazily released once
        :meth:`bascenev1.Actor.exists()` returns False for the actor.
        The :meth:`bascenev1.Actor.autoretain()` method is a convenient
        way to access this same functionality.
        """
        if __debug__:
            from bascenev1._actor import Actor

            assert isinstance(actor, Actor)
        self._actor_refs.append(actor)

    def add_actor_weak_ref(self, actor: bascenev1.Actor) -> None:
        """Add a weak-ref to a :class:`bascenev1.Actor` to this host.

        (called by the :class:`bascenev1.Actor` base class)
        """
        if __debug__:
            from bascenev1._actor import Actor

            assert isinstance(actor, Actor)
        self._actor_weak_refs.append(weakref.ref(actor))

    def _expire_actors(self) -> None:
        # Expire all Actors.
        for actor_ref in self._actor_weak_refs:
            actor = actor_ref()
            if actor is not None:
                babase.verify_object_death(actor)
                try:
                    actor.on_expire()
                except Exception:
                    logging.exception(
                        'Error in Actor.on_expire() for %s.', actor_ref()
                    )

    def _prune_dead_actors(self) -> None:
        # Prune our strong refs when the Actor's exists() call gives False
        self._actor_refs = [a for a in self._actor_refs if a.exists()]

        # Prune our weak refs once the Actor object has been freed.
        self._actor_weak_refs = [
            a for a in self._actor_weak_refs if a() is not None
        ]
