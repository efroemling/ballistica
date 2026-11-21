# Released under the MIT License. See LICENSE for details.
#
"""Host-ui pages for one party member or player.

See :class:`HostUIClientPage` and :class:`HostUIPlayerPage`.

To create your own version of these, either:

- **Tweak one:** subclass :class:`HostUIClientPage` or
  :class:`HostUIPlayerPage`, override just the methods you want to
  change, and assign an instance to
  ``babase.app.classic.host_ui.client_page`` (or ``.player_page``). Or
- **Start from one:** copy this module into your plugin as the starting
  point for pages of your own, serve them from routes of your own (see
  :class:`baclassic.HostUIHandler`), and point the host at them with
  ``host_ui.set_client_page()`` (for a player page, assign a
  :class:`HostUIPlayerPage` subclass whose ``get_browse()`` returns
  your route).

A copy uses only public api, with two kinds of exception to swap out:

- Imports from ``baclassic._hostui*`` modules: take those names from
  ``baclassic`` instead (``baclassic.host_ui_text`` and friends).
- The engine's own asset wrappers (``bascenev1._classicassets`` and
  co.) supply its localized strings and textures; they're private.
  Use plain strings, or your own asset-package's generated wrapper.

Link to other pages with ``host_ui.get_client_page()``,
``host_ui.player_page.get_browse()`` and ``host_ui.get_kick_page()``, so that
your links open whatever pages the host offers (yours or the defaults).
"""

from typing import TYPE_CHECKING, assert_never

import bacommon.depiction as bdep
import bacommon.docui.v2 as dui2
import bacommon.docui.routes.classichost as hroutes
from bacommon.docui.presets import section_button
from bacommon.langstr import LangStrSpecValue

import babase
import bascenev1
from bascenev1 import _classicassets, _commonassets

from baclassic._hostuikick import HostUIKickRequest
from baclassic._hostuiparts import (
    host_ui_gone_page,
    host_ui_player_icon,
    host_ui_player_name,
    host_ui_text,
)

if TYPE_CHECKING:
    from typing import Sequence

    import bacommon.depiction
    from bacommon.langstr import LangStrSpec
    from bacommon.docui.routes import DocUIRoute

    from baclassic._hostui import HostUISubsystem

#: Card geometry (a wide page has ~880 units for content).
_CARD_WIDTH = 800.0
_EDGE_PAD = 20.0

#: Invisible card backings (see the stats page's rows).
_CARD_COLOR = (1.0, 1.0, 1.0, 0.0)
_LABEL_COLOR = (0.7, 0.7, 0.8, 1.0)
_VALUE_COLOR = (0.85, 0.95, 0.85, 1.0)
_DIM_COLOR = (1.0, 1.0, 1.0, 0.45)

#: Field rows (label + value) on client pages, and the client's row
#: title style their labels copy (bauiv1lib.docui.prep._rowtext).
_FIELD_HEIGHT = 46.0
_FIELD_GAP = 16.0

#: The engine's usual window color (ContainerWidget's default), for
#: buttons meant to blend in.
_WINDOW_COLOR = (0.4, 0.37, 0.49, 1.0)
_ROW_TITLE_SCALE = 1.15
_ROW_TITLE_COLOR = (0.95, 1.0, 0.97, 1.0)
_ROW_TITLE_FLATNESS = 0.5
_ROW_TITLE_SHADOW = 1.0
_ROW_TITLE_LINE_HEIGHT = 30.0 * _ROW_TITLE_SCALE

#: Player buttons on client pages (three fit across).
_PLAYER_BUTTON_SIZE = (240.0, 64.0)
_PLAYER_ICON_SIZE = 48.0

# A value a page shows: text, a language-string, or a depiction.
type _Value = str | babase.LangStr | bdep.Depiction


def _host_ui() -> HostUISubsystem:
    classic = babase.app.classic
    assert classic is not None
    return classic.host_ui


