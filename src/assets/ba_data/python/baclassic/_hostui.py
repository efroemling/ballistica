# Released under the MIT License. See LICENSE for details.
#
"""Host-defined ui: menu buttons, host-served doc-ui pages, party notices.

A game host can give its connected clients buttons in their in-game
menu and party window's '...' menu, serve the doc-ui pages those
buttons open, post a party notice below the party icon, and flash the
party icon and '...' button. It all rides the per-connection host-ui
message channel (``bacommon.hostui``). The host's own ui shows the
same things locally.

Design: ``docs/initiatives/host-docui.md``.
"""

import math
import logging
import dataclasses
from dataclasses import dataclass
from typing import TYPE_CHECKING

from efro.util import strip_exception_tracebacks
from efro.dataclassio import dataclass_to_json, dataclass_from_json
import bacommon.hostui as hui
import bacommon.docui.v2 as dui2
import bacommon.docui.routes.classichost as hroutes

import babase
import bascenev1
from bascenev1 import _classicassets

from baclassic._hostuibutton import HostUIButton, button_to_wire
from baclassic._hostuiparts import host_ui_text
from baclassic._hostuistats import HostUIStatsPage
from baclassic._hostuikick import HostUIKickRequest, HostUIKickVotes
from baclassic._hostuimembers import HostUIClientPage, HostUIPlayerPage
from baclassic._hostuihandler import (
    HostUIHandler,
    run_handler,
    status_response,
)
from baclassic._hostuiwire import (
    PROBE_IDS,
    check_host_label,
    client_page_target,
    decode_message,
    kick_target,
    send_response,
    vet_state,
)

if TYPE_CHECKING:
    from typing import Callable, Literal, Sequence
    from concurrent.futures import Future

    import bacommon.hostui
    import bacommon.depiction
    import bacommon.docui.v2

    from bacommon.langstr import LangStrSpec
    from bacommon.docui.routes import DocUIRoute

logger = logging.getLogger('ba.net')

#: How close (seconds) a re-sent flash end time must be to the current
#: one to count as the same flash (so re-sending a state doesn't restart
#: a flash's quick phase).
_FLASH_END_TOLERANCE = 1.0


@dataclass
class _Timed[T]:
    """A notice or flash for some span of app-time."""

    posted: float
    end: float
    value: T


@dataclass
class _RequestLimit:
    """Rate limiting for one client's requests (a token bucket)."""

    tokens: float
    updated: float
    in_flight: int = 0
    warned: bool = False


