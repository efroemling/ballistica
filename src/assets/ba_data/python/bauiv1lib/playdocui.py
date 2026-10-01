# Released under the MIT License. See LICENSE for details.
#
"""The top level play window, as a doc-ui page.

A client-local doc-ui domain: one centered row of big buttons leading
to co-op (a legacy window) and the teams/free-for-all playlist browsers
(``bauiv1lib.playlist.browserdocui``).

Also the first step of gather's private-party playlist selection, in
select mode: just the teams and free-for-all buttons, leading to the
playlist browsers' own select mode.
"""

from enum import Enum
from dataclasses import dataclass, replace
from typing import TYPE_CHECKING, Annotated, override, assert_never

from efro.dataclassio import ioprepped, IOAttrs
import bacommon.docui.v2 as dui2
from bacommon.docui.routes import (
    DocUIRoute,
    DocUILocalActionBase,
    PressSound,
    family_members,
)
import bauiv1 as bui
from bauiv1 import _classicassets
from bauiv1lib.docui import TypedDocUIController

if TYPE_CHECKING:
    from typing import Literal

    from bacommon.docui import DocUIResponse
    from bacommon.langstr import LangStrSpec

    from bauiv1lib.docui import DocUILocalAction

#: The buttons' unscaled size.
_BW = 400.0
_BH = 400.0

#: Decoration coords below are the legacy window's, which placed
#: everything from its (400x360) buttons' bottom-left corner; these
#: re-center them on our buttons (hence the ``- _BW/2`` /
#: ``- _LEGACY_BH/2`` offsets), then spread art and labels apart a bit
#: into our taller buttons.
_LEGACY_BH = 360.0
_ART_RAISE = 15.0
_LABEL_DROP = 24.0

#: How far each button's art (characters, computer) is moved down as a
#: whole, after its layout above: the art was placed for 432-tall
#: buttons, and this keeps its margin from the top edge in our shorter
#: ones. (Labels are placed via _LABEL_DROP to sit centered in the
#: space between the art and the button's bottom edge.)
_ART_TUCK = 16.0

#: The legacy labels sat 10 units left of center (calibrated for the
#: old, unevenly-fitting backing graphic); we center them exactly and
#: shift the art right by the same amount so it keeps its place
#: relative to them.
_ART_SHIFT = 10.0

#: Width of the label text boxes, as a fraction of the button's.
_LABEL_WIDTH = 0.85

#: Overall button scale and spacing, sized to just fill the wide
#: layout's page (width and height) without scrolling.
#: (The legacy window's were 0.75/3, but its buttons drew with more
#: transparent margin, so its visible gaps were wider than that spacing
#: suggests.)
_BUTTON_SCALE = 0.655
_BUTTON_SPACING = 25.0

#: How far below center the button row sits (see its spacing).
_ROW_DROP = 20.0

_TITLE_COLOR = (0.7, 0.9, 0.7, 1.0)
_SUBTITLE_COLOR = (0.6, 0.7, 0.6, 1.0)


class Target(Enum):
    """Where the page's buttons lead."""

    COOP = 'coop'
    TEAMS = 'teams'
    FREE_FOR_ALL = 'ffa'


class PlayRoute(DocUIRoute):
    """Family class for the play routes."""

    @override
    @classmethod
    def get_route_types(cls) -> tuple[type[DocUIRoute], ...]:
        return family_members(AnyPlayRoute)

    @override
    @classmethod
    def get_window_layout(cls) -> dui2.WindowLayout:
        return dui2.WindowLayout.WIDE


@ioprepped
@dataclass
class Root(PlayRoute, path='/'):
    """The play page."""

    #: Picking a playlist for private-party hosting instead of playing.
    select: Annotated[bool, IOAttrs('s', store_default=False)] = False


AnyPlayRoute = Root


class PlayLocalAction(DocUILocalActionBase):
    """Family class for the play local-actions."""

    @override
    @classmethod
    def get_action_types(cls) -> tuple[type[DocUILocalActionBase], ...]:
        return family_members(AnyPlayLocalAction)


@ioprepped
@dataclass
class Open(PlayLocalAction, name='open'):
    """Go somewhere."""

    @override
    @classmethod
    def get_press_sound(cls) -> PressSound:
        return PressSound.SWISH

    target: Annotated[Target, IOAttrs('t')]
    select: Annotated[bool, IOAttrs('s', store_default=False)] = False


AnyPlayLocalAction = Open