class HostUIClientPage:
    """The page for one party member: a connected client, or the host.

    Shows their account, connection, and players (each linking to the
    host's player page; see
    :meth:`baclassic.HostUIPlayerPage.get_browse`), plus a way to
    kick them. Party windows (build 23075 and up) open this when a
    member's name is pressed, in the party list or in chat; see
    :meth:`baclassic.HostUISubsystem.set_client_page`.

    Customize it as for :class:`baclassic.HostUIStatsPage`: subclass
    this, override the methods holding the decisions you want to change,
    and assign an instance to ``app.classic.host_ui.client_page`` (or
    copy this module as a starting point; see its notes). Pages are
    built for each viewer (``viewer`` being their client id, -1 for the
    host).
    """

    def get_browse(self, client_id: int) -> bacommon.docui.v2.Browse:
        """How party windows open a member's page (window look included)."""
        return hroutes.Client(client_id=client_id).browse()

    def get_title(self, client_id: int) -> str | babase.LangStr:
        """The page's title: "Host" for the host, else "Client <id>"."""
        if client_id == -1:
            return _classicassets.strings.host_ui.role_host
        return _classicassets.strings.host_ui.client_title(id=str(client_id))

    def get_refresh_interval(self) -> float | None:
        """How often (seconds) the page refreshes while open (None: never)."""
        return 5.0

    def get_players(self, client_id: int) -> list[bascenev1.SessionPlayer]:
        """The member's players to list.

        By default all of them (see
        :meth:`baclassic.HostUISubsystem.get_client_players`).
        """
        return _host_ui().get_client_players(client_id)

    def get_kick_route(self, client_id: int, viewer: int) -> DocUIRoute | None:
        """The page the kick button opens (None: the button is disabled).

        By default the host's kick page for this viewer (see
        :meth:`baclassic.HostUISubsystem.set_kick_page`).
        """
        return _host_ui().get_kick_page(
            HostUIKickRequest(client_id=client_id, viewer=viewer)
        )

    def get_kick_text(
        self, client_id: int, viewer: int
    ) -> str | babase.LangStr:
        """The kick button's label.

        No name: the page it opens (a confirmation or vote) names
        everyone the kick would remove.
        """
        del client_id  # Unused.
        votes = _host_ui().kick_votes
        if votes.enabled and not votes.is_admin(viewer):
            return _classicassets.strings.party.kick_vote
        return _classicassets.strings.ui.kick

    def get_kick_unavailable_text(
        self, client_id: int, viewer: int
    ) -> str | babase.LangStr | None:
        """Why the kick button is disabled, noted under it (None: no note).

        By default the host's reason (see
        :meth:`baclassic.HostUISubsystem.get_kick_unavailable_text`).
        Only shown while :meth:`get_kick_route` returns None.
        """
        return _host_ui().get_kick_unavailable_text(
            HostUIKickRequest(client_id=client_id, viewer=viewer)
        )

    def get_account_action(
        self, client_id: int, account_id: str
    ) -> bacommon.docui.v2.Action | None:
        """What pressing the member's verified account does.

        By default it opens the account's page from the master server
        (see :class:`bacommon.docui.routes.classichost.ShowAccount`;
        clients before its build do nothing). None shows the account
        without a press.
        """
        del client_id  # Unused.
        return hroutes.ShowAccount(account_id=account_id).local()

    def get_role_text(self, client_id: int) -> str | babase.LangStr | None:
        """The member's role row: host, admin or member (None: no row)."""
        if client_id == -1:
            return _classicassets.strings.host_ui.role_host
        if _host_ui().kick_votes.is_admin(client_id):
            return _classicassets.strings.host_ui.role_admin
        return _classicassets.strings.host_ui.role_member

    def build(
        self, route: DocUIRoute, client_id: int, viewer: int
    ) -> bacommon.docui.v2.Response:
        """Build the page on ``client_id`` for ``viewer``.

        ``route`` is the one being served (it is what the page refreshes
        itself with). Gathers everything through the methods above and
        lays it out. Override those to change what the page shows; for a
        different layout, copy this module (see its notes).
        """
        return _build_client_page(self, route, client_id, viewer)


