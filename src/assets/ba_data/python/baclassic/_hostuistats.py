# Released under the MIT License. See LICENSE for details.
#
"""The host-ui stats page (see :class:`HostUIStatsPage`).

To create your own version of this, either:

- **Tweak it:** subclass :class:`HostUIStatsPage`, override just the
  methods you want to change (columns, title, which players, their
  order, cell values), and assign an instance to
  ``babase.app.classic.host_ui.stats_page``. Or
- **Start from it:** copy this whole module into your plugin as the
  starting point for a page of your own, serve it from a route of your
  own (see :class:`baclassic.HostUIHandler`), and point the menu's
  Stats button at it with ``host_ui.set_buttons()`` (or drop the
  button with ``set_buttons([])``).

A copy uses only public api, with two kinds of exception to swap out:

- Imports from ``baclassic._hostui*`` modules: take those names from
  ``baclassic`` instead (``baclassic.host_ui_text`` and friends).
- The engine's own asset wrappers (``bascenev1._classicassets`` and
  co.) supply its localized strings and textures; they're private.
  Use plain strings, or your own asset-package's generated wrapper.

Link to players with ``host_ui.player_page.get_browse()`` so that
whatever player page the host offers is the one your rows open.
"""

from dataclasses import dataclass
from typing import TYPE_CHECKING

import bacommon.depiction as bdep
import bacommon.docui.v2 as dui2
from bacommon.langstr import LangStrSpecValue

import babase
import bascenev1
from bascenev1 import _commonassets, _classicassets

from baclassic._hostuiparts import (
    host_ui_player_icon,
    host_ui_player_name,
    host_ui_text,
)

if TYPE_CHECKING:
    from typing import Callable

    import bacommon.depiction
    import bacommon.docui.v2
    from bacommon.docui.routes import DocUIRoute

    from baclassic._hostui import HostUISubsystem

#: Stats table geometry (a wide page has ~880 units for content).
_ROW_WIDTH = 800.0
_ROW_HEIGHT = 52.0

#: The lone row shown when nobody is here; tall enough to put its
#: message about mid-window.
_EMPTY_ROW_HEIGHT = 300.0

#: Row backings are invisible (a white texture at zero opacity; buttons
#: only honor opacity with a custom texture), so the table reads as
#: lines, not buttons. They're still buttons so controller/keyboard
#: selection has something to move through.
_ROW_COLOR = (1.0, 1.0, 1.0, 0.0)
_ICON_SIZE = 48.0
_ICON_GAP = 8.0
_EDGE_PAD = 16.0
_TITLE_COLOR = (0.7, 0.7, 0.8, 1.0)

#: The player column (icon plus name). Columns pack in from the left,
#: leaving the rest of the row free for more of them.
_PLAYER_WIDTH = 250.0

#: Space between one column's content and the next column.
_COLUMN_GAP = 10.0

# What a stats cell shows (see HostUIStatsColumn.value).
type _CellValue = str | babase.LangStr | bdep.Depiction | None


@dataclass
class HostUIStatsContext:
    """What stats column values may need beyond the player itself.

    Gathered once per page, so columns can look things up cheaply.
    """

    #: Verified account ids by client id (-1 being the host's own), for
    #: those who have one; see
    #: :meth:`~baclassic.HostUISubsystem.get_client_account_id`.
    account_ids: dict[int, str]

    #: The session's stats records (what between-round score screens
    #: show), by their players' ids; see :meth:`record`.
    records: dict[int, bascenev1.PlayerRecord]

    def record(
        self, player: bascenev1.SessionPlayer
    ) -> bascenev1.PlayerRecord | None:
        """A player's stats record, if they have one.

        Records' ``accum*`` values are the current game's (despite the
        name; they reset as each game starts) and are what score screens
        show; the plain ones run for the whole series.
        """
        return self.records.get(id(player))


@dataclass
class HostUIStatsColumn:
    """One column of values in the stats table, right of the player."""

    #: The column's title. A language-string must come from one of the
    #: host's own asset-packages (clients refuse anything else).
    title: str | babase.LangStr

    #: The column's width (the whole table is about 800 wide).
    width: float

    #: A player's value -- text, a language-string (each client shows it
    #: in its own language), a depiction, or None for none (drawn as a
    #: dash). Called on the logic thread for every player each time the
    #: page is built, so keep it cheap.
    value: Callable[
        [bascenev1.SessionPlayer, HostUIStatsContext],
        str | babase.LangStr | bacommon.depiction.Depiction | None,
    ]

    #: Leave the column out when nobody has a value for it (rather than
    #: showing a column of dashes).
    hide_when_empty: bool = False