class PlayController(TypedDocUIController[AnyPlayRoute, AnyPlayLocalAction]):
    """Doc-ui controller for the play page."""

    @override
    @classmethod
    def get_route_type(cls) -> type[PlayRoute]:
        return PlayRoute

    @override
    @classmethod
    def get_local_action_type(cls) -> type[PlayLocalAction]:
        return PlayLocalAction

    @override
    def get_window_toolbar_visibility(
        self,
    ) -> Literal['menu_full', 'menu_minimal']:
        return 'menu_full'

    @override
    def fulfill_route(self, route: AnyPlayRoute) -> DocUIResponse:
        match route:
            case Root():
                _preload_modules()
                return _page(route.select)
            case _:
                assert_never(route)

    @override
    def run_local_action(
        self, action: AnyPlayLocalAction, context: DocUILocalAction
    ) -> None:
        match action:
            case Open():
                _open(action.target, action.select, context)
            case _:
                assert_never(action)


class PlaySelectController(PlayController):
    """The play page as the first step of picking a private-party playlist.

    Open it at a :class:`Root` route with ``select`` set. Its own class
    keeps these windows distinct from the play flow's for navigation,
    and it shows a minimal toolbar (as the legacy select flow did): we're
    mid-errand for the gather window.
    """

    @override
    def get_window_toolbar_visibility(
        self,
    ) -> Literal['menu_full', 'menu_minimal']:
        return 'menu_minimal'


def _preload_modules() -> None:
    """Preload modules our buttons lead to (avoids hitches)."""
    # pylint: disable=cyclic-import
    import bauiv1lib.account as _unused1
    import bauiv1lib.coop.browser as _unused2
    import bauiv1lib.playlist.browserdocui as _unused3


def _page(select: bool) -> dui2.Response:
    """Build the page (called in a background thread)."""
    strs = _classicassets.strings
    buttons: list[dui2.Button] = []
    if not select:
        buttons.append(
            _button(
                Target.COOP,
                strs.play_modes.single_player_coop.spec,
                strs.play.one_to_four_players.spec,
                _coop_decos(),
                select=select,
                selected=True,
            )
        )
    buttons += [
        _button(
            Target.TEAMS,
            strs.play_modes.teams.spec,
            strs.play.two_to_eight_players.spec,
            _teams_decos(),
            select=select,
            selected=select,
        ),
        _button(
            Target.FREE_FOR_ALL,
            strs.play_modes.free_for_all.spec,
            strs.play.two_to_eight_players.spec,
            _ffa_decos(),
            select=select,
        ),
    ]
    return dui2.Response(
        page=dui2.Page(
            title=(
                strs.playlist.playlists.spec if select else strs.ui.play.spec
            ),
            center_vertically=True,
            rows=[
                dui2.ButtonRow(
                    content_align=dui2.HAlign.CENTER,
                    button_spacing=_BUTTON_SPACING,
                    # Every bit of width goes to the buttons.
                    padding_left=0.0,
                    padding_right=0.0,
                    # Enough room for the buttons' art (glow above,
                    # shadow below) so our h-scroll doesn't clip it...
                    padding_top=12.0,
                    padding_bottom=15.0,
                    # ...paid for out of the page's bottom buffer, as
                    # the page height is otherwise spoken for. The row
                    # also sits a bit lower than centered (space added
                    # above and taken from below), which reads better
                    # under the title.
                    spacing_top=_ROW_DROP,
                    spacing_bottom=-7.0 - _ROW_DROP,
                    buttons=buttons,
                )
            ],
        )
    )


def _button(
    target: Target,
    title: LangStrSpec,
    subtitle: LangStrSpec,
    art: list[dui2.Image],
    *,
    select: bool,
    selected: bool = False,
) -> dui2.Button:
    return dui2.Button(
        size=(_BW, _BH),
        scale=_BUTTON_SCALE,
        action=Open(target=target, select=select).local(),
        widget_id=target.value,
        selected=selected,
        decorations=[
            *_scaled(art, 1.0, pivot=(0.0, 0.0), shift=(0.0, -_ART_TUCK)),
            dui2.Text(
                text=title,
                position=(0.0, 120.0 - _LEGACY_BH * 0.5 - _LABEL_DROP),
                size=(_BW * _LABEL_WIDTH, 80.0),
                # Just fits the longest English title (co-op) in that
                # width, so all three draw the same size.
                scale=1.47,
                color=_TITLE_COLOR,
            ),
            dui2.Text(
                text=subtitle,
                # (A bit closer under the title than the legacy 69.)
                position=(0.0, 75.0 - _LEGACY_BH * 0.5 - _LABEL_DROP),
                size=(_BW * _LABEL_WIDTH, 40.0),
                # Grown along with the title.
                scale=1.06,
                flatness=1.0,
                color=_SUBTITLE_COLOR,
            ),
        ],
    )


