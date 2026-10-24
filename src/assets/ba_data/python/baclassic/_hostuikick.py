# Released under the MIT License. See LICENSE for details.
#
"""The standard host kick vote (see :class:`HostUIKickVotes`)."""

import logging
import datetime
from enum import Enum
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, assert_never

import bacommon.docui.v2 as dui2
from bacommon.langstr import LangStrSpec, LangStrSpecValue
import bacommon.docui.routes.classichost as hroutes
from efro.dataclassio import dataclass_from_json

import babase
import bascenev1
from bascenev1 import _builtinassets, _classicassets, _commonassets

if TYPE_CHECKING:
    from bacommon.docui.routes import DocUIRoute

    from baclassic._hostui import HostUIButton, HostUISubsystem

logger = logging.getLogger('ba.net')


class KickVoteRefusal(Enum):
    """Why a kick vote can't be started."""

    #: Kick voting is turned off.
    DISABLED = 'disabled'

    #: The player isn't here (anymore).
    NOT_PRESENT = 'not_present'

    #: Nobody can kick themselves.
    SELF = 'self'

    #: The host and admins can't be kicked.
    ADMIN = 'admin'

    #: A vote is already running.
    IN_PROGRESS = 'in_progress'

    #: Too few voters for a vote to mean anything.
    NOT_ENOUGH_PLAYERS = 'not_enough_players'

    #: The starter has to wait a while (they just joined, or a vote
    #: just failed).
    COOLDOWN = 'cooldown'


@dataclass
class HostUIKickVote:
    """A kick vote in progress."""

    #: Who would be kicked.
    target_client_id: int

    #: Their name (as of the vote starting, so it outlives them).
    target_name: str

    #: Who started the vote.
    starter_client_id: int

    #: App-time the vote runs out.
    end_time: float

    #: Votes so far, by client id (True for yes). The starter votes yes.
    votes: dict[int, bool] = field(default_factory=dict)