class HostUIStatsPage:
    """The stats page classic hosts serve: a table of the party.

    One row per player who has joined (icon and name, then a value per
    column), in scoreboard order during games. Serve your own variation
    by subclassing this, overriding :meth:`get_columns` (or anything
    else), and assigning an instance to ``app.classic.host_ui.stats_page``;
    for example, to add a column::

        class MyStatsPage(baclassic.HostUIStatsPage):
            def get_columns(self) -> list[baclassic.HostUIStatsColumn]:
                return super().get_columns() + [
                    baclassic.HostUIStatsColumn(
                        'Streak', 70.0, self.streak_value
                    )
                ]

            def streak_value(self, player, context):
                rec = context.record(player)
                return None if rec is None else str(rec.streak)

        babase.app.classic.host_ui.stats_page = MyStatsPage()

    Subclassing keeps everything you don't override up to date as the
    engine updates. For a page that differs more (a different layout,
    say), copy this module as a starting point instead; see the
    module's notes (``baclassic._hostuistats``) for what a copy needs.
    A table under a route of your own works either way: return
    ``self.build(route)`` from your :class:`baclassic.HostUIHandler`.
    Pages are built on the logic thread; see
    :class:`baclassic.HostUIHandler` for keeping big ones cheap.
    """

    def get_title(self) -> str | babase.LangStr:
        """The page's title."""
        return _classicassets.strings.host_ui.stats_title

    def get_refresh_interval(self) -> float | None:
        """How often (seconds) the page refreshes while open (None: never)."""
        return 10.0

    def get_columns(self) -> list[HostUIStatsColumn]:
        """The table's columns, left to right (after the player's)."""
        return [
            self.account_column(),
            self.score_column(),
            self.kills_column(),
            self.deaths_column(),
            self.ping_column(),
        ]

    # The default columns (for reuse in subclasses' get_columns()).
    # Score, kills and deaths are this game's, as between-round score
    # screens show them; they hide outside games.

    def score_column(self) -> HostUIStatsColumn:
        """The default Score column."""
        return HostUIStatsColumn(
            _classicassets.strings.game.score,
            70.0,
            self.score_value,
            hide_when_empty=True,
        )

    def kills_column(self) -> HostUIStatsColumn:
        """The default Kills column."""
        return HostUIStatsColumn(
            _classicassets.strings.multi_team.kills,
            70.0,
            self.kills_value,
            hide_when_empty=True,
        )

    def deaths_column(self) -> HostUIStatsColumn:
        """The default Deaths column."""
        return HostUIStatsColumn(
            _classicassets.strings.multi_team.deaths,
            80.0,
            self.deaths_value,
            hide_when_empty=True,
        )

    def ping_column(self) -> HostUIStatsColumn:
        """The default Ping column."""
        return HostUIStatsColumn(
            _classicassets.strings.host_ui.ping_column, 80.0, self.ping_value
        )

    def account_column(self) -> HostUIStatsColumn:
        """The default Account column (hidden when nobody has one)."""
        return HostUIStatsColumn(
            _classicassets.strings.host_ui.account_column,
            200.0,
            self.account_value,
            hide_when_empty=True,
        )

    def get_players(
        self, session: bascenev1.Session
    ) -> list[bascenev1.SessionPlayer]:
        """The players to list (before sorting).

        By default everyone who has joined; players still choosing a
        profile in the lobby have no name or look yet.
        """
        return [p for p in session.sessionplayers if p.in_game]

    def sort_players(
        self,
        players: list[bascenev1.SessionPlayer],
        context: HostUIStatsContext,
        session: bascenev1.Session,
    ) -> list[bascenev1.SessionPlayer]:
        """Players in the order to list them.

        By default scoreboard order during a game: grouped by team in
        team games, then by score (highest first), ties going to more
        kills and then fewer deaths, players without stats yet last.
        Outside a game (nobody has stats), join order.
        """
        if not any(context.record(p) is not None for p in players):
            return players
        team_games = isinstance(session, bascenev1.DualTeamSession)
        team_order = {id(t): i for i, t in enumerate(session.sessionteams)}

        def _key(player: bascenev1.SessionPlayer) -> tuple:
            team_index = 0
            if team_games:
                try:
                    team_index = team_order.get(id(player.sessionteam), 0)
                except bascenev1.SessionTeamNotFoundError:
                    pass
            rec = context.record(player)
            if rec is None:
                return (team_index, 1, 0, 0, 0)
            return (
                team_index,
                0,
                -rec.accumscore,
                -rec.accum_kill_count,
                rec.accum_killed_count,
            )

        # (Stable, so equal players keep join order.)
        return sorted(players, key=_key)

    # Column values (usable in subclasses' get_columns() too).

    def score_value(
        self, player: bascenev1.SessionPlayer, context: HostUIStatsContext
    ) -> str | None:
        """A player's score this game (as score screens show it)."""
        rec = context.record(player)
        return None if rec is None else str(rec.accumscore)

    def kills_value(
        self, player: bascenev1.SessionPlayer, context: HostUIStatsContext
    ) -> str | None:
        """A player's kills this game."""
        rec = context.record(player)
        return None if rec is None else str(rec.accum_kill_count)

    def deaths_value(
        self, player: bascenev1.SessionPlayer, context: HostUIStatsContext
    ) -> str | None:
        """A player's deaths this game."""
        rec = context.record(player)
        return None if rec is None else str(rec.accum_killed_count)

    def ping_value(
        self, player: bascenev1.SessionPlayer, context: HostUIStatsContext
    ) -> str | None:
        """A player's connection's ping in ms (as the host measures it)."""
        del context  # Unused.
        client_id = player.inputdevice.client_id
        if client_id == -1:
            return '-'  # The host has no ping to itself.
        ping = bascenev1.get_client_ping(client_id)
        return '?' if ping < 0 else str(round(ping))

    def account_value(
        self, player: bascenev1.SessionPlayer, context: HostUIStatsContext
    ) -> bacommon.depiction.Depiction | None:
        """A player's verified account, as its name depiction.

        Known for the host's own account and for clients that joined
        with v2 auth; so with client auth off, usually None.
        """
        account_id = context.account_ids.get(player.inputdevice.client_id)
        classic = babase.app.classic
        if account_id is None or classic is None:
            return None
        return classic.host_ui.get_account_name_depiction(account_id)

    def build(self, route: DocUIRoute) -> bacommon.docui.v2.Response:
        """Build the page; ``route`` is the one being served.

        (It is what the page refreshes itself with.) Gathers players and
        values through the methods above and lays out the table (see
        the module docs for making a version of your own). Each row
        opens its player's page (see
        :meth:`baclassic.HostUIPlayerPage.get_browse`).
        """
        return _build_page(self, route)