def _dude(
    i: int, pos: tuple[float, float], color: tuple[float, float, float]
) -> list[dui2.Image]:
    """One little character (body plus eyes), as the legacy window drew.

    ``pos`` is in the legacy window's per-button coords.
    """
    lineup_tex = _classicassets.textures.player_lineup
    eye_color = (
        0.7 + 0.3 * color[0],
        0.7 + 0.3 * color[1],
        0.7 + 0.3 * color[2],
        1.0,
    )
    # Body mesh, body size, eye offset, eye size -- per character.
    match i:
        case 0:
            mesh = _classicassets.meshes.player_lineup1_transparent
            bsize, eoffs, esize = (60.0, 80.0), (12.0, 53.0), (36.0, 18.0)
        case 1:
            mesh = _classicassets.meshes.player_lineup2_transparent
            bsize, eoffs, esize = (45.0, 90.0), (5.0, 67.0), (32.0, 16.0)
        case 2:
            mesh = _classicassets.meshes.player_lineup3_transparent
            bsize, eoffs, esize = (45.0, 90.0), (5.0, 59.0), (34.0, 17.0)
        case 3:
            mesh = _classicassets.meshes.player_lineup4_transparent
            bsize, eoffs, esize = (48.0, 96.0), (2.0, 62.0), (38.0, 19.0)
        case _:
            raise ValueError(f'Invalid dude index {i}.')

    # The legacy window offset every character by (-100, 130).
    x = pos[0] - 100.0 - _BW * 0.5 + _ART_SHIFT
    y = pos[1] + 130.0 - _LEGACY_BH * 0.5 + _ART_RAISE
    return [
        dui2.Image(
            texture=lineup_tex,
            mesh_transparent=mesh,
            position=(x, y),
            size=bsize,
            color=(*color, 1.0),
            h_align=dui2.HAlign.LEFT,
            v_align=dui2.VAlign.BOTTOM,
        ),
        dui2.Image(
            texture=lineup_tex,
            mesh_transparent=_classicassets.meshes.plastic_eyes_transparent,
            position=(x + eoffs[0], y + eoffs[1]),
            size=esize,
            color=eye_color,
            h_align=dui2.HAlign.LEFT,
            v_align=dui2.VAlign.BOTTOM,
        ),
    ]


def _scaled(
    images: list[dui2.Image],
    scale: float,
    pivot: tuple[float, float],
    shift: tuple[float, float],
) -> list[dui2.Image]:
    """Scale a group of images about a pivot, then shift it.

    Positions scale along with sizes, so the group keeps its internal
    proportions (spacing included). Assumes bottom-left-aligned images,
    as ours all are.
    """
    return [
        replace(
            img,
            position=(
                pivot[0] + (img.position[0] - pivot[0]) * scale + shift[0],
                pivot[1] + (img.position[1] - pivot[1]) * scale + shift[1],
            ),
            size=(img.size[0] * scale, img.size[1] * scale),
        )
        for img in images
    ]


def _coop_decos() -> list[dui2.Image]:
    computer = dui2.Image(
        texture=_classicassets.textures.player_lineup,
        mesh_transparent=_classicassets.meshes.angry_computer_transparent,
        position=(
            230.0 - _BW * 0.5 + _ART_SHIFT,
            153.0 - _LEGACY_BH * 0.5 + _ART_RAISE,
        ),
        size=(115.0, 115.0),
        h_align=dui2.HAlign.LEFT,
        v_align=dui2.VAlign.BOTTOM,
    )
    # The computer is grown into the extra space our buttons have over
    # the legacy ones (scaled about its center, then nudged up/right so
    # it sits centered in the green above the label); its box then
    # spans y 1..144, centered at 72.
    #
    # The players are grown the same way, and placed with their group
    # vertically centered on the computer, staggered a bit more than
    # the legacy window's so they fill their side of the button.
    return [
        *_dude_at(0, (-171, -9), (0.72, 0.4, 1.0), 1.2),
        *_dude_at(1, (-117, 32), (0.71, 0.5, 1.0), 1.2),
        *_dude_at(2, (-75, -12), (0.67, 0.44, 1.0), 1.2),
        *_dude_at(3, (-33, 40), (0.7, 0.3, 1.0), 1.2),
        *_scaled([computer], 1.25, pivot=(97.5, 45.5), shift=(14.0, 27.0)),
    ]


