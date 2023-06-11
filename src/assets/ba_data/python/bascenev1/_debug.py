# Released under the MIT License. See LICENSE for details.
#
"""Debugging functionality."""
from __future__ import annotations

from typing import TYPE_CHECKING

import babase

if TYPE_CHECKING:
    from typing import Any

    import bascenev1


def print_live_object_warnings(
    when: Any,
    ignore_session: bascenev1.Session | None = None,
    ignore_activity: bascenev1.Activity | None = None,
) -> None:
    """Print warnings for remaining objects in the current context.

    IMPORTANT - don't call this in production; usage of gc.get_objects()
    can bork Python. See notes at top of efro.debug module.
    """
    # pylint: disable=cyclic-import
    import gc

    from bascenev1._session import Session
    from bascenev1._actor import Actor
    from bascenev1._activity import Activity

    assert babase.app.classic is not None

    sessions: list[bascenev1.Session] = []
    activities: list[bascenev1.Activity] = []
    actors: list[bascenev1.Actor] = []

    # Once we come across leaked stuff, printing again is probably
    # redundant.
    if babase.app.classic.printed_live_object_warning:
        return
    for obj in gc.get_objects():
        if isinstance(obj, Actor):
            actors.append(obj)
        elif isinstance(obj, Session):
            sessions.append(obj)
        elif isinstance(obj, Activity):
            activities.append(obj)

    # Complain about any remaining sessions.
    for session in sessions:
        if session is ignore_session:
            continue
        babase.app.classic.printed_live_object_warning = True
        print(f'ERROR: Session found {when}: {session}')

    # Complain about any remaining activities.
    for activity in activities:
        if activity is ignore_activity:
            continue
        babase.app.classic.printed_live_object_warning = True
        print(f'ERROR: Activity found {when}: {activity}')

    # Complain about any remaining actors.
    for actor in actors:
        babase.app.classic.printed_live_object_warning = True
        print(f'ERROR: Actor found {when}: {actor}')