def _build_page(
    page: HostUIStatsPage, route: DocUIRoute
) -> bacommon.docui.v2.Response:
    """Implements HostUIStatsPage.build()."""
    host_ui = _host_ui()
    session = bascenev1.get_foreground_host_session()
    players = [] if session is None else page.get_players(session)
    context = HostUIStatsContext(
        account_ids={
            client_id: account_id
            for client_id in (-1, *host_ui.get_client_ids())
            if (account_id := host_ui.get_client_account_id(client_id))
            is not None
        },
        records=(
            {}
            if session is None
            else {
                id(rec.get_last_sessionplayer()): rec
                for rec in session.stats.get_records().values()
            }
        ),
    )
    if session is not None:
        players = page.sort_players(players, context, session)
    columns = page.get_columns()

    # Work out every value first, so columns nobody has values for can
    # be left out.
    values = [
        [column.value(player, context) for column in columns]
        for player in players
    ]
    shown = [
        i
        for i, column in enumerate(columns)
        if not column.hide_when_empty
        or any(row[i] is not None for row in values)
    ]
    geom = _geometry([columns[i] for i in shown])

    rows: list[dui2.Row] = [
        _player_row(
            player,
            [vals[i] for i in shown],
            geom,
            n == 0,
            host_ui.player_page.get_browse(player.id),
        )
        for n, (player, vals) in enumerate(zip(players, values))
    ]
    if not rows:
        rows.append(_empty_row(geom))

    refresh = page.get_refresh_interval()
    return dui2.Response(
        page=dui2.Page(title=host_ui_text(page.get_title()), rows=rows),
        # Keep it current while it's up.
        timed_action=(
            None if refresh is None else route.replace(default_sound=False)
        ),
        timed_action_delay=0.0 if refresh is None else refresh,
    )


def _host_ui() -> HostUISubsystem:
    classic = babase.app.classic
    assert classic is not None
    return classic.host_ui


def _lit(text: str) -> LangStrSpecValue:
    return LangStrSpecValue.literal(text)


@dataclass
class _Geometry:
    """Where things go in a row (x values relative to its center)."""

    #: Left edge of the player column (where its icon starts).
    player_left: float

    #: Left edge and width of the player's name.
    name_left: float
    name_width: float

    #: The columns shown, with each one's left edge.
    columns: list[tuple[HostUIStatsColumn, float]]


def _geometry(columns: list[HostUIStatsColumn]) -> _Geometry:
    player_left = -_ROW_WIDTH * 0.5 + _EDGE_PAD
    name_left = player_left + _ICON_SIZE + _ICON_GAP
    placed: list[tuple[HostUIStatsColumn, float]] = []
    left = player_left + _PLAYER_WIDTH
    for column in columns:
        placed.append((column, left))
        left += column.width
    return _Geometry(
        player_left=player_left,
        name_left=name_left,
        name_width=player_left + _PLAYER_WIDTH - _COLUMN_GAP - name_left,
        columns=placed,
    )