class HostUIPlayerPage:
    """The page for one player in the game.

    Shows who they're playing as, how they're doing this game, and the
    party member they play from (linking to the host's member page; see
    :meth:`baclassic.HostUISubsystem.get_client_page`), plus a way to
    kick them. The stats page's rows and the member page's player
    buttons lead here (see :meth:`get_browse`).

    Customize it as for :class:`baclassic.HostUIStatsPage`: subclass
    this, override the methods holding the decisions you want to change,
    and assign an instance to ``app.classic.host_ui.player_page`` (or
    copy this module as a starting point; see its notes). Pages are
    built for each viewer (``viewer`` being their client id, -1 for the
    host).
    """

    def get_browse(self, player_id: int) -> bacommon.docui.v2.Browse | None:
        """How links to a player open their page (window look included).

        Every link to a player comes through here: the stats page's rows
        and the party member page's player buttons. Override it to send
        them to a page of your own (served by your
        :attr:`baclassic.HostUISubsystem.handler`), or return None for
        no player links.
        """
        return hroutes.Player(player_id=player_id).browse()

    def get_refresh_interval(self) -> float | None:
        """How often (seconds) the page refreshes while open (None: never)."""
        return 5.0

    def get_player(self, player_id: int) -> bascenev1.SessionPlayer | None:
        """The player with a session player id (None if not here)."""
        session = bascenev1.get_foreground_host_session()
        if session is None:
            return None
        for player in session.sessionplayers:
            if player.id == player_id and player.in_game:
                return player
        return None

    def get_stats(
        self, player: bascenev1.SessionPlayer
    ) -> list[tuple[str | babase.LangStr, str]]:
        """Titles and values to show for the player (none outside games).

        By default this game's score, kills and deaths, as between-round
        score screens show them.
        """
        session = bascenev1.get_foreground_host_session()
        if session is None:
            return []
        for rec in session.stats.get_records().values():
            if rec.get_last_sessionplayer() is player:
                return [
                    (_classicassets.strings.game.score, str(rec.accumscore)),
                    (
                        _classicassets.strings.multi_team.kills,
                        str(rec.accum_kill_count),
                    ),
                    (
                        _classicassets.strings.multi_team.deaths,
                        str(rec.accum_killed_count),
                    ),
                ]
        return []

    def get_kick_route(
        self, player: bascenev1.SessionPlayer, viewer: int
    ) -> DocUIRoute | None:
        """The page the kick button opens (None: the button is disabled).

        Kicks remove the player's whole party member (every player on
        their device; the kick page names the others). By default the
        host's kick page for this viewer and player (see
        :meth:`baclassic.HostUISubsystem.set_kick_page`).
        """
        return _host_ui().get_kick_page(
            HostUIKickRequest(
                client_id=player.inputdevice.client_id,
                viewer=viewer,
                player_id=player.id,
            )
        )

    def get_kick_text(
        self, player: bascenev1.SessionPlayer, viewer: int
    ) -> str | babase.LangStr:
        """The kick button's label.

        No name: the page it opens (a confirmation or vote) names
        everyone the kick would remove.
        """
        del player  # Unused.
        votes = _host_ui().kick_votes
        if votes.enabled and not votes.is_admin(viewer):
            return _classicassets.strings.party.kick_vote
        return _classicassets.strings.ui.kick

    def get_kick_unavailable_text(
        self, player: bascenev1.SessionPlayer, viewer: int
    ) -> str | babase.LangStr | None:
        """Why the kick button is disabled, noted under it (None: no note).

        By default the host's reason (see
        :meth:`baclassic.HostUISubsystem.get_kick_unavailable_text`).
        Only shown while :meth:`get_kick_route` returns None.
        """
        return _host_ui().get_kick_unavailable_text(
            HostUIKickRequest(
                client_id=player.inputdevice.client_id,
                viewer=viewer,
                player_id=player.id,
            )
        )

    def build(
        self, route: DocUIRoute, player_id: int, viewer: int
    ) -> bacommon.docui.v2.Response:
        """Build the page on ``player_id`` for ``viewer``.

        ``route`` is the one being served (it is what the page refreshes
        itself with). Gathers everything through the methods above and
        lays it out. Override those to change what the page shows; for a
        different layout, copy this module (see its notes).
        """
        return _build_player_page(self, route, player_id, viewer)


# ----------------------------------------------------------------------
# Layout.