def _teams_decos() -> list[dui2.Image]:
    # Two tight huddles side by side, each a zigzag of front/back
    # rows close enough that heights overlap, with a gap between the
    # teams; both centered in the space above the label (the legacy
    # window stacked blue above red, which looked lopsided). Grown
    # like co-op's players. Each team listed left to right, except
    # that its rightmost (back-row) player comes first so it draws
    # behind the one beside it.
    return [
        *_dude_at(0, (-73, 42), (0.3, 0.5, 1.0), 1.2),
        *_dude_at(2, (-175, -4), (0.2, 0.4, 1.0), 1.2),
        *_dude_at(1, (-141, 38), (0.3, 0.5, 1.0), 1.2),
        *_dude_at(3, (-107, 0), (0.3, 0.4, 1.0), 1.2),
        *_dude_at(2, (121, 40), (1.0, 0.5, 0.5), 1.2),
        *_dude_at(0, (7, -6), (1.0, 0.5, 0.4), 1.2),
        *_dude_at(1, (47, 36), (1.0, 0.58, 0.58), 1.2),
        *_dude_at(3, (83, -10), (1.0, 0.5, 0.5), 1.2),
    ]


def _dude_at(
    i: int,
    pos: tuple[float, float],
    color: tuple[float, float, float],
    scale: float,
) -> list[dui2.Image]:
    """A character with its body's bottom-left at ``pos``, scaled.

    Unlike :func:`_dude`, ``pos`` is in our button coords (origin at
    the button's center).
    """
    legacy_pos = (
        pos[0] + 100.0 + _BW * 0.5 - _ART_SHIFT,
        pos[1] - 130.0 + _LEGACY_BH * 0.5 - _ART_RAISE,
    )
    return _scaled(_dude(i, legacy_pos, color), scale, pivot=pos, shift=(0, 0))


def _ffa_decos() -> list[dui2.Image]:
    # A scatter over the space above the label, grown like the other
    # buttons' players: heights staggered so there's no sense of rows,
    # and nobody overlapping. (Started from a randomized
    # max-min-spacing search, then hand-tuned.) Listed left to right.
    return [
        *_dude_at(0, (-164, 66), (0.4, 0.5, 1.0), 1.2),
        *_dude_at(2, (-121, -28), (0.5, 1.0, 0.4), 1.2),
        *_dude_at(1, (-84, 59), (1.0, 0.9, 0.4), 1.2),
        *_dude_at(3, (-35, 3), (0.4, 0.5, 0.8), 1.2),
        *_dude_at(1, (12, -32), (0.7, 0.5, 0.9), 1.2),
        *_dude_at(0, (15, 81), (0.4, 1.0, 0.4), 1.2),
        *_dude_at(3, (71, -17), (1.0, 0.4, 0.5), 1.2),
        *_dude_at(2, (120, 33), (0.7, 1.0, 0.5), 1.2),
    ]


def _open(target: Target, select: bool, context: DocUILocalAction) -> None:
    # pylint: disable=cyclic-import
    window = context.window

    # No-op if we're not in control.
    if not window.main_window_has_control():
        return
    match target:
        case Target.COOP:
            from bauiv1lib.account.signin import show_sign_in_prompt
            from bauiv1lib.coop.browser import CoopBrowserWindow

            plus = bui.app.plus
            assert plus is not None
            if plus.get_v1_account_state() != 'signed_in':
                show_sign_in_prompt(origin_widget=context.widget)
                return
            window.main_window_replace(
                lambda: CoopBrowserWindow(origin_widget=context.widget)
            )
        case Target.TEAMS | Target.FREE_FOR_ALL:
            from bauiv1lib.playlist.browserdocui import (
                PlaylistBrowserController,
                PlaylistSelectController,
                Playlists,
                SessionKind,
                window_layout_for,
            )

            kind = (
                SessionKind.TEAMS
                if target is Target.TEAMS
                else SessionKind.FREE_FOR_ALL
            )
            # WIDE or WIDER, depending on how many playlists it'll show.
            layout = window_layout_for(kind)
            ctrl = (
                PlaylistSelectController
                if select
                else PlaylistBrowserController
            )
            window.main_window_replace(
                lambda: ctrl().create_window(
                    Playlists(kind=kind, select=select),
                    origin_widget=context.widget,
                    auxiliary_style=False,
                    layout=layout,
                ),
                extra_type_id=ctrl.get_window_extra_type_id(),
            )
        case _:
            assert_never(target)