class HostUISubsystem:  # pylint: disable=too-many-public-methods
    """Host-defined ui, from both ends.

    Access the single shared instance of this class via
    ``app.classic.host_ui``.

    As a host: set the buttons everyone gets with :meth:`set_buttons`
    (or one client's with :meth:`set_client_buttons`), post notices
    with :meth:`post_notice`, flash things with
    :meth:`flash_party_icon` and :meth:`flash_party_menu`, and serve
    pages by assigning :attr:`handler`. Clients are kept up to date
    automatically, joiners included.

    As a client, this holds what our host has declared to us.
    """

    def __init__(self) -> None:
        #: Serves the pages host buttons open.
        self.handler: HostUIHandler = HostUIHandler()

        #: The default stats page (assign a subclass to customize it).
        self.stats_page: HostUIStatsPage = HostUIStatsPage()

        #: The standard kick vote (assign a subclass to customize it).
        self.kick_votes: HostUIKickVotes = HostUIKickVotes()

        #: The default party member page (assign a subclass to customize
        #: it).
        self.client_page: HostUIClientPage = HostUIClientPage()

        #: The default player page (assign a subclass to customize it).
        self.player_page: HostUIPlayerPage = HostUIPlayerPage()

        #: V2 account ids (a-XXX) of this host's admins. Admins can't be
        #: kicked by vote, and kick without one.
        self.admins: set[str] = set()

        # (None while it's kick_votes'; see set_kick_page().)
        self._kick_page_getter: (
            Callable[[HostUIKickRequest], DocUIRoute | None] | None
        ) = None
        self._kick_page_offered = True
        # (None while it's client_page's; see set_client_page().)
        self._client_page_getter: Callable[[int], dui2.Browse] | None = None
        self._client_page_offered = True
        self._known_clients: set[int] = set()

        # Host side. (Notice/flash dicts are keyed by client id, or
        # None for everyone.)
        # (None until first needed: the defaults' labels are language
        # strings, which can't be looked up this early in launch.)
        self._buttons: list[HostUIButton] | None = None
        self._client_buttons: dict[int, list[HostUIButton]] = {}
        self._notices: dict[int | None, _Timed[LangStrSpec | None]] = {}
        self._icon_flashes: dict[int | None, _Timed[bool]] = {}
        self._menu_flashes: dict[int | None, _Timed[bool]] = {}
        self._sent_clients: set[int] = set()
        self._request_limits: dict[int, _RequestLimit] = {}

        # Verified account name depictions (json) from v2 auth, by
        # account id, with when we got each.
        self._account_name_depictions: dict[str, tuple[str, float]] = {}

        # Client side: what we're currently showing, and whether it came
        # from our own hosting ('local') or from a host ('remote').
        self._shown: hui.State | None = None
        self._shown_source: Literal['local', 'remote'] | None = None
        self._notice_end = 0.0
        self._icon_flash_end = 0.0
        self._menu_flash_start = 0.0
        self._menu_flash_end = 0.0
        self._pending: dict[int, Future[dui2.Response | bytes | None]] = {}
        self._next_request_id = 0

        self._timer: babase.AppTimer | None = None

    # ------------------------------------------------------------------
    # Host api.

    def get_buttons(self) -> list[HostUIButton]:
        """The buttons every client gets (unless overridden per client)."""
        if self._buttons is None:
            self._buttons = _default_buttons()
        return list(self._buttons)

    def set_buttons(self, buttons: Sequence[HostUIButton]) -> None:
        """Set the buttons every client gets.

        Clients with their own (see :meth:`set_client_buttons`) keep
        theirs.
        """
        for button in buttons:
            check_host_label(button.label)
        self._buttons = list(buttons)
        self._push(None)

    def set_client_buttons(
        self, client_id: int, buttons: Sequence[HostUIButton] | None
    ) -> None:
        """Give one client its own set of buttons (None to undo).

        Use -1 for the host's own ui. Forgotten when the client leaves.
        """
        if buttons is None:
            self._client_buttons.pop(client_id, None)
        else:
            for button in buttons:
                check_host_label(button.label)
            self._client_buttons[client_id] = list(buttons)
        self._push([client_id])

    def post_notice(
        self,
        text: str | babase.LangStr | LangStrSpec,
        duration: float,
        *,
        clients: Sequence[int] | None = None,
    ) -> None:
        """Show a notice below the party icon for a while.

        Replaces any notice showing (the most recently posted notice
        wins). ``clients`` limits it to some clients (-1 is the host);
        None means everyone. A language-string must come from one of the
        host's own asset-packages.
        """
        spec = host_ui_text(text)
        check_host_label(spec)
        self._post(self._notices, spec, duration, clients)

    def clear_notice(self, *, clients: Sequence[int] | None = None) -> None:
        """Take down the notice (for some clients, or everyone)."""
        self._post(self._notices, None, None, clients)

    def flash_party_icon(
        self, duration: float, *, clients: Sequence[int] | None = None
    ) -> None:
        """Flash the party icon for a while (0 to stop)."""
        self._post(
            self._icon_flashes,
            duration > 0.0,
            duration if duration > 0.0 else None,
            clients,
        )

    def flash_party_menu(
        self, duration: float, *, clients: Sequence[int] | None = None
    ) -> None:
        """Flash the party window's '...' button for a while (0 to stop)."""
        self._post(
            self._menu_flashes,
            duration > 0.0,
            duration if duration > 0.0 else None,
            clients,
        )

    def set_kick_page(
        self,
        get_route: Callable[[HostUIKickRequest], DocUIRoute | None] | None,
    ) -> None:
        """Set where clients go when they choose to kick someone.

        The one place kicking is decided. ``get_route`` is called with a
        :class:`baclassic.HostUIKickRequest` (who would be kicked, who
        is asking, and the player they picked, if any) and returns the
        page for it (which your :attr:`handler` serves), or None to
        offer that viewer no kick option there. Nobody is offered
        kicking the host, themselves, or someone not here; you're only
        asked about the rest. None offers kicking to nobody.

        By default the standard kick vote's
        (:meth:`baclassic.HostUIKickVotes.get_kick_page`, of whatever
        :attr:`kick_votes` is at the time), which uses only public api
        and so works as an example to copy or wrap.

        Clients from build 23075 on get to it from party member and
        player pages (see :meth:`set_client_page`); older ones from their
        party list, which asks without a player.
        """
        self._kick_page_getter = get_route
        self._kick_page_offered = get_route is not None
        self._push(None)

    def get_kick_page(self, request: HostUIKickRequest) -> DocUIRoute | None:
        """Where a kick request goes, as set by :meth:`set_kick_page`.

        None if the viewer isn't offered kicking that client.
        """
        if (
            request.client_id
            in (
                -1,
                request.viewer,
            )
            or request.client_id not in self.get_client_ids()
        ):
            return None
        return self._ask_kick_page(request)

    def _ask_kick_page(self, request: HostUIKickRequest) -> DocUIRoute | None:
        if not self._kick_page_offered:
            return None
        getter = self._kick_page_getter or self.kick_votes.get_kick_page
        return getter(request)

    def set_client_page(
        self, get_browse: Callable[[int], dui2.Browse] | None
    ) -> None:
        """Set what opens when clients pick a party member.

        ``get_browse`` is called with a client id (-1 for the host) and
        returns how to open the page for that member (which your
        :attr:`handler` serves): a route's ``browse()``, which may also
        set the window's look. Party windows (build 23075 and up) open it
        when a member's name is pressed, in the party list or in chat.
        Pages linking to a member (the player page's Connection button)
        use it too (see :meth:`get_client_page`). By default
        :attr:`client_page`'s (:meth:`baclassic.HostUIClientPage.get_browse`,
        of whatever :attr:`client_page` is at the time). None offers no
        page; party lists then fall back to their older kick option
        (see :meth:`set_kick_page`).
        """
        if get_browse is not None:
            # Check it now rather than on every send.
            client_page_target(get_browse)
        self._client_page_getter = get_browse
        self._client_page_offered = get_browse is not None
        self._push(None)

    def get_client_page(self, client_id: int) -> dui2.Browse | None:
        """How to open a party member's page, as :meth:`set_client_page` says.

        None while no member page is offered. For linking to one from a
        page of your own.
        """
        if not self._client_page_offered:
            return None
        getter = self._client_page_getter or self.client_page.get_browse
        return getter(client_id)

    def get_client_players(
        self, client_id: int
    ) -> list[bascenev1.SessionPlayer]:
        """A client's players in the game (-1 for the host's own).

        In join order; not including players still choosing a profile in
        the lobby.
        """
        session = bascenev1.get_foreground_host_session()
        if session is None:
            return []
        return [
            p
            for p in session.sessionplayers
            if p.in_game and p.inputdevice.client_id == client_id
        ]

    def refresh_clients(self) -> None:
        """Send everyone their current state again.

        For when something the state is built from changed without going
        through this class (such as the buttons
        :meth:`baclassic.HostUIKickVotes.get_buttons` adds).
        """
        self._push(None)

    def get_client_ids(self) -> list[int]:
        """Ids of the clients connected to us (not including the host)."""
        return self._client_ids()

    def client_has_host_ui(self, client_id: int) -> bool:
        """Whether a client can see host buttons, notices, and pages.

        (Clients predating them can't.) True for the host (-1) while it
        has ui.
        """
        if client_id == -1:
            return babase.app.env.gui
        return client_id in self._sent_clients

    def get_client_account_id(self, client_id: int) -> str | None:
        """A client's verified v2 account id (a-XXX), if it has one.

        Client id -1 is the host (our own signed-in account).
        """
        if client_id == -1:
            plus = babase.app.plus
            primary = None if plus is None else plus.accounts.primary
            return None if primary is None else primary.accountid
        for entry in bascenev1.get_game_roster():
            if entry['client_id'] == client_id:
                account_id = entry['account_id']
                # The roster also carries v1 ids (pb-XXX) for clients
                # the legacy master vouched for; we only deal in v2.
                if isinstance(account_id, str) and account_id.startswith('a-'):
                    return account_id
                return None
        return None

    def get_client_name(self, client_id: int) -> str | None:
        """A client's name as the party list shows it (None if not here).

        Repeated names are numbered ("iPhone 2"); see
        ``bascenev1.get_party_member_names()``.
        """
        return bascenev1.get_party_member_names().get(client_id)

    def get_account_name_depiction(
        self, account_id: str
    ) -> bacommon.depiction.Depiction | None:
        """An account's name as it draws in game, if we know it.

        Known for our own account, and for clients that joined with v2
        auth (so it is verified by the master server); see
        ``get_game_roster()`` for each client's account id. None
        otherwise.
        """
        import bacommon.depiction as bdep

        plus = babase.app.plus
        classic = babase.app.classic
        primary = None if plus is None else plus.accounts.primary
        depjson: str | None
        if (
            classic is not None
            and primary is not None
            and account_id == primary.accountid
        ):
            depjson = classic.account_name_depiction or None
        else:
            entry = self._account_name_depictions.get(account_id)
            depjson = None if entry is None else entry[0]
        if depjson is None:
            return None
        # Not lossy: depictions get written back out when served, which
        # lossy-decoded objects can't be.
        try:
            return dataclass_from_json(bdep.Depiction, depjson)
        except Exception as exc:
            logger.exception('Invalid account name depiction json.')
            strip_exception_tracebacks(exc)
            return None

    def note_account_name_depiction(
        self, account_id: str, depiction_json: str
    ) -> None:
        """Remember an account's name depiction from v2 auth.

        :meta private:
        """
        self._account_name_depictions[account_id] = (
            depiction_json,
            babase.apptime(),
        )

    # ------------------------------------------------------------------
    # Client-side api (for our ui).

    def get_shown_buttons(
        self, placement: bacommon.hostui.ButtonPlacement
    ) -> list[bacommon.hostui.Button]:
        """Host-defined buttons to show at a placement.

        :meta private:
        """
        if self._shown is None:
            return []
        return [b for b in self._shown.buttons if b.placement is placement]

    def get_kick_request(
        self, client_id: int
    ) -> bacommon.docui.v2.Request | None:
        """The page to open to kick a party member (None if not offered).

        :meta private:
        """
        kick = None if self._shown is None else self._shown.kick
        if kick is None:
            return None
        return dataclasses.replace(
            kick.request,
            args={**kick.request.args, kick.client_id_arg: client_id},
        )

    def get_client_page_browse(
        self, client_id: int
    ) -> bacommon.docui.v2.Browse | None:
        """How to open a party member's page (None if not offered).

        :meta private:
        """
        target = None if self._shown is None else self._shown.client_page
        if target is None:
            return None
        request = target.browse.request
        return dataclasses.replace(
            target.browse,
            request=dataclasses.replace(
                request,
                args={**request.args, target.client_id_arg: client_id},
            ),
        )

    def get_party_menu_flash_times(self) -> tuple[float, float]:
        """App-times the party window's '...' button flashes between.

        :meta private:
        """
        return self._menu_flash_start, self._menu_flash_end

    def submit_request(
        self,
        request: bacommon.docui.v2.Request,
        future: Future[bacommon.docui.v2.Response | bytes | None],
    ) -> None:
        """Get a page from whoever is serving our host-ui pages.

        Must be called in the logic thread. ``future`` gets the response
        (when we're the host), the response as a host sent it (bytes to
        decode with :func:`bacommon.hostui.decode_response`, so that can
        happen off the logic thread), or None if the request could not
        be made.

        :meta private:
        """
        assert babase.in_logic_thread()
        if self._shown_source == 'local':
            # We're the host; serve ourself.
            run_handler(self.handler, request, -1, future.set_result)
            return
        if self._shown_source != 'remote':
            future.set_result(None)
            return
        request_id = self._next_request_id
        self._next_request_id += 1
        msg = dataclass_to_json(
            hui.DocUIRequestMessage(request_id=request_id, request=request)
        )
        if len(msg) > hui.MAX_REQUEST_BYTES:
            logger.warning(
                'Host-ui request too large to send (%d bytes).', len(msg)
            )
            future.set_result(None)
            return
        if not bascenev1.host_ui_send_to_host(msg):
            logger.warning(
                'Could not send host-ui request for %r to our host.',
                request.path,
            )
            future.set_result(None)
            return
        self._pending[request_id] = future

    # ------------------------------------------------------------------
    # Internal.

    def start(self, *, tick_now: bool = False) -> None:
        """Start periodic upkeep (as classic app-mode activates).

        ``tick_now`` runs the first upkeep pass immediately.

        :meta private:
        """
        assert self._timer is None
        self._timer = babase.AppTimer(
            1.0, babase.WeakCallStrict(self._tick), repeat=True
        )
        if tick_now:
            self._tick()

    def stop(self) -> None:
        """Stop periodic upkeep (as classic app-mode deactivates).

        :meta private:
        """
        self._timer = None

    def on_message_from_host(self, msg: str) -> None:
        """Handle a host-ui message from our host.

        :meta private:
        """
        if len(msg) > hui.MAX_RESPONSE_BYTES:
            logger.warning(
                'Ignoring oversized host-ui message (%d bytes).', len(msg)
            )
            return
        message = decode_message(msg, from_host=True)
        if message is None:
            return
        if isinstance(message, hui.StateMessage):
            self._show(message.state, 'remote')
        elif isinstance(message, hui.DocUIResponseMessage):
            # Hand over the still-encoded response; whoever is waiting
            # decodes it off our thread.
            future = self._pending.pop(message.request_id, None)
            if future is not None and not future.done():
                future.set_result(message.data)
        else:
            logger.debug('Ignoring host-ui message %s from host.', message)

    def on_message_from_client(self, msg: str, client_id: int) -> None:
        """Handle a host-ui message from one of our clients.

        :meta private:
        """
        message = decode_message(msg)
        if message is None:
            return
        if not isinstance(message, hui.DocUIRequestMessage):
            logger.debug(
                'Ignoring host-ui message %s from client %d.',
                message,
                client_id,
            )
            return
        request_id = message.request_id
        request = message.request
        limit = self._take_request_slot(client_id)
        if limit is None:
            self._send_response(
                client_id,
                request_id,
                status_response(dui2.ResponseStatus.UNKNOWN_ERROR),
            )
            return
        if not isinstance(request, dui2.Request):
            limit.in_flight -= 1
            self._send_response(
                client_id,
                request_id,
                status_response(dui2.ResponseStatus.NEED_UPDATE_ERROR),
            )
            return

        def _done(response: dui2.Response) -> None:
            limit.in_flight -= 1
            self._send_response(client_id, request_id, response)

        run_handler(self.handler, request, client_id, _done)

    def _take_request_slot(self, client_id: int) -> _RequestLimit | None:
        """Account for a request from a client, if it may make one.

        Clients are untrusted and handlers can be costly, so each gets a
        burst of requests then a steady rate, and only so many at once.
        """
        now = babase.apptime()
        limit = self._request_limits.get(client_id)
        if limit is None:
            limit = self._request_limits[client_id] = _RequestLimit(
                tokens=float(hui.REQUEST_BURST), updated=now
            )
        limit.tokens = min(
            float(hui.REQUEST_BURST),
            limit.tokens + (now - limit.updated) * hui.REQUESTS_PER_SECOND,
        )
        limit.updated = now
        if limit.tokens < 1.0 or limit.in_flight >= hui.MAX_REQUESTS_IN_FLIGHT:
            if not limit.warned:
                limit.warned = True
                logger.warning(
                    'Rate limiting host-ui requests from client %d.', client_id
                )
            return None
        limit.tokens -= 1.0
        limit.in_flight += 1
        return limit

    def _send_response(
        self, client_id: int, request_id: int, response: dui2.Response
    ) -> None:
        babase.app.create_async_task(
            send_response(client_id, request_id, response)
        )

    def _post[T](
        self,
        store: dict[int | None, _Timed[T]],
        value: T,
        duration: float | None,
        clients: Sequence[int] | None,
    ) -> None:
        """Record a notice/flash (or, with no duration, a stop).

        Whatever was posted most recently for a client wins, so a stop
        is a record too: one lasting until something newer comes along
        (otherwise stopping it for one client would let an everyone-
        entry show through).
        """
        now = babase.apptime()
        end = math.inf if duration is None else now + max(0.0, duration)
        timed = _Timed(posted=now, end=end, value=value)
        if clients is None:
            # Supersedes everything, so per-client entries can go.
            store.clear()
            store[None] = timed
        else:
            for client_id in clients:
                store[client_id] = timed
        self._push(None if clients is None else list(clients))

    def _hosting(self) -> bool:
        # Our timer runs exactly while classic app-mode is active (see
        # start()/stop()), so it doubles as that check.
        return (
            self._timer is not None
            and bascenev1.get_connection_to_host_info_2() is None
        )

    def _client_ids(self) -> list[int]:
        return [
            e['client_id']
            for e in bascenev1.get_game_roster()
            if e['client_id'] != -1
        ]

    def _push(self, clients: Sequence[int] | None) -> None:
        """Send current state to clients (None for everyone + us)."""
        if not self._hosting():
            return
        targets = (
            [-1, *self._client_ids()] if clients is None else list(clients)
        )
        for client_id in targets:
            state = self._state_for(client_id)
            if client_id == -1:
                self._show(state, 'local')
            elif bascenev1.host_ui_send_to_client(
                client_id, dataclass_to_json(hui.StateMessage(state=state))
            ):
                self._sent_clients.add(client_id)

    def _kick_target_for(self, viewer: int) -> hui.KickTarget | None:
        """How a viewer's (older) party list kicks: one request for all.

        Party lists predating member pages fill in the client id
        themselves, so the kick page is asked about two stand-in clients
        on the viewer's behalf (no player picked) and the arg that
        differs is the id. Kicking anyone is offered only if both get a
        page.
        """
        try:
            route_a, route_b = (
                self._ask_kick_page(
                    HostUIKickRequest(client_id=probe, viewer=viewer)
                )
                for probe in PROBE_IDS
            )
            if route_a is None or route_b is None:
                return None
            return kick_target(route_a, route_b)
        except Exception as exc:
            # (A broken kick page getter; don't let it stop the rest of
            # the state going out.)
            logger.exception('Error describing host-ui kick page.')
            strip_exception_tracebacks(exc)
            return None

    def _client_page_target(self) -> hui.ClientPageTarget | None:
        if not self._client_page_offered:
            return None
        getter = self._client_page_getter or self.client_page.get_browse
        try:
            return client_page_target(getter)
        except Exception as exc:
            # (A broken client_page override; don't let it stop the rest
            # of the state going out.)
            logger.exception('Error describing host-ui client page.')
            strip_exception_tracebacks(exc)
            return None

    def _state_for(self, client_id: int) -> hui.State:
        now = babase.apptime()
        notice = _current(self._notices, client_id, now)
        icon_flash = _current(self._icon_flashes, client_id, now)
        menu_flash = _current(self._menu_flashes, client_id, now)
        buttons = [
            *self._client_buttons.get(client_id, self.get_buttons()),
            *self.kick_votes.get_buttons(client_id),
        ]
        return hui.State(
            buttons=[button_to_wire(b) for b in buttons],
            kick=self._kick_target_for(client_id),
            client_page=self._client_page_target(),
            notice=None if notice is None else notice.value,
            notice_time_left=(
                0.0
                if notice is None or notice.value is None
                else notice.end - now
            ),
            party_icon_flash_time_left=(
                icon_flash.end - now
                if icon_flash is not None and icon_flash.value
                else 0.0
            ),
            party_menu_flash_time_left=(
                menu_flash.end - now
                if menu_flash is not None and menu_flash.value
                else 0.0
            ),
        )

    def _tick(self) -> None:
        # (Only ticks while ClassicAppMode is active; see start()/stop().)
        now = babase.apptime()

        if self._hosting():
            # Stop showing anything a host we left gave us.
            if self._shown_source == 'remote':
                self._clear_shown()
            if self._shown_source is None:
                self._push([-1])

            # Forget clients that left; bring new ones up to date
            # (retrying ones not ready yet, or too old to care).
            client_ids = set(self._client_ids())
            self._forget_departed_clients(client_ids)
            self._prune_account_name_depictions(now)
            self.kick_votes.update()
            unsent = sorted(client_ids - self._sent_clients)
            if unsent:
                self._push(unsent)
        else:
            # We're a client; stop showing anything from our own
            # hosting.
            if self._shown_source == 'local':
                self._clear_shown()

        # Notices run out on their own.
        if self._shown is not None and self._shown.notice is not None:
            if now >= self._notice_end:
                self._shown.notice = None
                if babase.app.env.gui:
                    import bauiv1

                    bauiv1.set_party_notice(None)

        # Drop requests nobody is waiting on anymore.
        for request_id, future in list(self._pending.items()):
            if future.done():
                del self._pending[request_id]

    def _forget_departed_clients(self, client_ids: set[int]) -> None:
        """Drop per-client state for clients no longer connected."""
        for client_id in client_ids - self._known_clients:
            self.kick_votes.on_client_seen(client_id)
        for client_id in self._known_clients - client_ids:
            self.kick_votes.on_client_gone(client_id)
        self._known_clients = set(client_ids)
        self._sent_clients &= client_ids
        for limit_client_id in list(self._request_limits):
            if limit_client_id not in client_ids:
                del self._request_limits[limit_client_id]
        for store in (
            self._client_buttons,
            self._notices,
            self._icon_flashes,
            self._menu_flashes,
        ):
            for key in list(store):
                if key is not None and key != -1 and key not in client_ids:
                    del store[key]

    def _prune_account_name_depictions(self, now: float) -> None:
        """Forget accounts no longer connected.

        (Entries get a grace period, as auth comes a bit before the
        client shows up in the roster.)
        """
        if not self._account_name_depictions:
            return
        present = {
            e['account_id']
            for e in bascenev1.get_game_roster()
            if e['account_id'] is not None
        }
        for account_id, (_json, noted) in list(
            self._account_name_depictions.items()
        ):
            if account_id not in present and now - noted > 60.0:
                del self._account_name_depictions[account_id]

    def _show(
        self, state: hui.State, source: Literal['local', 'remote']
    ) -> None:
        """Show a state, after vetting it if it came from a host."""
        if source == 'remote':
            state = vet_state(state)
        self._shown = state
        self._shown_source = source
        now = babase.apptime()
        self._notice_end = (
            0.0 if state.notice is None else now + state.notice_time_left
        )
        menu_flash_end = (
            0.0
            if state.party_menu_flash_time_left <= 0.0
            else now + state.party_menu_flash_time_left
        )
        # Only (re)start a flash if this is a different one; re-sent
        # states shouldn't restart its quick phase.
        if abs(menu_flash_end - self._menu_flash_end) > _FLASH_END_TOLERANCE:
            self._menu_flash_start = now
        self._menu_flash_end = menu_flash_end
        icon_flash_end = (
            0.0
            if state.party_icon_flash_time_left <= 0.0
            else now + state.party_icon_flash_time_left
        )
        if not babase.app.env.gui:
            return

        import bauiv1

        bauiv1.set_party_notice(
            None if state.notice is None else native_langstr(state.notice)
        )
        if abs(icon_flash_end - self._icon_flash_end) > _FLASH_END_TOLERANCE:
            bauiv1.flash_party_icon(max(0.0, icon_flash_end - now))
        self._icon_flash_end = icon_flash_end

    def _clear_shown(self) -> None:
        self._shown = None
        self._shown_source = None
        self._notice_end = 0.0
        self._menu_flash_end = 0.0
        for future in self._pending.values():
            if not future.done():
                future.set_result(None)
        self._pending.clear()
        if babase.app.env.gui:
            import bauiv1

            bauiv1.set_party_notice(None)
            if self._icon_flash_end > babase.apptime():
                bauiv1.flash_party_icon(0.0)
        self._icon_flash_end = 0.0


def native_langstr(spec: LangStrSpec) -> babase.LangStr:
    """A native language-string for a host-ui spec.

    :meta private:
    """
    return babase.LangStr(dataclass_to_json(spec))


def _default_buttons() -> list[HostUIButton]:
    return [
        HostUIButton(
            label=_classicassets.strings.host_ui.stats_title,
            browse=hroutes.Stats().browse(),
        ),
    ]


def _current[T](
    store: dict[int | None, _Timed[T]], client_id: int, now: float
) -> _Timed[T] | None:
    """The most recently posted unexpired entry that applies to a client."""
    candidates = [
        t
        for t in (store.get(None), store.get(client_id))
        if t is not None and t.end > now
    ]
    return max(candidates, key=lambda t: t.posted, default=None)