def _build_client_page(
    page: HostUIClientPage, route: DocUIRoute, client_id: int, viewer: int
) -> dui2.Response:
    host_ui = _host_ui()
    if host_ui.get_client_name(client_id) is None:
        return host_ui_gone_page()

    players = page.get_players(client_id)
    # (Always shown; disabled when this viewer can't kick this member.)
    kick_row: dui2.ButtonRow | None = _kick_row(
        page.get_kick_text(client_id, viewer),
        page.get_kick_route(client_id, viewer),
        page.get_kick_unavailable_text(client_id, viewer),
    )
    first: dui2.ButtonRow
    note: tuple[babase.LangStr, babase.LangStr] | None = None
    # With no players, the players heading still shows, with a line
    # saying there are none where the players would be.
    no_players_note = (
        _classicassets.strings.host_ui.players_title,
        _classicassets.strings.host_ui.no_players,
    )
    if players:
        first = dui2.ButtonRow(
            title=host_ui_text(_classicassets.strings.host_ui.players_title),
            buttons=[
                _player_button(p, host_ui.player_page.get_browse(p.id))
                for p in players
            ],
            # (Wrapping, for clients with lots of players; builds
            # predating grids scroll them instead.)
            layout=dui2.ButtonRowLayout.GRID,
            # The buttons are invisible and already pad their icons, so
            # lines can touch (spacing them like the title is from the
            # first line).
            grid_line_spacing=0.0,
        )
    else:
        # No players to list: the kick button is the first (and only)
        # thing to select, and the note goes above it.
        assert kick_row is not None
        note = no_players_note
        first = kick_row
        kick_row = None
    # A verified account gets a row of its own, to press; the member's
    # other fields (and any note) go in a header band atop that first
    # row.
    #
    # TODO: Once builds from TEXT_ROW_BUILD (23075, 1.8.5) on are
    #  ubiquitous, simplify: make each field line a standalone HeaderRow
    #  (attach off) with the account's button row in among them, and let
    #  the page space them by kind, instead of stacking the fields into
    #  one band and choosing which row carries it (with
    #  _ACCOUNT_ROW_PULL to line the two up). Builds before that skip
    #  HeaderRows, and still reach this page through player pages.
    account_row = _account_row(page, client_id)
    _add_fields_band(
        first,
        _client_fields(page, client_id, with_account=account_row is None),
        note,
    )
    rows: list[dui2.Row] = [first]
    if account_row is not None:
        rows.insert(0, account_row)
        # Pull the band up so its first line sits one field line below
        # the account's, as if both were in the band.
        first.spacing_top = _ACCOUNT_ROW_PULL

    if kick_row is not None:
        rows.append(kick_row)
    return _response(page.get_title(client_id), rows, route, page)


#: A labeled value: its label, value, and whether to dim the value.
type _Field = tuple[str | babase.LangStr, _Value, bool]


def _account_row(
    page: HostUIClientPage, client_id: int
) -> dui2.ButtonRow | None:
    """A verified account as a row to press (None if it isn't one).

    Drawn as a field line of the band below (see
    :func:`_add_fields_band`) would be: the account's name as the
    row's one button, at its right edge, and the label in the row's
    zero-height header band, dropped to the button's midline (header
    bands' left point is inset as the band's labels are, so it lines
    up with them).
    """
    host_ui = _host_ui()
    account_id = host_ui.get_client_account_id(client_id)
    if account_id is None:
        return None
    depiction = host_ui.get_account_name_depiction(account_id)
    if depiction is None:
        return None
    action = page.get_account_action(client_id, account_id)
    if action is None:
        return None
    button_height = _ACCOUNT_BUTTON_SIZE[1]
    # (Top padding puts the line's middle where a band's first line's
    # would be.)
    pad_top = _FIELD_HEIGHT * 0.5 - button_height * 0.5
    return dui2.ButtonRow(
        buttons=[
            dui2.Button(
                label=_lit(''),
                depiction=depiction,
                depiction_h_align=dui2.HAlign.RIGHT,
                depiction_hit_area=True,
                size=_ACCOUNT_BUTTON_SIZE,
                action=action,
            )
        ],
        layout=dui2.ButtonRowLayout.FIXED,
        center_content=True,
        # (Slid as far right as it goes: to the row's right edge.)
        content_offset=10000.0,
        padding_top=pad_top,
        padding_bottom=0.0,
        header_height=0.0,
        header_decorations_left=[
            _field_label(
                _classicassets.strings.host_ui.account_column,
                -(pad_top + button_height * 0.5),
            )
        ],
    )


