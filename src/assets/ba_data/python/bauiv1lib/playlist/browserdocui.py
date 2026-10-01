# Released under the MIT License. See LICENSE for details.
#
"""The teams/free-for-all playlist browser, as a doc-ui page.

A client-local doc-ui domain: one long row of playlist buttons (map
previews and all) plus a small customize button, leading to the
play-options popup and the playlist customize browser (both still
legacy).

It also serves gather's private-party hosting in select mode (reached
via the play page's select mode), where confirming a playlist in the
popup just records it and heads back to gather.
"""

import logging
import weakref
from enum import Enum
from dataclasses import dataclass
from typing import TYPE_CHECKING, Annotated, override, assert_never

from efro.dataclassio import ioprepped, IOAttrs
from bacommon.langstr import LangStrSpecValue
import bacommon.docui.v2 as dui2
from bacommon.docui.routes import (
    DocUIRoute,
    DocUILocalActionBase,
    PressSound,
    family_members,
)
import bascenev1 as bs
import bauiv1 as bui
from bauiv1 import _commonassets, _classicassets, _classiccatalogassets
from bauiv1lib.docui import TypedDocUIController

if TYPE_CHECKING:
    from typing import Literal

    from bacommon.docui import DocUIResponse
    from bacommon.assetspec import TextureSpec
    from bacommon.langstr import LangStrSpec

    from bauiv1lib.docui import DocUILocalAction, DocUIWindow
    from bauiv1lib.playlist import PlaylistTypeVars

#: The playlist buttons' unscaled size; decoration coords are relative
#: to its center. Wider than tall: three just fill a WIDE page's width
#: at our scale and spacing (measured: that row is then 867.7 wide of
#: the page's 868.8; any wider and it scrolls sideways).
_BW = 264.0
_BH = 230.0

#: Button width when there are too many playlists for WIDE (so the page
#: opens WIDER and its row scrolls): narrower, to show more at once.
#: Square, at the legacy browser's size.
_BW_MANY = _BH

#: Overall playlist-button scale and spacing. The scale just fills the
#: wider layout's page height (which is the same at every ui-scale)
#: along with the page's title and customize rows, so nothing scrolls
#: vertically. (Measured: at 0.982 the page's content is 342.6 of its
#: 343.6 visible height; recheck if the rows around the buttons change.)
_BUTTON_SCALE = 0.982
_BUTTON_SPACING = 20.0


#: How far the customize row is pulled up toward the playlist buttons
#: and pushed down into the page's bottom buffer (negative row
#: spacings).
_CUSTOMIZE_PULL_UP = -13.0

#: (Only ever frees height for the buttons to grow into -- a bottom
#: spacing doesn't move its own row. Past the page's 20-unit bottom
#: buffer that height is borrowed from the scroll area's edge, and the
#: grown buttons push the customize button into it: at -28 its bottom
#: gets clipped; -24 still clears, shadow and all.)
_CUSTOMIZE_PUSH_DOWN = -24.0

#: Most map previews shown per playlist button.
_MAX_PREVIEWS = 6


class SessionKind(Enum):
    """Which kind of playlists a page shows."""

    TEAMS = 'teams'
    FREE_FOR_ALL = 'ffa'

    def sessiontype(self) -> type[bs.Session]:
        """The session type for this kind."""
        match self:
            case SessionKind.TEAMS:
                return bs.DualTeamSession
            case SessionKind.FREE_FOR_ALL:
                return bs.FreeForAllSession
            case _:
                assert_never(self)


class PlaylistRoute(DocUIRoute):
    """Family class for the playlist browser routes."""

    @override
    @classmethod
    def get_route_types(cls) -> tuple[type[DocUIRoute], ...]:
        return family_members(AnyPlaylistRoute)

    @override
    @classmethod
    def get_window_layout(cls) -> dui2.WindowLayout:
        # (The fallback; openers pick per playlist count via
        # window_layout_for().)
        return dui2.WindowLayout.WIDER