class HostUIKickVotes:  # pylint: disable=too-many-public-methods
    """The standard kick vote, run by classic hosts.

    Lives at ``app.classic.host_ui.kick_votes``. Clients pick someone in
    their party window and choose to kick them, which opens this vote's
    page. There they can start a vote; everyone else (who can see host
    pages: build 23067 and up) gets a 'Kick X?' notice with the party
    icon and '...' button flashing, and votes on the page the '...' menu
    leads to. Admins (see ``host_ui.admins``) and the host kick without
    a vote and can't be kicked.

    **Customizing.** The methods come in sections, in this order:

    - *The rules* -- every number and decision (vote length, minimum
      voters, votes required, cooldowns, ban time, who's an admin, who
      votes, why a vote can't start).
    - *What people see* -- every bit of text; return your own (plain
      strings are fine) to reword anything.
    - *Running votes* -- the machinery that applies the rules.
    - *The page* -- the vote's doc-ui page.

    Subclass this, copy in just the methods you want to change (those
    in the first two sections use only public api), and assign an
    instance to ``host_ui.kick_votes``; for example, for longer votes::

        class MyKickVotes(baclassic.HostUIKickVotes):
            def get_vote_duration(self) -> float:
                return 60.0

        babase.app.classic.host_ui.kick_votes = MyKickVotes()

    To replace kick votes with something else entirely, turn this off
    (:meth:`set_enabled`, or the server config's
    ``enable_default_kick_voting``) and point
    :meth:`baclassic.HostUISubsystem.set_kick_route` at a page of your
    own.

    The vote's notice uses the single party notice clients have; the
    most recently posted notice wins, so a notice posted during a vote
    replaces the vote's (and the vote's ending replaces whatever is
    showing then).

    Votes starting and ending, and kicks, are logged (``ba.net``, at
    info level); a kick that fails is a warning.
    """

    def __init__(self) -> None:
        self._enabled = True

        #: The vote in progress, if any.
        self.vote: HostUIKickVote | None = None

        # App-times before which clients may not start votes.
        self._start_allowed_times: dict[int, float] = {}

    # ------------------------------------------------------------------
    # The rules.

    def get_vote_duration(self) -> float:
        """How long a vote runs (seconds)."""
        return 30.0

    def get_minimum_clients(self) -> int:
        """Fewest voting clients (not counting the host) for a vote.

        A host that is also playing doesn't count, so require one more
        then (two of three clients in a 2-on-2 shouldn't be able to
        kick the third).
        """
        return 3 if babase.app.env.headless else 4

    def get_votes_required(self, client_count: int) -> int:
        """Yes votes needed to kick, given the voting clients present.

        ``client_count`` doesn't include the host; a host that is also
        playing counts as one more participant (and votes too).
        """
        participants = client_count + (0 if babase.app.env.headless else 1)
        if client_count <= 7:
            # Small parties: a majority of everyone present.
            return participants // 2 + 1
        # Large parties: all but 3 of the clients must agree; kicks
        # should approach unanimity as crowds grow.
        return client_count - 3

    def get_new_client_delay(self) -> float:
        """Seconds a client must have been here to start a vote."""
        return 60.0

    def get_failed_vote_delay(self, starter: bool) -> float:
        """Seconds before someone can start a vote after one fails.

        ``starter`` is whether they started the failed one.
        """
        return 180.0 if starter else 60.0

    def get_ban_time(self) -> int:
        """Seconds a kicked client is kept from rejoining."""
        return 5 * 60

    def get_notice_duration(self) -> float:
        """How long the failed-vote notice shows (seconds)."""
        return 4.0

    def is_admin(self, client_id: int) -> bool:
        """Whether a client is an admin (or the host; client id -1)."""
        if client_id == -1:
            return True
        host_ui = self.get_host_ui()
        account_id = host_ui.get_client_account_id(client_id)
        return account_id is not None and account_id in host_ui.admins

    def get_voters(self) -> list[int]:
        """Who votes: clients that can see host pages, plus a playing host.

        (Clients too old for host pages can't take part at all.)
        """
        host_ui = self.get_host_ui()
        voters = [
            c for c in host_ui.get_client_ids() if host_ui.client_has_host_ui(c)
        ]
        if not babase.app.env.headless:
            voters.append(-1)
        return voters

    def get_voting_client_count(self) -> int:
        """How many voters are clients (that is, not the host)."""
        return len([v for v in self.get_voters() if v != -1])

    def get_refusal(
        self, starter_client_id: int, target_client_id: int
    ) -> KickVoteRefusal | None:
        """Why a client can't start a vote to kick another (None: they can).

        Admins (and the host) skip this; they kick outright.
        """
        # pylint: disable=too-many-return-statements
        if not self._enabled:
            return KickVoteRefusal.DISABLED
        if target_client_id not in self.get_host_ui().get_client_ids():
            return KickVoteRefusal.NOT_PRESENT
        if target_client_id == starter_client_id:
            return KickVoteRefusal.SELF
        if self.is_admin(target_client_id):
            return KickVoteRefusal.ADMIN
        if self.vote is not None:
            return KickVoteRefusal.IN_PROGRESS
        if self.get_voting_client_count() < self.get_minimum_clients():
            return KickVoteRefusal.NOT_ENOUGH_PLAYERS
        if self.get_start_wait(starter_client_id) > 0.0:
            return KickVoteRefusal.COOLDOWN
        return None

    # ------------------------------------------------------------------
    # What people see. (The defaults are the engine's own localized
    # strings; plain strings work too.)

    def get_title_text(self) -> str | babase.LangStr:
        """The vote page's title (also its party-menu button's label)."""
        return _classicassets.strings.party.kick_vote

    def get_question_text(self, name: str) -> str | babase.LangStr:
        """'Kick X?': the voters' notice, and the page's question."""
        return _builtinassets.strings.session.kick_question(name=name)

    def get_started_text(self, name: str) -> str | babase.LangStr:
        """What the starter and the target are told."""
        return _builtinassets.strings.session.kick_vote_started(name=name)

    def get_votes_needed_text(self, count: int) -> str | babase.LangStr:
        """The tally: how many more yes votes are needed."""
        return _builtinassets.strings.session.kick_votes_needed(count=count)

    def get_time_left_text(
        self, ends: datetime.datetime
    ) -> str | babase.LangStr:
        """The countdown under the vote's buttons.

        ``ends`` is when the vote runs out; clients count down to it
        live. (Passing a ``datetime`` to a string's duration param does
        that; see :class:`bacommon.langstr.LangStrSpecTimeTarget`.)
        """
        return _classicassets.strings.host_ui.kick_vote_ends(t=ends)

    def get_yes_text(self) -> str | babase.LangStr:
        """The yes button's label."""
        return _commonassets.strings.actions.yes

    def get_no_text(self) -> str | babase.LangStr:
        """The no button's label."""
        return _commonassets.strings.actions.no

    def get_start_text(self) -> str | babase.LangStr:
        """The button that starts a vote."""
        return _classicassets.strings.host_ui.start_kick_vote

    def get_admin_kick_text(self) -> str | babase.LangStr:
        """The button an admin (or the host) kicks with instead."""
        return _classicassets.strings.ui.kick

    def get_no_vote_text(self) -> str | babase.LangStr:
        """The page when there's no vote and nobody to kick."""
        return _classicassets.strings.host_ui.no_kick_vote

    def get_failed_text(self) -> str | babase.LangStr:
        """The notice everyone gets when a vote fails."""
        return _builtinassets.strings.session.kick_vote_failed

    def get_kicked_text(self, name: str) -> str | babase.LangStr:
        """The screen message everyone gets when someone is kicked."""
        return _builtinassets.strings.session.kick_occurred(name=name)

    def get_refusal_text(
        self, refusal: KickVoteRefusal, starter_client_id: int
    ) -> str | babase.LangStr:
        """Why a vote can't start, as told to whoever tried."""
        # pylint: disable=too-many-return-statements
        strs = _builtinassets.strings.session
        match refusal:
            case KickVoteRefusal.DISABLED:
                return strs.kick_voting_disabled
            case KickVoteRefusal.NOT_PRESENT:
                return _classicassets.strings.host_ui.player_gone
            case KickVoteRefusal.SELF:
                return strs.kick_vote_cant_kick_self
            case KickVoteRefusal.ADMIN:
                return strs.kick_vote_cant_kick_admins
            case KickVoteRefusal.IN_PROGRESS:
                return strs.vote_in_progress
            case KickVoteRefusal.NOT_ENOUGH_PLAYERS:
                return strs.kick_vote_not_enough_players
            case KickVoteRefusal.COOLDOWN:
                return strs.vote_delay(
                    seconds=max(
                        1, round(self.get_start_wait(starter_client_id))
                    )
                )
            case _:
                assert_never(refusal)

    # ------------------------------------------------------------------
    # Running votes.

    def get_host_ui(self) -> HostUISubsystem:
        """The host-ui subsystem we run on (``app.classic.host_ui``)."""
        classic = babase.app.classic
        assert classic is not None
        return classic.host_ui

    @property
    def enabled(self) -> bool:
        """Whether kick voting is on."""
        return self._enabled

    def set_enabled(self, enabled: bool) -> None:
        """Turn kick voting on or off.

        Also offers (or stops offering) this vote's page as where
        clients go to kick someone (see
        :meth:`baclassic.HostUISubsystem.set_kick_route`).
        """
        self._enabled = enabled
        if not enabled and self.vote is not None:
            self.end_vote(passed=False, quiet=True)
        self.get_host_ui().set_kick_route(
            self.get_kick_route if enabled else None
        )

    def get_kick_route(self, client_id: int) -> DocUIRoute:
        """The page clients get when they choose to kick someone."""
        return hroutes.KickVote(client_id=client_id)

    def get_start_wait(self, client_id: int) -> float:
        """Seconds until a client may start a vote (0 if they may now)."""
        allowed = self._start_allowed_times.get(client_id, 0.0)
        return max(0.0, allowed - babase.apptime())

    def start_vote(
        self, starter_client_id: int, target_client_id: int
    ) -> KickVoteRefusal | None:
        """Start a vote (or, for admins, just kick).

        Returns why it couldn't be started, if it couldn't.
        """
        host_ui = self.get_host_ui()
        if self.is_admin(starter_client_id):
            if target_client_id not in host_ui.get_client_ids():
                return KickVoteRefusal.NOT_PRESENT
            if self.is_admin(target_client_id):
                return KickVoteRefusal.ADMIN
            logger.info(
                'Admin client %d kicking client %d (no vote).',
                starter_client_id,
                target_client_id,
            )
            self.kick(target_client_id)
            return None
        refusal = self.get_refusal(starter_client_id, target_client_id)
        if refusal is not None:
            logger.debug(
                'Client %d could not start a kick vote against %d: %s.',
                starter_client_id,
                target_client_id,
                refusal.name,
            )
            return refusal

        name = host_ui.get_client_name(target_client_id) or '?'
        duration = self.get_vote_duration()
        self.vote = HostUIKickVote(
            target_client_id=target_client_id,
            target_name=name,
            starter_client_id=starter_client_id,
            end_time=babase.apptime() + duration,
            votes={starter_client_id: True},
        )
        logger.info(
            'Kick vote started by client %d against client %d (%r);'
            ' %d voting clients, %d yes votes required.',
            starter_client_id,
            target_client_id,
            name,
            self.get_voting_client_count(),
            self.get_votes_required(self.get_voting_client_count()),
        )
        others = [
            c
            for c in self.get_voters()
            if c not in (starter_client_id, target_client_id)
        ]
        told = [starter_client_id, target_client_id]
        host_ui.post_notice(self.get_started_text(name), duration, clients=told)
        host_ui.post_notice(
            self.get_question_text(name), duration, clients=others
        )
        host_ui.flash_party_icon(duration, clients=others)
        host_ui.flash_party_menu(duration, clients=others)
        # (Adds the vote's button to everyone's party menu.)
        host_ui.refresh_clients()
        self.update()
        return None

    def cast_vote(self, client_id: int, yes: bool) -> None:
        """Record a vote (ignored if there's no vote or they voted)."""
        vote = self.vote
        if (
            vote is None
            or client_id in vote.votes
            or client_id == vote.target_client_id
            or client_id not in self.get_voters()
        ):
            logger.debug('Ignoring kick vote from client %d.', client_id)
            return
        vote.votes[client_id] = yes
        host_ui = self.get_host_ui()
        host_ui.flash_party_icon(0.0, clients=[client_id])
        host_ui.flash_party_menu(0.0, clients=[client_id])
        self.update()

    def update(self) -> None:
        """Check the vote in progress: end it if it passed or failed.

        Runs whenever a vote is cast, and every second.
        """
        vote = self.vote
        if vote is None:
            return
        if vote.target_client_id not in self.get_host_ui().get_client_ids():
            # They left; nothing to vote on.
            self.end_vote(passed=False, quiet=True)
            return
        if (
            self.get_voting_client_count() < self.get_minimum_clients()
            or babase.apptime() > vote.end_time
        ):
            self.end_vote(passed=False)
            return
        if self.get_votes_needed() <= 0:
            self.end_vote(passed=True)

    def get_votes_needed(self) -> int:
        """More yes votes the vote in progress needs (0 if none running)."""
        vote = self.vote
        if vote is None:
            return 0
        voters = self.get_voters()
        yes_votes = len(
            [c for c, yes in vote.votes.items() if yes and c in voters]
        )
        return (
            self.get_votes_required(self.get_voting_client_count()) - yes_votes
        )

    def end_vote(self, passed: bool, quiet: bool = False) -> None:
        """End the vote in progress, kicking its target if it passed.

        ``quiet`` ends it without telling anyone how it went (the target
        left, say).
        """
        vote = self.vote
        if vote is None:
            return
        self.vote = None
        yes = len([v for v in vote.votes.values() if v])
        logger.info(
            'Kick vote against client %d (%r) %s (%d yes, %d no).',
            vote.target_client_id,
            vote.target_name,
            'passed' if passed else 'ended' if quiet else 'failed',
            yes,
            len(vote.votes) - yes,
        )
        host_ui = self.get_host_ui()
        everyone = [*self.get_voters(), vote.target_client_id]
        host_ui.flash_party_icon(0.0, clients=everyone)
        host_ui.flash_party_menu(0.0, clients=everyone)
        if passed:
            host_ui.clear_notice(clients=everyone)
            self.kick(vote.target_client_id, name=vote.target_name)
        elif quiet:
            host_ui.clear_notice(clients=everyone)
        else:
            host_ui.post_notice(
                self.get_failed_text(),
                self.get_notice_duration(),
                clients=everyone,
            )
            # Nobody starts another for a while; the starter especially.
            now = babase.apptime()
            for client_id in host_ui.get_client_ids():
                wait = self.get_failed_vote_delay(
                    client_id == vote.starter_client_id
                )
                self._start_allowed_times[client_id] = max(
                    self._start_allowed_times.get(client_id, 0.0), now + wait
                )
        host_ui.refresh_clients()

    def kick(self, client_id: int, name: str | None = None) -> None:
        """Kick a client (banning them for :meth:`get_ban_time`)."""
        if name is None:
            name = self.get_host_ui().get_client_name(client_id) or '?'
        if not bascenev1.disconnect_client(
            client_id, ban_time=self.get_ban_time()
        ):
            logger.warning(
                'Kick of client %d (%r) failed; they may have just left.',
                client_id,
                name,
            )
            return
        logger.info('Kicked client %d (%r).', client_id, name)
        bascenev1.broadcastmessage(
            self.get_kicked_text(name), color=(1.0, 0.5, 0.0)
        )

    def get_buttons(self, client_id: int) -> list[HostUIButton]:
        """Buttons a client gets from us (on top of the host's own).

        While a vote runs, a button to its page in everyone's party
        menu.
        """
        # pylint: disable=cyclic-import
        # (Safe: baclassic imports us, so it's loaded by now.)
        from baclassic import HostUIButton

        del client_id  # Same for everyone.
        if self.vote is None:
            return []
        return [
            HostUIButton(
                label=self.get_title_text(),
                route=hroutes.KickVote(),
                placement='party_menu',
                layout=dui2.WindowLayout.WIDE,
            )
        ]

    def on_client_seen(self, client_id: int) -> None:
        """Note a client arriving (they can't start votes right away).

        :meta private:
        """
        self._start_allowed_times[client_id] = max(
            self._start_allowed_times.get(client_id, 0.0),
            babase.apptime() + self.get_new_client_delay(),
        )

    def on_client_gone(self, client_id: int) -> None:
        """Forget a client that left.

        :meta private:
        """
        self._start_allowed_times.pop(client_id, None)

    # ------------------------------------------------------------------
    # The page.

    def build_page(
        self, client_id: int, target_client_id: int | None
    ) -> dui2.Response:
        """The vote's page, for one client.

        ``target_client_id`` is who they chose to kick, if they came
        here to kick someone. Refreshes itself every second. Its text
        comes from the methods above; the layout is engine machinery,
        so override those rather than this.
        """
        return _build_page(self, client_id, target_client_id, None)

    def handle_start(
        self, client_id: int, target_client_id: int
    ) -> dui2.Response:
        """A client pressed 'Start a Kick Vote'; returns their new page.

        :meta private:
        """
        refusal = self.start_vote(client_id, target_client_id)
        return _build_page(self, client_id, target_client_id, refusal)

    def handle_cast(self, client_id: int, yes: bool) -> dui2.Response:
        """A client voted; returns their new page.

        :meta private:
        """
        self.cast_vote(client_id, yes)
        return _build_page(self, client_id, None, None)


