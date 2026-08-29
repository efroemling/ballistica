# Released under the MIT License. See LICENSE for details.
#
"""In-memory cache of doc-ui responses, for instant page re-display.

Holds responses in the form
:meth:`~bauiv1lib.docui.DocUIController.fulfill_request` produced them
-- never de-indexed, so an entry can be re-prepped at whatever ui-scale
or window size it next appears at. Entries are keyed by who asked for
what: the controller, the request, and the audience the server tailored
the response to (account and locale).

Re-opening a cached page shows it immediately and then refreshes in the
background, so what's on screen is never more than one round-trip
stale. That refresh is what makes entries need no expiry, and it is
load-bearing for more than server freshness: a controller may splice
locally-authored content into what it returns (the inventory's player
profiles are built from local config), and only the refetch re-runs
that splice. An entry is only as current as the local state at the
moment it was stored.

The cache deliberately lives at module scope rather than on
:class:`~bauiv1lib.docui.DocUIController`. Controllers are constructed
per window-open (``StoreUIController().create_window(...)``) and die
with the window, so an instance-level cache would never see a hit.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from bacommon.docui import DocUIRequest, DocUIResponse

    from bauiv1lib.docui import DocUIController

#: Max entries held. Distinct doc-ui destinations are few, but request
#: args are not: any page taking free-form args (an item id, a page
#: offset) mints an entry per value, so cap the count rather than
#: trusting the page count to stay small. Entries are small enough that
#: the exact figure doesn't matter much.
MAX_ENTRIES = 48

#: Insertion-ordered, so the oldest entry is simply the first one; a
#: read moves its entry to the end to make this an LRU.
_entries: 'dict[str, DocUIResponse]' = {}


def _key(controller: 'DocUIController', request: 'DocUIRequest') -> str | None:
    """Cache key for a request, or None if it must not be cached.

    Account and locale are part of the *key* rather than a validity
    check on a shared entry. Two accounts' store pages are different
    pages, not stale versions of one, so keying them apart both keeps
    each cached independently and makes serving one account's page to
    another structurally impossible rather than a check we could
    forget.
    """
    import json

    import bauiv1 as bui
    import bacommon.docui.v2 as dui2
    from efro.dataclassio import dataclass_to_dict

    # Only v2 GETs. POSTs may have side-effects, so they are neither
    # replayable from cache nor safe to auto-refresh.
    if (
        not isinstance(request, dui2.Request)
        or request.method is not dui2.RequestMethod.GET
    ):
        return None

    # A controller may serve different pages from one request path
    # depending on its own state; it declares that here.
    extra = controller.get_cache_key_extra()
    if extra is None:
        return None

    plus = bui.app.plus
    accountid = ''
    if plus is not None:
        account = plus.accounts.primary
        if account is not None:
            accountid = account.accountid

    # Sorted, so two logically-equal arg dicts built in different
    # orders land on the same entry.
    reqkey = json.dumps(
        dataclass_to_dict(request), sort_keys=True, separators=(',', ':')
    )

    ctp = type(controller)
    return (
        f'{ctp.__module__}.{ctp.__qualname__}'
        f'|{extra}'
        f'|{accountid}'
        f'|{bui.app.locale.current_locale.name}'
        f'|{reqkey}'
    )


def _describe(request: 'DocUIRequest') -> str:
    """Short human-readable form of a request, for logging."""
    import bacommon.docui.v2 as dui2

    if isinstance(request, dui2.Request):
        return f'{request.path!r}' + (
            f' {request.args}' if request.args else ''
        )
    return repr(request)


def get(
    controller: 'DocUIController', request: 'DocUIRequest'
) -> 'DocUIResponse | None':
    """Return a cached response for a request, if we have one.

    The returned response is shared with every other holder of it --
    the window, its back-stack state, this cache -- so treat it as
    read-only; prep makes its own copy to de-index (see
    :func:`~bauiv1lib.docui._resolve.deindex_response`).
    """
    import bauiv1 as bui

    assert bui.in_logic_thread()

    key = _key(controller, request)
    if key is None:
        return None

    response = _entries.get(key)
    if response is None:
        bui.uilog.debug('docui cache: miss for %s.', _describe(request))
        return None

    # Freshen for LRU purposes.
    del _entries[key]
    _entries[key] = response

    bui.uilog.debug('docui cache: hit for %s.', _describe(request))
    return response


def put(
    controller: 'DocUIController',
    request: 'DocUIRequest',
    response: 'DocUIResponse',
) -> None:
    """Store a freshly fetched response.

    Pass the response as fulfillment produced it, never a de-indexed
    one; the whole point of the entry is that it can be re-prepped
    later at a different ui-scale or window size.
    """
    import bauiv1 as bui

    assert bui.in_logic_thread()

    key = _key(controller, request)
    if key is None:
        return

    # Re-insert so an updated entry counts as most-recently-used.
    updating = key in _entries
    if updating:
        del _entries[key]
    _entries[key] = response

    bui.uilog.debug(
        'docui cache: %s %s (%d entries).',
        'updated' if updating else 'stored',
        _describe(request),
        len(_entries),
    )

    while len(_entries) > MAX_ENTRIES:
        del _entries[next(iter(_entries))]


def clear() -> None:
    """Drop everything we hold."""
    import bauiv1 as bui

    assert bui.in_logic_thread()

    _entries.clear()