@ioprepped
@dataclass
class Playlists(PlaylistRoute, path='/'):
    """The playlists of one kind."""

    kind: Annotated[SessionKind, IOAttrs('k')]

    #: Picking a playlist for private-party hosting instead of playing.
    select: Annotated[bool, IOAttrs('s', store_default=False)] = False


AnyPlaylistRoute = Playlists


class PlaylistLocalAction(DocUILocalActionBase):
    """Family class for the playlist browser local-actions."""

    @override
    @classmethod
    def get_action_types(cls) -> tuple[type[DocUILocalActionBase], ...]:
        return family_members(AnyPlaylistLocalAction)


@ioprepped
@dataclass
class OpenPlaylist(PlaylistLocalAction, name='open_playlist'):
    """Show a playlist's play options."""

    @override
    @classmethod
    def get_press_sound(cls) -> PressSound:
        return PressSound.SWISH

    kind: Annotated[SessionKind, IOAttrs('k')]
    name: Annotated[str, IOAttrs('n')]
    select: Annotated[bool, IOAttrs('s', store_default=False)] = False


@ioprepped
@dataclass
class Customize(PlaylistLocalAction, name='customize'):
    """Go to the playlist customize browser."""

    @override
    @classmethod
    def get_press_sound(cls) -> PressSound:
        return PressSound.SWISH

    kind: Annotated[SessionKind, IOAttrs('k')]


AnyPlaylistLocalAction = OpenPlaylist | Customize


class PlaylistBrowserController(
    TypedDocUIController[AnyPlaylistRoute, AnyPlaylistLocalAction]
):
    """Doc-ui controller for the playlist browser."""

    @override
    @classmethod
    def get_route_type(cls) -> type[PlaylistRoute]:
        return PlaylistRoute

    @override
    @classmethod
    def get_local_action_type(cls) -> type[PlaylistLocalAction]:
        return PlaylistLocalAction

    @override
    def get_window_toolbar_visibility(
        self,
    ) -> Literal['menu_full', 'menu_minimal']:
        return 'menu_full'

    @override
    def fulfill_route(self, route: AnyPlaylistRoute) -> DocUIResponse:
        match route:
            case Playlists():
                _preload_modules()
                return _page(
                    route.kind, _Contents.gather(route.kind), route.select
                )
            case _:
                assert_never(route)

    @override
    def run_local_action(
        self, action: AnyPlaylistLocalAction, context: DocUILocalAction
    ) -> None:
        match action:
            case OpenPlaylist():
                _open_playlist(action.kind, action.name, action.select, context)
            case Customize():
                _customize(action.kind, context)
            case _:
                assert_never(action)


class PlaylistSelectController(PlaylistBrowserController):
    """The playlist browser for picking a private-party playlist.

    Open it at :class:`Playlists` routes with ``select`` set (the play
    page's select mode does). Its own class keeps these windows distinct
    from the play flow's for navigation, and it shows a minimal toolbar
    (as the legacy select flow did): we're mid-errand for the gather
    window.
    """

    @override
    def get_window_toolbar_visibility(
        self,
    ) -> Literal['menu_full', 'menu_minimal']:
        return 'menu_minimal'


@dataclass
class _Preview:
    """One map preview on a playlist button."""

    texture: TextureSpec
    owned: bool


@dataclass
class _PlaylistInfo:
    """What a playlist button shows."""

    name: str  # Config name ('__default__' for the built-in one).
    label: LangStrSpec
    previews: list[_Preview]