def _field_label(title: str | babase.LangStr, y: float) -> dui2.Text:
    """A field line's label, at a band's left point (``y`` from its midline).

    Styled as row titles are, as the client draws them.
    """
    return dui2.Text(
        text=host_ui_text(title),
        position=(0.0, y),
        size=(_CARD_WIDTH * 0.5 - _EDGE_PAD, 30.0 * _ROW_TITLE_SCALE),
        scale=_ROW_TITLE_SCALE,
        h_align=dui2.HAlign.LEFT,
        color=_ROW_TITLE_COLOR,
        flatness=_ROW_TITLE_FLATNESS,
        shadow=_ROW_TITLE_SHADOW,
    )


def _ping_text(client_id: int) -> str | babase.LangStr:
    """A member's ping as shown on their pages (the host has none)."""
    hstrs = _classicassets.strings.host_ui
    if client_id == -1:
        return hstrs.ping_host
    ping = bascenev1.get_client_ping(client_id)
    return '?' if ping < 0 else hstrs.ping_value(ms=str(round(ping)))


def _client_fields(
    page: HostUIClientPage, client_id: int, *, with_account: bool
) -> list[_Field]:
    """The member's account (``with_account``), ping and role."""
    host_ui = _host_ui()
    hstrs = _classicassets.strings.host_ui
    fields: list[_Field] = []

    if with_account:
        # Only ever a verified account (v2); otherwise say so.
        account_id = host_ui.get_client_account_id(client_id)
        depiction = (
            None
            if account_id is None
            else host_ui.get_account_name_depiction(account_id)
        )
        fields.append(
            (
                hstrs.account_column,
                depiction if depiction is not None else hstrs.not_verified,
                depiction is None,
            )
        )
    fields.append((hstrs.ping_label, _ping_text(client_id), client_id == -1))
    role = page.get_role_text(client_id)
    if role is not None:
        fields.append((hstrs.role_label, role, False))
    return fields


def _add_fields_band(
    row: dui2.ButtonRow,
    fields: list[_Field],
    note: (
        tuple[str | babase.LangStr, str | babase.LangStr | LangStrSpec] | None
    ) = None,
) -> None:
    """Put labeled values in a header band atop ``row``, one per line.

    Labels sit at the band's left decoration point, which is inset as
    row titles are, and are styled as titles; so they line up with
    and match the row's own title. Values sit at its right point. A
    ``note`` (a title and its text) goes below them: the title on a
    line of its own, styled as a row title, and the text centered on
    the next, so it reads like a row with nothing in it.

    (A standalone :class:`~bacommon.docui.v2.HeaderRow` per field
    would be tidier, but builds before ``TEXT_ROW_BUILD`` skip those
    and older clients can reach this page through player pages.)
    """
    width = _CARD_WIDTH * 0.5 - _EDGE_PAD
    # The fields, then a gap between them and the row.
    lines = len(fields) + (0 if note is None else 2)
    if row.title is not None:
        # Space the row's title as one more line: the client centers
        # it this far into its strip (the band's bottom edge).
        gap = (_FIELD_HEIGHT - _ROW_TITLE_LINE_HEIGHT) * 0.5
    else:
        gap = _FIELD_GAP
    height = _FIELD_HEIGHT * lines + gap
    left: list[dui2.Decoration] = []
    right: list[dui2.Decoration] = []
    if note is not None:
        note_title, note_text = note
        title_y = height * 0.5 - _FIELD_HEIGHT * (len(fields) + 0.5)
        left.append(_field_label(note_title, title_y))
        row.header_decorations_center = [
            _text(
                note_text,
                (0.0, title_y - _FIELD_HEIGHT),
                _CARD_WIDTH - 2.0 * _EDGE_PAD,
                color=_LABEL_COLOR,
                h_align=dui2.HAlign.CENTER,
            )
        ]
    for i, (title, value, dim) in enumerate(fields):
        # (Positions are from the band's vertical midline.)
        y = height * 0.5 - _FIELD_HEIGHT * (i + 0.5)
        left.append(_field_label(title, y))
        right.append(
            _value(
                value,
                (0.0, y),
                width,
                h_align=dui2.HAlign.RIGHT,
                color=_DIM_COLOR if dim else _VALUE_COLOR,
            )
        )
    row.header_height = height
    row.header_decorations_left = left
    row.header_decorations_right = right


