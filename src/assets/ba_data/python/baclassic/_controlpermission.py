# Released under the MIT License. See LICENSE for details.
#
"""Deciding who may control this app.

Something outside the app -- today the cloud console -- can ask to
run commands here and read this app's log. That is a large amount of
trust to hand over on someone else's say-so, so it is gated on the
person at the device saying yes.

This module holds the *policy* half of that: whether we already have
a live grant for whoever is asking, and how those grants are
remembered. Putting the question on screen is the UI layer's job.
"""

import time
import logging
from typing import TYPE_CHECKING

import babase

if TYPE_CHECKING:
    from collections.abc import Callable

logger = logging.getLogger('ba.controlpermission')

#: App-config key holding remembered grants: requester key -> the
#: unix time it stops counting.
_CONFIG_KEY = 'Control Grants'

#: How long 'always allow' actually lasts. Deliberately finite: a
#: permanent grant is one the user has no reason to ever revisit,
#: and one stolen browser session later they'd never know it was
#: still open. A month is long enough that a regular user isn't
#: re-answering constantly, short enough that access decays.
GRANT_DURATION_SECONDS = 30 * 24 * 60 * 60

#: Cap on how many grants we keep. Someone who consoles in from many
#: places shouldn't grow this list without bound; past the cap the
#: soonest-to-expire is dropped, so the most durable grants survive.
_MAX_GRANTS = 16


def _stored_grants() -> dict[str, float]:
    """Read remembered grants out of the app config."""
    raw = babase.app.config.get(_CONFIG_KEY)
    if not isinstance(raw, dict):
        return {}
    # Be forgiving about what's on disk; a malformed entry should cost
    # that entry, not the whole list.
    out: dict[str, float] = {}
    for key, expire_time in raw.items():
        if isinstance(key, str) and isinstance(expire_time, (int, float)):
            out[key] = float(expire_time)
    return out


def _store_grants(grants: dict[str, float]) -> None:
    """Write remembered grants back to the app config."""
    if grants:
        babase.app.config[_CONFIG_KEY] = grants
    else:
        babase.app.config.pop(_CONFIG_KEY, None)
    babase.app.config.commit()


def prune_grants() -> dict[str, float]:
    """Drop expired grants and return what's left.

    Pruning is lazy -- it happens whenever grants are looked at --
    because there is no moment worth waking up for: an expired grant
    is inert either way, and the only cost of it lingering unread is
    a config entry.
    """
    now = time.time()
    grants = {k: v for k, v in _stored_grants().items() if v > now}
    if len(grants) > _MAX_GRANTS:
        keep = sorted(grants.items(), key=lambda i: i[1], reverse=True)
        grants = dict(keep[:_MAX_GRANTS])
    if grants != _stored_grants():
        _store_grants(grants)
    return grants


def remember_grant(requester_key: str) -> None:
    """Let this requester back in without asking again, for a while."""
    grants = prune_grants()
    grants[requester_key] = time.time() + GRANT_DURATION_SECONDS
    _store_grants(grants)


def forget_grant(requester_key: str) -> None:
    """Revoke a remembered grant."""
    grants = prune_grants()
    if grants.pop(requester_key, None) is not None:
        _store_grants(grants)


def grant_expire_times() -> dict[str, float]:
    """Live grants and when each runs out, for showing the user.

    Revoking is only meaningful if the grants are visible, so this is
    part of the feature rather than a debugging aid.
    """
    return prune_grants()


def handle_request(
    request: babase.ControlPermissionRequest,
    on_result: Callable[[babase.ControlPermission], None],
) -> bool:
    """Answer from standing policy alone, if we can.

    Returns whether it was answered. A ``False`` return means nothing
    here settles it and the user has to be asked.
    """
    # A dedicated server has nobody to ask, and its operator is the
    # account owner already -- refusing there would make the cloud
    # console useless for the servers it's most used on. (Note that
    # drawing a dialog is not the test: those draw in server mode
    # too. What matters is whether a human is watching.)
    if not babase.app.env.gui:
        on_result(babase.ControlPermission.ALLOW)
        return True

    key = request.requester_key
    if key is not None and key in prune_grants():
        logger.debug('control request allowed by remembered grant')
        on_result(babase.ControlPermission.ALLOW)
        return True

    return False