@dataclass
class _Contents:
    """Everything the page shows."""

    playlists: list[_PlaylistInfo]
    selected: str | None

    @classmethod
    def gather(cls, kind: SessionKind) -> _Contents:
        """Gather contents (from a background thread).

        Config, account and map lookups all belong to the logic thread,
        so we hop over there and wait. Done per page build so edits made
        in the customize browser show up on return.
        """
        return bui.logic_thread_submit(
            cls._gather_in_logic_thread, kind
        ).result(timeout=10.0)

    @classmethod
    def _gather_in_logic_thread(cls, kind: SessionKind) -> _Contents:
        # pylint: disable=cyclic-import
        from bauiv1lib.playlist import PlaylistTypeVars

        pvars = PlaylistTypeVars(kind.sessiontype())
        _ensure_standard_playlists_exist()
        names = _stored_playlist_names(pvars)
        stored = bui.app.config.get(pvars.config_name + ' Playlists', {})

        playlists = [
            _PlaylistInfo(
                name='__default__',
                label=pvars.default_list_name.spec,
                previews=_previews(pvars, '__default__', None),
            )
        ]
        for name in names:
            playlists.append(
                _PlaylistInfo(
                    name=name,
                    label=LangStrSpecValue.literal(name),
                    previews=_previews(pvars, name, stored[name]),
                )
            )
        return cls(
            playlists=playlists,
            selected=bui.app.config.get(
                pvars.config_name + ' Playlist Selection'
            ),
        )


#: Most playlists (the default one included) shown in the WIDE layout;
#: more get WIDER, which shows more of them before scrolling.
_WIDE_MAX_PLAYLISTS = 3


def window_layout_for(kind: SessionKind) -> dui2.WindowLayout:
    """The layout to open a browser for ``kind`` playlists at.

    WIDE when its playlists fit it, else WIDER. Call it right before
    opening (logic thread only). The window keeps its layout on back
    navigation, so playlists added in the meantime just scroll.

    Deliberately doesn't create the standard playlists first (the page
    does, as it's built): that queues v1 account transactions which
    only apply locally a cycle later, so doing it here too could send
    them twice. Not needed anyway -- they only get made on new
    installs, bringing a kind to at most 3 playlists, which picks WIDE
    either way.

    :meta private:
    """
    # pylint: disable=cyclic-import
    from bauiv1lib.playlist import PlaylistTypeVars

    pvars = PlaylistTypeVars(kind.sessiontype())
    count = 1 + len(_stored_playlist_names(pvars))  # (+1: default)
    return (
        dui2.WindowLayout.WIDE
        if count <= _WIDE_MAX_PLAYLISTS
        else dui2.WindowLayout.WIDER
    )


def _stored_playlist_names(pvars: PlaylistTypeVars) -> list[str]:
    """A kind's stored (non-default) playlist names, sorted (logic thread)."""
    assert bui.in_logic_thread()
    stored = bui.app.config.get(pvars.config_name + ' Playlists', {})
    return sorted(
        (n.decode() if isinstance(n, bytes) else n for n in stored),
        key=str.lower,
    )


