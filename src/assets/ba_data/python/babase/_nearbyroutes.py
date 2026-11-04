# Released under the MIT License. See LICENSE for details.
#
"""Nearby discovery internals: per-host route state and ranking.

This is an internal module; the api is in babase._nearby.

Each host keeps its routes ranked by smoothed round-trip time (plus a
per-type bias), switching its best route only when another is clearly
better or the best one stops answering.
"""

import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, assert_never

from babase._nearby import NearbyRouteType, NearbyRoute

if TYPE_CHECKING:
    from babase._nearby import NearbySource, NearbyGameInfo, NearbyRemoteInfo

logger = logging.getLogger('ba.net')

# A route that has missed this many probes in a row is 'stale' (out of
# the running for best route). (The discovery protocol drops routes
# after more misses than this.)
ROUTE_STALE_MISSES = 2

# How long an answer gets before its probe counts as missed.
_ANSWER_GRACE = 0.5

# Score for routes with no measured round-trip time (legacy hosts).
_UNMEASURED_RTT = 0.5

# A host only switches to a new best route when it scores at least
# this much better (fractionally and absolutely); keeps near-equal
# routes from flapping.
_SWITCH_FRACTION = 0.75
_SWITCH_MARGIN = 0.001

# Wider still between two routes of the same address family: those
# are nearly always alternate addresses of one interface (a peer's
# ULA, privacy and link-local IPv6 addresses), so the same radio path,
# and any difference in round trip is noise. A truly different path
# (a cable beside Wi-Fi) is many times faster and still wins.
_SWITCH_FRACTION_SAME_FAMILY = 0.5
_SWITCH_MARGIN_SAME_FAMILY = 0.005

# Added to IPv6 routes' scores so equal-RTT IPv4 routes rank first.
_IPV6_TIE_PENALTY = 0.0005


def route_type_bias(route_type: NearbyRouteType) -> float:
    """Seconds added to a route type's round-trip time when ranking.

    The place to favor (or penalize) connection types whose raw
    round-trip time doesn't tell the whole story.
    """
    match route_type:
        case NearbyRouteType.UDP:
            return 0.0
        case _:
            assert_never(route_type)


@dataclass
class RouteState:
    """One address a host has answered at."""

    address: str
    port: int
    last_heard: float
    type: NearbyRouteType = NearbyRouteType.UDP
    srtt: float | None = None
    sources: set[NearbySource] = field(default_factory=set)

    # How often it's currently probed, when the next is due, and probes
    # sent since it last answered (see missed()).
    probe_interval: float = 0.0
    next_probe: float = 0.0
    last_probe: float = 0.0
    unanswered: int = 0

    # Whether we've logged it going quiet (cleared when it answers).
    quiet_logged: bool = False

    # Whether this route has answered a v2 query of each kind (so we
    # know whether to keep sending v1 queries to it).
    game_v2: bool = False
    remote_v2: bool = False

    def missed(self, now: float) -> int:
        """Probes that went unanswered (the latest gets a grace period)."""
        if self.unanswered and now - self.last_probe < _ANSWER_GRACE:
            return self.unanswered - 1
        return self.unanswered


@dataclass
class HostState:
    """One host and the routes it answers at."""

    key: str
    routes: dict[tuple[str, int], RouteState] = field(default_factory=dict)
    best: tuple[str, int] | None = None
    game: NearbyGameInfo | None = None
    game_is_v2: bool = False
    remote: NearbyRemoteInfo | None = None
    remote_is_v2: bool = False


def route_score(route: RouteState) -> float:
    """A route's ranking score (lower is better)."""
    rtt = _UNMEASURED_RTT if route.srtt is None else route.srtt
    # IPv4 wins ties: the old, well-trodden path on most LANs.
    v6_penalty = _IPV6_TIE_PENALTY if ':' in route.address else 0.0
    return rtt + route_type_bias(route.type) + v6_penalty


