# Released under the MIT License. See LICENSE for details.
#
"""Functionality related to analytics."""

from __future__ import annotations

from typing import TYPE_CHECKING

import babase
import bascenev1

if TYPE_CHECKING:
    pass


def game_begin_analytics() -> None:
    """Update analytics events for the start of a game."""
    # pylint: disable=too-many-branches
    # pylint: disable=cyclic-import
    from bascenev1 import (
        DualTeamSession,
        FreeForAllSession,
        CoopSession,
        GameActivity,
    )

    assert babase.app.classic is not None

    activity = bascenev1.getactivity(False)
    session = bascenev1.getsession(False)

    # Fail gracefully if we didn't cleanly get a session and game activity.
    if not activity or not session or not isinstance(activity, GameActivity):
        return

    if isinstance(session, CoopSession):
        campaign = session.campaign
        assert campaign is not None
        babase.set_analytics_screen(
            'Coop Game: '
            + campaign.name
            + ' '
            + campaign.getlevel(
                babase.app.classic.coop_session_args['level']
            ).name
        )
        babase.increment_analytics_count('Co-op round start')
        if len(activity.players) == 1:
            babase.increment_analytics_count('Co-op round start 1 human player')
        elif len(activity.players) == 2:
            babase.increment_analytics_count(
                'Co-op round start 2 human players'
            )
        elif len(activity.players) == 3:
            babase.increment_analytics_count(
                'Co-op round start 3 human players'
            )
        elif len(activity.players) >= 4:
            babase.increment_analytics_count(
                'Co-op round start 4+ human players'
            )

    elif isinstance(session, DualTeamSession):
        babase.set_analytics_screen('Teams Game: ' + activity.getname())
        babase.increment_analytics_count('Teams round start')
        if len(activity.players) == 1:
            babase.increment_analytics_count('Teams round start 1 human player')
        elif 1 < len(activity.players) < 8:
            babase.increment_analytics_count(
                'Teams round start '
                + str(len(activity.players))
                + ' human players'
            )
        elif len(activity.players) >= 8:
            babase.increment_analytics_count(
                'Teams round start 8+ human players'
            )

    elif isinstance(session, FreeForAllSession):
        babase.set_analytics_screen('FreeForAll Game: ' + activity.getname())
        babase.increment_analytics_count('Free-for-all round start')
        if len(activity.players) == 1:
            babase.increment_analytics_count(
                'Free-for-all round start 1 human player'
            )
        elif 1 < len(activity.players) < 8:
            babase.increment_analytics_count(
                'Free-for-all round start '
                + str(len(activity.players))
                + ' human players'
            )
        elif len(activity.players) >= 8:
            babase.increment_analytics_count(
                'Free-for-all round start 8+ human players'
            )