def _ensure_standard_playlists_exist() -> None:
    """Create a few standard playlists on new installations.

    Besides the hard-coded default one; a no-op once done (tracked by
    an account misc-val). Logic thread only.
    """
    plus = bui.app.plus
    assert plus is not None

    # On new installations, go ahead and create a few playlists
    # besides the hard-coded default one:
    if not plus.get_v1_account_misc_val('madeStandardPlaylists', False):
        plus.add_v1_account_transaction(
            {
                'type': 'ADD_PLAYLIST',
                'playlistType': 'Free-for-All',
                'playlistName': (
                    _classicassets.strings.playlist.single_game_name(
                        game=(
                            _classiccatalogassets.strings
                        ).game_names.death_match
                    ).evaluate()
                ),
                'playlist': [
                    {
                        'type': 'bs_death_match.DeathMatchGame',
                        'settings': {
                            'Epic Mode': False,
                            'Kills to Win Per Player': 10,
                            'Respawn Times': 1.0,
                            'Time Limit': 300,
                            'map': 'Doom Shroom',
                        },
                    },
                    {
                        'type': 'bs_death_match.DeathMatchGame',
                        'settings': {
                            'Epic Mode': False,
                            'Kills to Win Per Player': 10,
                            'Respawn Times': 1.0,
                            'Time Limit': 300,
                            'map': 'Crag Castle',
                        },
                    },
                ],
            }
        )
        plus.add_v1_account_transaction(
            {
                'type': 'ADD_PLAYLIST',
                'playlistType': 'Team Tournament',
                'playlistName': (
                    _classicassets.strings.playlist.single_game_name(
                        game=(
                            _classiccatalogassets.strings.game_names
                        ).capture_the_flag
                    ).evaluate()
                ),
                'playlist': [
                    {
                        'type': 'bs_capture_the_flag.CTFGame',
                        'settings': {
                            'map': 'Bridgit',
                            'Score to Win': 3,
                            'Flag Idle Return Time': 30,
                            'Flag Touch Return Time': 0,
                            'Respawn Times': 1.0,
                            'Time Limit': 600,
                            'Epic Mode': False,
                        },
                    },
                    {
                        'type': 'bs_capture_the_flag.CTFGame',
                        'settings': {
                            'map': 'Roundabout',
                            'Score to Win': 2,
                            'Flag Idle Return Time': 30,
                            'Flag Touch Return Time': 0,
                            'Respawn Times': 1.0,
                            'Time Limit': 600,
                            'Epic Mode': False,
                        },
                    },
                    {
                        'type': 'bs_capture_the_flag.CTFGame',
                        'settings': {
                            'map': 'Tip Top',
                            'Score to Win': 2,
                            'Flag Idle Return Time': 30,
                            'Flag Touch Return Time': 3,
                            'Respawn Times': 1.0,
                            'Time Limit': 300,
                            'Epic Mode': False,
                        },
                    },
                ],
            }
        )
        plus.add_v1_account_transaction(
            {
                'type': 'ADD_PLAYLIST',
                'playlistType': 'Team Tournament',
                'playlistName': (
                    _classicassets.strings.playlist.just_sports
                ).evaluate(),
                'playlist': [
                    {
                        'type': 'bs_hockey.HockeyGame',
                        'settings': {
                            'Time Limit': 0,
                            'map': 'Hockey Stadium',
                            'Score to Win': 1,
                            'Respawn Times': 1.0,
                        },
                    },
                    {
                        'type': 'bs_football.FootballTeamGame',
                        'settings': {
                            'Time Limit': 0,
                            'map': 'Football Stadium',
                            'Score to Win': 21,
                            'Respawn Times': 1.0,
                        },
                    },
                ],
            }
        )
        plus.add_v1_account_transaction(
            {
                'type': 'ADD_PLAYLIST',
                'playlistType': 'Free-for-All',
                'playlistName': (
                    _classicassets.strings.playlist.just_epic
                ).evaluate(),
                'playlist': [
                    {
                        'type': 'bs_elimination.EliminationGame',
                        'settings': {
                            'Time Limit': 120,
                            'map': 'Tip Top',
                            'Respawn Times': 1.0,
                            'Lives Per Player': 1,
                            'Epic Mode': 1,
                        },
                    }
                ],
            }
        )
        plus.add_v1_account_transaction(
            {
                'type': 'SET_MISC_VAL',
                'name': 'madeStandardPlaylists',
                'value': True,
            }
        )
        plus.run_v1_account_transactions()


def _previews(
    pvars: PlaylistTypeVars, name: str, playlist: list | None
) -> list[_Preview]:
    """Map previews for a playlist (logic thread)."""
    out: list[_Preview] = []
    try:
        if playlist is None:
            playlist = pvars.get_default_list_call()
        entries = bs.filter_playlist(
            playlist,
            pvars.sessiontype,
            remove_unowned=False,
            mark_unowned=True,
            name=name,
        )
        for entry in entries:
            try:
                maptype = bs.get_map_class(entry['settings']['map'])
            except bui.NotFoundError:
                continue
            spec = maptype.get_preview_texture_spec()
            if spec is None:
                continue
            out.append(
                _Preview(
                    texture=spec,
                    owned=not (
                        entry.get('is_unowned_map', False)
                        or entry.get('is_unowned_game', False)
                    ),
                )
            )
            if len(out) >= _MAX_PREVIEWS:
                break
    except Exception:
        logging.exception('Error listing maps for playlist %r.', name)
    return out