def _build_player_page(
    page: HostUIPlayerPage, route: DocUIRoute, player_id: int, viewer: int
) -> dui2.Response:
    player = page.get_player(player_id)
    if player is None:
        return host_ui_gone_page()
    rows: list[dui2.Row] = [_player_stats_row(page, player)]
    rows.append(
        _kick_row(
            page.get_kick_text(player, viewer),
            page.get_kick_route(player, viewer),
            page.get_kick_unavailable_text(player, viewer),
        )
    )
    return _response(
        _classicassets.strings.multi_team.player, rows, route, page
    )


#: Player page geometry: the big icon, and the stats row's columns.
_BIG_ICON_SIZE = 128.0
_STAT_COLUMN_WIDTH = 120.0
#: (The name depiction fills its height, so this sizes the name to sit
#: with the row's other values.)
_CONNECTION_BUTTON_SIZE = (260.0, 34.0)

#: A member page's account button (the name depiction fills its height,
#: as depiction field values are drawn).
_ACCOUNT_BUTTON_SIZE = (300.0, 40.0)

#: The account row's pull on the row after it (its ``spacing_top``),
#: so the field lines stay one apart across the two rows. (Measured
#: against the band's own line spacing; -15 left Account and Ping ~8.5
#: units closer than the other lines.)
_ACCOUNT_ROW_PULL = -6.5

#: The footer band holding a disabled kick button's note (why).
_KICK_NOTE_HEIGHT = 34.0


def _player_stats_row(
    page: HostUIPlayerPage, player: bascenev1.SessionPlayer
) -> dui2.ButtonRow:
    """The player's icon and name, then a row of columns.

    Columns are their team (in team games), this game's stats, the
    party member they play from (a button opening its page), and ping.
    It's all one row: the icon, name and column titles go in its header
    band, and the button is its content, carrying the other columns'
    values as decorations so they sit level with it. Everything is
    placed from the row's center, so it holds together at any width.
    """
    client_id = player.inputdevice.client_id

    # Columns before and after the connection button's. (The team, if
    # any, leads; its value is drawn in the team's color.)
    team = _team_of(player)
    team_cols: list[tuple[str | babase.LangStr, str | babase.LangStr]] = (
        []
        if team is None
        else [(_classicassets.strings.host_ui.team_column, team.name)]
    )
    before = [*team_cols, *page.get_stats(player)]
    hstrs = _classicassets.strings.host_ui
    after: list[tuple[str | babase.LangStr, str | babase.LangStr]] = [
        (hstrs.ping_label, _ping_text(client_id))
    ]
    columns: list[tuple[str | babase.LangStr, str | babase.LangStr]] = [
        *before,
        *after,
    ]

    # Column centers.
    button_width = _CONNECTION_BUTTON_SIZE[0]
    left = -(_STAT_COLUMN_WIDTH * len(columns) + button_width) * 0.5
    button_x = left + _STAT_COLUMN_WIDTH * len(before) + button_width * 0.5
    xs = [left + _STAT_COLUMN_WIDTH * (i + 0.5) for i in range(len(before))]
    xs += [
        button_x + button_width * 0.5 + _STAT_COLUMN_WIDTH * (i + 0.5)
        for i in range(len(after))
    ]

    titles = [(title, x) for (title, _value), x in zip(columns, xs)]
    titles.append((hstrs.connection_column, button_x))
    height, heading = _player_heading(player, titles)

    # Values ride the button (not following its highlight), offset
    # from its center to their columns.
    values: list[dui2.Decoration] = []
    for i, ((_title, value), x) in enumerate(zip(columns, xs)):
        if team is not None and i == 0:
            # The team's name, in its color (brightened if dark, as the
            # game does for team-colored text); flat and shadowed to
            # read on the card whatever the color.
            text = _text(
                value,
                (x - button_x, 0.0),
                _STAT_COLUMN_WIDTH - 10.0,
                scale=1.1,
                h_align=dui2.HAlign.CENTER,
                color=(*_rgb(babase.safecolor(_rgb(team.color))), 1.0),
                flatness=1.0,
                shadow=1.0,
            )
        else:
            # (The host's ping is a placeholder, so dim it.)
            dim = client_id == -1 and i == len(columns) - 1
            text = _text(
                value,
                (x - button_x, 0.0),
                _STAT_COLUMN_WIDTH - 10.0,
                scale=1.1,
                h_align=dui2.HAlign.CENTER,
                color=_DIM_COLOR if dim else _VALUE_COLOR,
            )
        text.highlight = False
        values.append(text)

    return dui2.ButtonRow(
        buttons=[_connection_button(client_id, values)],
        layout=dui2.ButtonRowLayout.FIXED,
        center_content=True,
        content_offset=button_x,
        header_height=height,
        header_decorations_center=heading,
    )