def _add_header(row: dui2.ButtonRow, geom: _Geometry) -> None:
    """Top the table: the host's app info, then the column titles.

    (The column titles each sit at their column's left edge.)
    """
    row.header_height = 54.0
    titles = [
        (
            host_ui_text(_classicassets.strings.multi_team.player),
            geom.player_left,
            _PLAYER_WIDTH,
        )
    ]
    titles += [
        (host_ui_text(column.title), left, column.width)
        for column, left in geom.columns
    ]
    env = babase.app.env
    decorations: list[dui2.Decoration] = [
        dui2.Text(
            text=_lit(
                f'{babase.appnameupper()} {env.engine_version}'
                f' ({env.engine_build_number})'
            ),
            # (Up past the header's top, about midway to the page title.)
            position=(0, 42),
            size=(_ROW_WIDTH, 20.0),
            scale=0.65,
            color=(1.0, 1.0, 1.0, 0.45),
        )
    ]
    decorations += [
        dui2.Text(
            text=text,
            # (Text anchors at its position, so left-aligned text
            # starts there.)
            position=(left, -12),
            size=(width - _COLUMN_GAP, 24.0),
            scale=0.7,
            h_align=dui2.HAlign.LEFT,
            color=_TITLE_COLOR,
        )
        for text, left, width in titles
    ]
    row.header_decorations_center = decorations


def _player_row(
    player: bascenev1.SessionPlayer,
    values: list[_CellValue],
    geom: _Geometry,
    header: bool,
    browse: dui2.Browse | None,
) -> dui2.ButtonRow:
    """One player: icon, name, then a value per shown column.

    The player's own depictions carry their colors (their team's in team
    games), so they show as they do in the game. Pressing the row does
    ``browse`` (opening the player's page), if given.
    """
    decorations: list[dui2.Decoration] = []

    decorations += host_ui_player_icon(
        player, (geom.player_left + _ICON_SIZE * 0.5, 0.0), _ICON_SIZE
    )
    decorations.append(
        _cell(host_ui_player_name(player), geom.name_left, geom.name_width)
    )

    for (column, left), value in zip(geom.columns, values):
        decorations.append(_cell(value, left, column.width - _COLUMN_GAP))

    row = _table_row(decorations, action=browse)
    if header:
        _add_header(row, geom)
    return row


def _cell(value: _CellValue, left: float, width: float) -> dui2.Decoration:
    """A table cell's decoration: left-aligned in [left, left + width]."""
    if isinstance(value, bdep.Depiction):
        # Depictions fit within a box centered on their position.
        return dui2.Depiction(
            depiction=value,
            position=(left + width * 0.5, 0.0),
            size=(width, 40.0),
            h_align=dui2.HAlign.LEFT,
        )
    # Text anchors at its position instead.
    return dui2.Text(
        text=host_ui_text('-' if value is None else value),
        position=(left, 0.0),
        size=(width, 28.0),
        scale=0.9,
        h_align=dui2.HAlign.LEFT,
        color=(0.85, 0.95, 0.85, 1.0),
    )


def _empty_row(geom: _Geometry) -> dui2.ButtonRow:
    # A tall row, so the message sits mid-window while the header (and
    # the app info in it) stays at the top.
    row = _table_row(
        [
            dui2.Text(
                text=host_ui_text(_classicassets.strings.host_ui.nobody_here),
                position=(0.0, 0.0),
                size=(_ROW_WIDTH - 2.0 * _EDGE_PAD, 30.0),
                color=_TITLE_COLOR,
            )
        ],
        height=_EMPTY_ROW_HEIGHT,
    )
    _add_header(row, geom)
    return row


def _table_row(
    decorations: list[dui2.Decoration],
    height: float = _ROW_HEIGHT,
    action: dui2.Action | None = None,
) -> dui2.ButtonRow:
    """A table row: one invisible full-width button, packed tight.

    Pressing it does ``action`` (or nothing).
    """
    return dui2.ButtonRow(
        center_content=True,
        padding_top=0.0,
        padding_bottom=0.0,
        buttons=[
            dui2.Button(
                label=_lit(''),
                size=(_ROW_WIDTH, height),
                style=dui2.ButtonStyle.SQUARE,
                texture=_commonassets.textures.white,
                color=_ROW_COLOR,
                action=(
                    dui2.Local(default_sound=False)
                    if action is None
                    else action
                ),
                decorations=decorations,
            )
        ],
    )