#: Marks the choice a voter made (both buttons grey out once they vote).
_CHECK = '✓ '


def _spec(value: str | babase.LangStr) -> LangStrSpec:
    if isinstance(value, str):
        return LangStrSpecValue.literal(value)
    return dataclass_from_json(LangStrSpec, value.to_resource_json())


def _vote_button(
    label: str | babase.LangStr,
    voted_this: bool,
    action: dui2.Action | None,
) -> dui2.Button:
    """A big square Yes or No (greyed out once there's no voting)."""
    text = _spec(label)
    if voted_this:
        text = LangStrSpecValue(_CHECK + '{l}', {'l': text})
    return dui2.Button(
        label=text,
        action=action,
        size=(220.0, 200.0),
        label_scale=1.5,
        selected=voted_this,
        disabled=action is None,
    )


def _build_page(
    votes: HostUIKickVotes,
    client_id: int,
    target_client_id: int | None,
    refusal: KickVoteRefusal | None,
) -> dui2.Response:
    """Implements HostUIKickVotes.build_page() and friends."""
    vote = votes.vote
    rows: list[dui2.Row] = []

    def _row(
        title: str | babase.LangStr,
        subtitle: str | babase.LangStr | None = None,
        buttons: list[dui2.Button] | None = None,
        padding_top: float | None = None,
        footnote: str | babase.LangStr | None = None,
    ) -> None:
        if not buttons:
            # Just a message; an Ok to go with it (an empty row would
            # get a 'nothing here' placeholder).
            buttons = [
                dui2.Button(
                    label=_spec(_commonassets.strings.actions.ok),
                    action=dui2.Local(close_window=True),
                    size=(200.0, 70.0),
                    style=dui2.ButtonStyle.MEDIUM,
                )
            ]
            if padding_top is None:
                padding_top = 30.0
        rows.append(
            dui2.ButtonRow(
                title=_spec(title),
                subtitle=None if subtitle is None else _spec(subtitle),
                buttons=buttons,
                layout=dui2.ButtonRowLayout.FIXED,
                center_title=True,
                center_content=True,
                button_spacing=40.0,
                padding_top=padding_top,
                # Some air around the tally line.
                spacing_subtitle=0.0 if subtitle is None else 8.0,
                spacing_title=0.0 if subtitle is None else 16.0,
                footnote=None if footnote is None else _spec(footnote),
                # (Time-varying, so one line rather than wrapped.)
                footnote_wrap=False,
                spacing_footnote=0.0 if footnote is None else 20.0,
            )
        )

    refusal_text = (
        None if refusal is None else votes.get_refusal_text(refusal, client_id)
    )
    if vote is not None:
        needed = votes.get_votes_needed_text(max(0, votes.get_votes_needed()))
        time_left = votes.get_time_left_text(
            babase.utc_now_cloud()
            + datetime.timedelta(seconds=vote.end_time - babase.apptime())
        )
        if client_id == vote.target_client_id:
            _row(
                votes.get_started_text(vote.target_name),
                needed,
                footnote=time_left,
            )
        else:
            voted = vote.votes.get(client_id)
            can_vote = voted is None and client_id in votes.get_voters()
            _row(
                votes.get_question_text(vote.target_name),
                refusal_text or needed,
                [
                    _vote_button(
                        votes.get_yes_text(),
                        voted is True,
                        (
                            hroutes.KickVoteCast(yes=True).replace()
                            if can_vote
                            else None
                        ),
                    ),
                    _vote_button(
                        votes.get_no_text(),
                        voted is False,
                        (
                            hroutes.KickVoteCast(yes=False).replace()
                            if can_vote
                            else None
                        ),
                    ),
                ],
                footnote=time_left,
            )
    elif target_client_id is not None:
        name = votes.get_host_ui().get_client_name(target_client_id)
        if name is None:
            _row(votes.get_refusal_text(KickVoteRefusal.NOT_PRESENT, client_id))
        else:
            _row(
                votes.get_question_text(name),
                refusal_text,
                [
                    dui2.Button(
                        label=_spec(
                            votes.get_admin_kick_text()
                            if votes.is_admin(client_id)
                            else votes.get_start_text()
                        ),
                        action=hroutes.KickVoteStart(
                            client_id=target_client_id
                        ).replace(),
                        size=(400.0, 80.0),
                        style=dui2.ButtonStyle.LARGE,
                    )
                ],
                padding_top=30.0,
            )
    else:
        _row(votes.get_no_vote_text(), refusal_text)

    return dui2.Response(
        page=dui2.Page(
            title=_spec(votes.get_title_text()),
            rows=rows,
            center_vertically=True,
        ),
        # Keep it current while it's up.
        timed_action=hroutes.KickVote(client_id=target_client_id).replace(
            default_sound=False
        ),
        timed_action_delay=1.0,
    )