def _player_heading(
    player: bascenev1.SessionPlayer,
    titles: list[tuple[str | babase.LangStr, float]],
) -> tuple[float, list[dui2.Decoration]]:
    """The player page's header band: its height and decorations.

    Top down: the big icon, the name, then the columns' titles (each
    at its x).
    """
    name_height = 50.0
    titles_height = 24.0
    # (The name sits close under its icon, with just enough room that a
    # capsule name doesn't touch it, and clear of the values.)
    icon_gap = 12.0
    values_gap = 28.0
    height = (
        _BIG_ICON_SIZE
        + icon_gap
        + name_height
        + values_gap
        + titles_height
        + 2.0
    )
    y = height * 0.5
    decorations = host_ui_player_icon(
        player, (0.0, y - _BIG_ICON_SIZE * 0.5), _BIG_ICON_SIZE
    )
    y -= _BIG_ICON_SIZE + icon_gap
    decorations.append(
        _value(
            host_ui_player_name(player),
            (0.0, y - name_height * 0.5),
            _CARD_WIDTH * 0.6,
            scale=1.5,
            h_align=dui2.HAlign.CENTER,
        )
    )
    y -= name_height
    y -= values_gap
    for title, x in titles:
        decorations.append(
            _text(
                title,
                (x, y - titles_height * 0.5),
                _STAT_COLUMN_WIDTH - 10.0,
                scale=0.7,
                color=_LABEL_COLOR,
                h_align=dui2.HAlign.CENTER,
            )
        )
    return height, decorations


def _connection_button(
    client_id: int,
    decorations: list[dui2.Decoration],
) -> dui2.Button:
    """A button opening the page of the party member a player is on.

    Always a name depiction, as the party window lists the member:
    their account's if we can vouch for it, else their party-list name
    as plain text with no icons (an icon could pass for an account they
    don't own).
    """
    host_ui = _host_ui()
    account_id = host_ui.get_client_account_id(client_id)
    depiction = (
        None
        if account_id is None
        else host_ui.get_account_name_depiction(account_id)
    )
    if depiction is None:
        depiction = bdep.NameDepiction(
            bascenev1.plain_name_json(
                babase.app.lang.remove_custom_unicode_chars(
                    host_ui.get_client_name(client_id) or '?'
                )
            )
        )
    browse = host_ui.get_client_page(client_id)
    return dui2.Button(
        label=_lit(''),
        depiction=depiction,
        depiction_hit_area=True,
        size=_CONNECTION_BUTTON_SIZE,
        action=browse,
        disabled=browse is None,
        decorations=decorations,
    )


def _team_of(player: bascenev1.SessionPlayer) -> bascenev1.SessionTeam | None:
    """A player's team, in team games (None otherwise)."""
    if not isinstance(
        bascenev1.get_foreground_host_session(), bascenev1.DualTeamSession
    ):
        return None
    try:
        return player.sessionteam
    except bascenev1.SessionTeamNotFoundError:
        return None


def _player_button(
    player: bascenev1.SessionPlayer, browse: dui2.Browse | None
) -> dui2.Button:
    width = _PLAYER_BUTTON_SIZE[0]
    left = -width * 0.5 + 10.0
    decorations = host_ui_player_icon(
        player,
        (left + _PLAYER_ICON_SIZE * 0.5, 0.0),
        _PLAYER_ICON_SIZE,
    )
    name_left = left + _PLAYER_ICON_SIZE + 8.0
    decorations.append(
        _value(
            host_ui_player_name(player),
            (name_left, 0.0),
            width * 0.5 - 10.0 - name_left,
        )
    )
    return dui2.Button(
        label=_lit(''),
        size=_PLAYER_BUTTON_SIZE,
        style=dui2.ButtonStyle.SQUARE,
        texture=_commonassets.textures.white,
        color=_CARD_COLOR,
        action=browse,
        decorations=decorations,
    )


