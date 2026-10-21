# Released under the MIT License. See LICENSE for details.
#
"""The doc-ui pages classic hosts serve their clients by default.

The pages themselves live with what they're for: the stats page in
``baclassic._hostuistats`` (:class:`baclassic.HostUIStatsPage`) and
the kick vote's in ``baclassic._hostuikick``
(:class:`baclassic.HostUIKickVotes`); this routes the default classic
host routes to them.
"""

from typing import TYPE_CHECKING, assert_never

import bacommon.docui.routes.classichost as hroutes

import babase

if TYPE_CHECKING:
    import bacommon.docui.v2


def fulfill_classic_host_route(
    route: hroutes.AnyClassicHostRoute, client_id: int
) -> bacommon.docui.v2.Response:
    """Build the page for one of the default classic host routes."""
    classic = babase.app.classic
    assert classic is not None
    host_ui = classic.host_ui
    match route:
        case hroutes.Stats():
            return host_ui.stats_page.build(route)
        case hroutes.KickVote():
            return host_ui.kick_votes.build_page(client_id, route.client_id)
        case hroutes.KickVoteStart():
            return host_ui.kick_votes.handle_start(client_id, route.client_id)
        case hroutes.KickVoteCast():
            return host_ui.kick_votes.handle_cast(client_id, route.yes)
        case _:
            assert_never(route)