def _preload_modules() -> None:
    """Preload modules our buttons lead to (avoids hitches)."""
    # pylint: disable=cyclic-import
    import bauiv1lib.playoptions as _unused1
    import bauiv1lib.playlist.customizebrowser as _unused2


def _page(
    kind: SessionKind, contents: _Contents, select: bool
) -> dui2.Response:
    """Build the page (called in a background thread).

    Select mode looks just the same; only its buttons behave
    differently.
    """
    from bauiv1lib.playlist import PlaylistTypeVars

    pvars = PlaylistTypeVars(kind.sessiontype())
    rows: list[dui2.Row] = [
        dui2.ButtonRow(
            title=_classicassets.strings.playlist.playlists.spec,
            button_spacing=_BUTTON_SPACING,
            buttons=[
                _playlist_button(
                    kind,
                    info,
                    info.name == contents.selected,
                    select=select,
                    width=(
                        _BW
                        if len(contents.playlists) <= _WIDE_MAX_PLAYLISTS
                        else _BW_MANY
                    ),
                )
                for info in contents.playlists
            ],
        ),
        dui2.ButtonRow(
            # Pulled up to sit about as close under the playlist buttons
            # as their title does above them...
            spacing_top=_CUSTOMIZE_PULL_UP,
            # ...and down into the page's bottom buffer, leaving just
            # enough for its shadow; the playlist buttons get all the
            # height this frees (see _BUTTON_SCALE).
            padding_bottom=0.0,
            spacing_bottom=_CUSTOMIZE_PUSH_DOWN,
            buttons=[
                dui2.Button(
                    label=_commonassets.strings.actions.customize.spec,
                    size=(100, 30),
                    label_scale=0.6,
                    # (Medium is the backing drawn for this aspect;
                    # small is for squarer buttons.)
                    style=dui2.ButtonStyle.MEDIUM,
                    # Muted, so it doesn't stand out from the backing.
                    color=(0.54, 0.52, 0.67, 1.0),
                    label_color=(0.7, 0.65, 0.7, 1.0),
                    action=Customize(kind=kind).local(),
                    widget_id='customize',
                )
            ],
        ),
    ]
    return dui2.Response(
        page=dui2.Page(
            title=pvars.window_title_name.spec,
            center_vertically=True,
            rows=rows,
        )
    )


def _playlist_button(
    kind: SessionKind,
    info: _PlaylistInfo,
    selected: bool,
    *,
    select: bool,
    width: float,
) -> dui2.Button:
    decorations: list[dui2.Decoration] = [
        dui2.Text(
            text=info.label,
            position=(0.0, _BH * 0.79 - _BH * 0.5),
            size=(width * 0.7, 40.0),
            scale=0.69,
        ),
        *_preview_decos(info.previews),
    ]
    if not info.previews:
        decorations.append(
            dui2.Text(
                text=LangStrSpecValue.literal('???'),
                position=(0.0, 0.0),
                size=(width * 0.7, 60.0),
                scale=1.5,
                color=(1.0, 1.0, 1.0, 0.5),
            )
        )
    return dui2.Button(
        size=(width, _BH),
        scale=_BUTTON_SCALE,
        action=OpenPlaylist(kind=kind, name=info.name, select=select).local(),
        selected=selected,
        decorations=decorations,
    )