def _kick_row(
    label: str | babase.LangStr,
    route: DocUIRoute | None,
    unavailable_text: str | babase.LangStr | None,
) -> dui2.ButtonRow:
    """The kick button's row; disabled (greyed) if there's no route.

    It's always there, so the page keeps its shape whether or not this
    viewer can kick this member. A disabled one gets
    ``unavailable_text`` (why) as a subtle centered note under it.
    """
    # Spans the column, like the full-width section buttons on settings
    # pages (same style and height as bacommon.docui.presets'
    # section_button; a FILL row ignores the width). A disabled one
    # gets a no-op action too: builds predating Button.disabled show it
    # as a normal button.
    button = section_button(
        host_ui_text(label),
        dui2.Local() if route is None else route.browse(),
    )
    button.disabled = route is None
    # (Red, with a light red label, as on the profile editor's Delete
    # Profile button.)
    button.color = (0.7, 0.3, 0.3, 1.0)
    button.label_color = (1.0, 0.7, 0.65, 1.0)
    row = dui2.ButtonRow(
        buttons=[button],
        layout=dui2.ButtonRowLayout.FILL,
        padding_top=30.0,
    )
    if route is None and unavailable_text is not None:
        # (A footer band rather than the row's footnote, which aligns
        # like a title; this one is centered.)
        row.footer_height = _KICK_NOTE_HEIGHT
        row.footer_decorations_center = [
            _text(
                unavailable_text,
                (0.0, 0.0),
                _CARD_WIDTH - 2.0 * _EDGE_PAD,
                scale=0.8,
                color=_DIM_COLOR,
                h_align=dui2.HAlign.CENTER,
            )
        ]
    return row


def _response(
    title: str | babase.LangStr,
    rows: list[dui2.Row],
    route: DocUIRoute,
    page: HostUIClientPage | HostUIPlayerPage,
) -> dui2.Response:
    refresh = page.get_refresh_interval()
    return dui2.Response(
        page=dui2.Page(
            title=host_ui_text(title), rows=rows, center_vertically=True
        ),
        # Keep it current while it's up.
        timed_action=(
            None if refresh is None else route.replace(default_sound=False)
        ),
        timed_action_delay=0.0 if refresh is None else refresh,
    )


def _value(
    value: _Value,
    anchor: tuple[float, float],
    width: float,
    scale: float = 1.0,
    *,
    h_align: dui2.HAlign = dui2.HAlign.LEFT,
    color: tuple[float, float, float, float] = _VALUE_COLOR,
) -> dui2.Decoration:
    """Text or a depiction aligned at ``anchor`` (its left or right end).

    (``color`` applies to text only; depictions bring their own.)
    """
    if isinstance(value, bdep.Depiction):
        # Depictions fit within a box centered on their position.
        match h_align:
            case dui2.HAlign.LEFT:
                offset = width * 0.5
            case dui2.HAlign.CENTER:
                offset = 0.0
            case dui2.HAlign.RIGHT:
                offset = width * -0.5
            case _:
                assert_never(h_align)
        return dui2.Depiction(
            depiction=value,
            position=(anchor[0] + offset, anchor[1]),
            size=(width, 40.0 * scale),
            h_align=h_align,
        )
    return _text(
        value, anchor, width, scale=scale, h_align=h_align, color=color
    )


def _text(
    text: str | babase.LangStr | LangStrSpec,
    position: tuple[float, float],
    width: float,
    *,
    scale: float = 1.0,
    color: tuple[float, float, float, float] = _VALUE_COLOR,
    h_align: dui2.HAlign = dui2.HAlign.LEFT,
    flatness: float | None = None,
    shadow: float | None = None,
) -> dui2.Text:
    # (Text anchors at its position, so left-aligned text starts there.)
    return dui2.Text(
        text=host_ui_text(text),
        position=position,
        size=(width, 30.0 * scale),
        scale=scale,
        h_align=h_align,
        color=color,
        flatness=flatness,
        shadow=shadow,
    )


def _lit(text: str) -> LangStrSpecValue:
    return LangStrSpecValue.literal(text)


def _rgb(color: Sequence[float]) -> tuple[float, float, float]:
    return (float(color[0]), float(color[1]), float(color[2]))
