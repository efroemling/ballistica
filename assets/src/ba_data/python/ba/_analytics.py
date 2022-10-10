# Released under the MIT License. See LICENSE for details.
#
"""Functionality related to analytics."""

from __future__ import annotations

from typing import TYPE_CHECKING

import _ba

if TYPE_CHECKING:
    pass


def game_begin_analytics() -> None:
    """Update analytics events for the start of a game."""
    # pylint: disable=too-many-branches
    # pylint: disable=cyclic-import
    from ba._dualteamsession import DualTeamSession
    from ba._freeforallsession import FreeForAllSession
    from ba._coopsession import CoopSession
    from ba._gameactivity import GameActivity

    activity = _ba.getactivity(False)
    session = _ba.getsession(False)

    # Fail gracefully if we didn't cleanly get a session and game activity.
    if not activity or not session or not isinstance(activity, GameActivity):
        return

    if isinstance(session, CoopSession):
        campaign = session.campaign
        assert campaign is not None
        _ba.set_analytics_screen(
            'Coop Game: '
            + campaign.name
            + ' '
            + campaign.getlevel(_ba.app.coop_session_args['level']).name
        )
        _ba.increment_analytics_count('Co-op round start')
        if len(activity.players) == 1:
            _ba.increment_analytics_count('Co-op round start 1 human player')
        elif len(activity.players) == 2:
            _ba.increment_analytics_count('Co-op round start 2 human players')
        elif len(activity.players) == 3:
            _ba.increment_analytics_count('Co-op round start 3 human players')
        elif len(activity.players) >= 4:
            _ba.increment_analytics_count('Co-op round start 4+ human players')

    elif isinstance(session, DualTeamSession):
        _ba.set_analytics_screen('Teams Game: ' + activity.getname())
        _ba.increment_analytics_count('Teams round start')
        if len(activity.players) == 1:
            _ba.increment_analytics_count('Teams round start 1 human player')
        elif 1 < len(activity.players) < 8:
            _ba.increment_analytics_count(
                'Teams round start '
                + str(len(activity.players))
                + ' human players'
            )
        elif len(activity.players) >= 8:
            _ba.increment_analytics_count('Teams round start 8+ human players')

    elif isinstance(session, FreeForAllSession):
        _ba.set_analytics_screen('FreeForAll Game: ' + activity.getname())
        _ba.increment_analytics_count('Free-for-all round start')
        if len(activity.players) == 1:
            _ba.increment_analytics_count(
                'Free-for-all round start 1 human player'
            )
        elif 1 < len(activity.players) < 8:
            _ba.increment_analytics_count(
                'Free-for-all round start '
                + str(len(activity.players))
                + ' human players'
            )
        elif len(activity.players) >= 8:
            _ba.increment_analytics_count(
                'Free-for-all round start 8+ human players'
            )

    # For some analytics tracking on the c layer.
    _ba.reset_game_activity_tracking()