def route_stale(route: RouteState, now: float) -> bool:
    """Whether a route has missed enough probes to be presumed dead."""
    return route.missed(now) >= ROUTE_STALE_MISSES


def answering_elsewhere(host: HostState, route: RouteState, now: float) -> bool:
    """Whether a host answered its latest probe on some other route.

    A host that goes quiet on one address while still answering on
    another has almost always just lost a probe or two on that address
    (measured on Wi-Fi: the 'quiet' route answers again within seconds
    at a normal round trip), not dropped off the network.
    """
    return any(
        r is not route and r.missed(now) == 0 for r in host.routes.values()
    )


def update_best_route(host: HostState, now: float) -> bool:
    """Pick a host's best route, with hysteresis.

    Only routes still answering are in the running (unless none are).
    A best route that has gone quiet is replaced at once; otherwise a
    new one has to be clearly better. Returns whether the best route
    was replaced because it went quiet with the host answering nowhere
    else: that is news about the network (worth probing at full rate
    for a while). A switch on timing alone is just jitter, and a quiet
    route beside one still answering is most likely lost probes, so
    neither is.
    """
    fresh = [r for r in host.routes.values() if not route_stale(r, now)]
    candidate = min(fresh or host.routes.values(), key=route_score)
    best = host.routes.get(host.best) if host.best is not None else None
    if best is None:
        host.best = (candidate.address, candidate.port)
        return False
    if not best.quiet_logged and route_stale(best, now):
        best.quiet_logged = True
        _log_went_quiet(host, best, now)
    if candidate is best:
        return False
    best_went_quiet = bool(fresh) and best not in fresh
    if (':' in candidate.address) == (':' in best.address):
        fraction = _SWITCH_FRACTION_SAME_FAMILY
        margin = _SWITCH_MARGIN_SAME_FAMILY
    else:
        fraction, margin = _SWITCH_FRACTION, _SWITCH_MARGIN
    if best_went_quiet or route_score(candidate) < (
        route_score(best) * fraction - margin
    ):
        news = best_went_quiet and not answering_elsewhere(host, best, now)
        if not best_went_quiet:
            why = ''
        elif news:
            why = ' (previous best went quiet)'
        else:
            why = ' (previous best went quiet; host still answering elsewhere)'
        logger.debug(
            'Nearby discovery: %s now best reached via %s:%d%s.',
            host.key,
            candidate.address,
            candidate.port,
            why,
        )
        host.best = (candidate.address, candidate.port)
        return news
    return False


def _log_went_quiet(host: HostState, route: RouteState, now: float) -> None:
    """Say why a best route counts as quiet, for chasing lost answers.

    The telling part is whether the host was still answering on its
    other routes (answers coming back from an address other than the
    one probed, or one path failing) or silent on all of them (answers
    lost, e.g. to a dozing Wi-Fi radio).
    """
    if not logger.isEnabledFor(logging.DEBUG):
        return
    others = [r for r in host.routes.values() if r is not route]
    latest = max(others, key=lambda r: r.last_heard, default=None)
    if latest is None:
        elsewhere = 'it has no other routes'
    else:
        elsewhere = (
            f'host last answered on {latest.address}:{latest.port}'
            f' {now - latest.last_heard:.1f}s ago'
        )
    logger.debug(
        'Nearby discovery: %s:%d of %s went quiet: %d probe(s) unanswered'
        ' (last sent %.1fs ago, every %.1fs); its last answer %.1fs ago;'
        ' %s.',
        route.address,
        route.port,
        host.key,
        route.unanswered,
        now - route.last_probe,
        route.probe_interval,
        now - route.last_heard,
        elsewhere,
    )


def public_route(route: RouteState) -> NearbyRoute:
    """The api's view of a route."""
    return NearbyRoute(
        type=route.type,
        address=route.address,
        port=route.port,
        # Rounded to the ms, so jitter below that doesn't count as a
        # change.
        rtt=None if route.srtt is None else round(route.srtt, 3),
        sources=frozenset(route.sources),
    )