def _preview_decos(previews: list[_Preview]) -> list[dui2.Decoration]:
    """The map-preview grid on a playlist button.

    The legacy browser's grids (one to six maps) with its per-count
    scales and heights for its 230-tall buttons (which ours match),
    shifted from its bottom-left-corner coords to our centered ones.
    Its horizontal offsets left each grid a few units off center, so
    we center them instead (on any button width).
    """
    count = len(previews)
    # Rows, columns, scale, and the top row's bottom edge in the legacy
    # button's coords.
    if count > 4:
        rows, cols, scl, v_offs = 3, 2, 0.33, 126.0
    elif count > 2:
        rows, cols, scl, v_offs = 2, 2, 0.35, 110.0
    elif count > 1:
        rows, cols, scl, v_offs = 2, 1, 0.5, 105.0
    else:
        rows, cols, scl, v_offs = 1, 1, 0.75, 65.0

    # Previews are 250x125 at scale 1, on a 250x130 pitch.
    h_left = -scl * 250.0 * cols * 0.5
    v_top_row = v_offs - _BH * 0.5

    cmeshes = _classiccatalogassets.meshes
    mask = _classiccatalogassets.textures.map_preview_mask
    out: list[dui2.Decoration] = []
    for row in range(rows):
        for col in range(cols):
            index = row * cols + col
            if index >= count:
                continue
            preview = previews[index]
            h = h_left + scl * 250.0 * col
            v = v_top_row - scl * 130.0 * row
            out.append(
                dui2.Image(
                    texture=preview.texture,
                    position=(h, v),
                    size=(scl * 250.0, scl * 125.0),
                    color=(1.0, 1.0, 1.0, 1.0 if preview.owned else 0.25),
                    mesh_opaque=cmeshes.level_select_button_opaque,
                    mesh_transparent=cmeshes.level_select_button_transparent,
                    mask_texture=mask,
                    h_align=dui2.HAlign.LEFT,
                    v_align=dui2.VAlign.BOTTOM,
                )
            )
            if not preview.owned:
                out.append(
                    dui2.Image(
                        texture=_classicassets.textures.lock,
                        position=(h + scl * 75.0, v + scl * 10.0),
                        size=(scl * 100.0, scl * 100.0),
                        h_align=dui2.HAlign.LEFT,
                        v_align=dui2.VAlign.BOTTOM,
                    )
                )
    return out


class _PlayOptionsDelegate:
    """Moves our window along when the play-options popup is confirmed.

    Launching a game closes it; in select mode it heads back past the
    play page (select mode) it came from, to the gather window.
    """

    def __init__(self, window: DocUIWindow, select: bool) -> None:
        self._window = weakref.ref(window)
        self._select = select

    def on_play_options_window_run_game(self) -> None:
        """Called by the popup as it launches a game (or selects)."""
        window = self._window()
        if window is None or not window.main_window_has_control():
            return
        if self._select:
            # Our back-state recreates the play page; its parent is
            # whatever that page goes back to (gather).
            back_state = window.main_window_back_state
            if back_state is not None and back_state.parent is not None:
                window.main_window_back_state = back_state.parent
            else:
                logging.error('No play page to skip past in playlist select.')
            window.main_window_back()
        else:
            window.main_window_close(transition='out_left')


def _open_playlist(
    kind: SessionKind, name: str, select: bool, context: DocUILocalAction
) -> None:
    # pylint: disable=cyclic-import
    from bauiv1lib.playlist import PlaylistTypeVars
    from bauiv1lib.playoptions import PlayOptionsWindow

    if not context.window.main_window_has_control():
        return

    pvars = PlaylistTypeVars(kind.sessiontype())
    cfg = bui.app.config

    # Make sure the target playlist still exists.
    if name != '__default__' and name not in cfg.get(
        pvars.config_name + ' Playlists', {}
    ):
        return

    # Remember it as the selection (so we come back to it next time).
    # In select mode that's the popup's call; its OK is what selects.
    selkey = pvars.config_name + ' Playlist Selection'
    if not select and cfg.get(selkey) != name:
        cfg[selkey] = name
        cfg.commit()

    PlayOptionsWindow(
        sessiontype=kind.sessiontype(),
        scale_origin=(
            (0.0, 0.0)
            if context.widget is None
            else context.widget.get_screen_space_center()
        ),
        playlist=name,
        delegate=_PlayOptionsDelegate(context.window, select),
        select_only=select,
    )


def _customize(kind: SessionKind, context: DocUILocalAction) -> None:
    # pylint: disable=cyclic-import
    from bauiv1lib.playlist.customizebrowser import (
        PlaylistCustomizeBrowserWindow,
    )

    window = context.window
    if not window.main_window_has_control():
        return
    window.main_window_replace(
        lambda: PlaylistCustomizeBrowserWindow(
            origin_widget=context.widget, sessiontype=kind.sessiontype()
        )
    )
