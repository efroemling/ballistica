# Released under the MIT License. See LICENSE for details.
#
"""Doc-ui test page for live viewers (the page's viewer pane).

Shows one case at a time in the pane: viewers that should work, empty
panes (and no pane at all), and bad data that should show the
broken-depiction placeholder (an outlined box with a question mark) and
log why, rather than a blank pane. The page's controls switch the case
and the pane's frame style, background and side in place.
"""

from enum import Enum
from dataclasses import dataclass
from typing import TYPE_CHECKING, Annotated, assert_never

from efro.dataclassio import ioprepped, IOAttrs
from bacommon.langstr import LangStrSpecValue
from bacommon.docui.routes import DocUIState
import bacommon.depiction as bdep
import bacommon.docui.v2 as dui2

if TYPE_CHECKING:
    import bacommon.docui.v2
    import bacommon.docui.routes.docuitest


class _Background(Enum):
    """The pane backgrounds the page can show its cases over."""

    DEFAULT = 'default'
    SOLID = 'solid'
    HALF = 'half'
    TINT = 'tint'
    CLEAR = 'clear'


def _background_color(
    background: _Background,
) -> tuple[float, float, float, float] | None:
    match background:
        case _Background.DEFAULT:
            return None
        case _Background.SOLID:
            return (0.1, 0.45, 0.45, 1.0)
        case _Background.HALF:
            return (0.1, 0.45, 0.45, 0.5)
        case _Background.TINT:
            return (0.0, 0.0, 0.0, 0.25)
        case _Background.CLEAR:
            return (0.0, 0.0, 0.0, 0.0)
        case _:
            assert_never(background)


def _background_label(background: _Background) -> LangStrSpecValue:
    match background:
        case _Background.DEFAULT:
            return _lit('Default')
        case _Background.SOLID:
            return _lit('Teal')
        case _Background.HALF:
            return _lit('Teal 50%')
        case _Background.TINT:
            return _lit('Dark 25%')
        case _Background.CLEAR:
            return _lit('Clear')
        case _:
            assert_never(background)


@ioprepped
@dataclass
class ViewersState(DocUIState, state_id='docuitest.viewers'):
    """The viewers page's pane options (switched in place).

    :meta private:
    """

    # Unframed by default: standalone models look best straight over the
    # window.
    frame_style: Annotated[dui2.ViewerFrameStyle, IOAttrs('fs')] = (
        dui2.ViewerFrameStyle.NO_FRAME
    )
    background: Annotated[_Background, IOAttrs('bg')] = _Background.DEFAULT
    side: Annotated[dui2.ViewerSide, IOAttrs('side')] = dui2.ViewerSide.LEFT


class _Case(Enum):
    """The cases the page can show."""

    BLANK = 'blank'
    NO_VIEWER = 'no_viewer'
    BOX = 'box'
    BOX_INDEXED = 'box_indexed'
    SCENE = 'scene'
    UNTEXTURED = 'untextured'
    STILL = 'still'
    DOWNLOADS = 'downloads'
    CHARACTER = 'character'
    LOOK_POWERUP = 'look_powerup'
    LOOK_BOMBS = 'look_bombs'
    LOOK_TINTED = 'look_tinted'
    LOOK_BLENDED = 'look_blended'
    LOOK_TINT_BLEND = 'look_tint_blend'
    LOOK_BACKGROUND = 'look_background'
    LOOK_BOUNDS_SCALE = 'look_bounds_scale'
    LOOK_POSED = 'look_posed'
    LOOK_SET_SHOT = 'look_set_shot'
    LOOK_MOVING_SHOT = 'look_moving_shot'
    LOOK_MOVE_ONCE = 'look_move_once'
    NO_ENTRIES = 'no_entries'
    INDEX_NO_MANIFEST = 'index_no_manifest'
    INDEX_OUT_OF_RANGE = 'index_out_of_range'
    DIGEST_MISMATCH = 'digest_mismatch'
    MISSING_ASSET = 'missing_asset'
    WRONG_KIND = 'wrong_kind'
    MISSING_PACKAGE = 'missing_package'
    BAD_SPAZ = 'bad_spaz'
    UNKNOWN_KIND = 'unknown_kind'


class _Group(Enum):
    """Which section of the page a case's button sits in."""

    EXAMPLES = 'examples'
    LOOKS = 'looks'
    BAD = 'bad'


def _group(case: _Case) -> _Group:
    match case:
        case (
            _Case.BLANK
            | _Case.NO_VIEWER
            | _Case.BOX
            | _Case.BOX_INDEXED
            | _Case.SCENE
            | _Case.UNTEXTURED
            | _Case.STILL
            | _Case.DOWNLOADS
            | _Case.CHARACTER
        ):
            return _Group.EXAMPLES
        case (
            _Case.LOOK_POWERUP
            | _Case.LOOK_BOMBS
            | _Case.LOOK_TINTED
            | _Case.LOOK_BLENDED
            | _Case.LOOK_TINT_BLEND
            | _Case.LOOK_BACKGROUND
            | _Case.LOOK_BOUNDS_SCALE
            | _Case.LOOK_POSED
            | _Case.LOOK_SET_SHOT
            | _Case.LOOK_MOVING_SHOT
            | _Case.LOOK_MOVE_ONCE
        ):
            return _Group.LOOKS
        case (
            _Case.NO_ENTRIES
            | _Case.INDEX_NO_MANIFEST
            | _Case.INDEX_OUT_OF_RANGE
            | _Case.DIGEST_MISMATCH
            | _Case.MISSING_ASSET
            | _Case.WRONG_KIND
            | _Case.MISSING_PACKAGE
            | _Case.BAD_SPAZ
            | _Case.UNKNOWN_KIND
        ):
            return _Group.BAD
        case _:
            assert_never(case)


def _label(case: _Case) -> str:
    """A case's button label (short)."""
    # pylint: disable=too-many-return-statements
    # pylint: disable=too-many-branches
    match case:
        case _Case.BLANK:
            return 'Blank'
        case _Case.NO_VIEWER:
            return 'No Viewer'
        case _Case.BOX:
            return 'Powerup Box'
        case _Case.BOX_INDEXED:
            return 'Box (indexed)'
        case _Case.SCENE:
            return 'Several Meshes'
        case _Case.UNTEXTURED:
            return 'Untextured'
        case _Case.STILL:
            return 'No Spin'
        case _Case.DOWNLOADS:
            return 'Downloads First'
        case _Case.CHARACTER:
            return 'Character'
        case _Case.LOOK_POWERUP:
            return 'Powerup'
        case _Case.LOOK_BOMBS:
            return 'Bombs'
        case _Case.LOOK_TINTED:
            return 'Tinted'
        case _Case.LOOK_BLENDED:
            return 'Blended'
        case _Case.LOOK_TINT_BLEND:
            return 'Tint + Blend'
        case _Case.LOOK_BACKGROUND:
            return 'Background'
        case _Case.LOOK_BOUNDS_SCALE:
            return 'Bounds Scale'
        case _Case.LOOK_POSED:
            return 'Posed'
        case _Case.LOOK_SET_SHOT:
            return 'Set Shot'
        case _Case.LOOK_MOVING_SHOT:
            return 'Moving Shot'
        case _Case.LOOK_MOVE_ONCE:
            return 'Move Once'
        case _Case.NO_ENTRIES:
            return 'No Entries'
        case _Case.INDEX_NO_MANIFEST:
            return 'Index, No Manifest'
        case _Case.INDEX_OUT_OF_RANGE:
            return 'Index Out of Range'
        case _Case.DIGEST_MISMATCH:
            return 'Digest Mismatch'
        case _Case.MISSING_ASSET:
            return 'Missing Asset'
        case _Case.WRONG_KIND:
            return 'Texture as Mesh'
        case _Case.MISSING_PACKAGE:
            return 'Missing Package'
        case _Case.BAD_SPAZ:
            return 'Bad Character'
        case _Case.UNKNOWN_KIND:
            return 'Unknown Kind'
        case _:
            assert_never(case)


def _description(case: _Case) -> str:
    """What a case shows and what to expect."""
    # pylint: disable=too-many-return-statements
    # pylint: disable=too-many-branches
    match case:
        case _Case.BLANK:
            return (
                'An empty pane (a blank depiction): just its background'
                ' (and frame, when framed). Unframed with the default'
                ' background that is nothing at all, though the pane'
                ' keeps its room.'
            )
        case _Case.NO_VIEWER:
            return (
                'A page with no viewer: no pane, and its rows take the'
                " window's whole width (the style and side settings have"
                ' nothing to apply to).'
            )
        case _Case.BOX:
            return 'A powerup box with its punch texture, turning.'
        case _Case.BOX_INDEXED:
            return (
                'The same box, its refs sent as indices into the'
                " depiction's own package manifest."
            )
        case _Case.SCENE:
            return (
                'A bomb, a TNT box and a land mine placed side by side,'
                ' all framed together.'
            )
        case _Case.UNTEXTURED:
            return 'The box with no texture, drawn in a flat color.'
        case _Case.STILL:
            return 'The box with spin off; drag to turn it.'
        case _Case.DOWNLOADS:
            return (
                'The box from a package version this client has not'
                ' registered: the loading spinner shows until it arrives'
                ' (only briefly, or not at all, when its art is already'
                ' cached from another version).'
            )
        case _Case.CHARACTER:
            return (
                'A character viewer, for comparison. Its scene keeps no'
                " transparency, so it covers the pane's background (and"
                ' shows as a plain rectangle unframed).'
            )
        case _Case.LOOK_POWERUP:
            return (
                'A powerup box as the game draws it: its texture plus the'
                ' powerup cube map reflected at 1.0.'
            )
        case _Case.LOOK_BOMBS:
            return (
                'Bombs as the game draws them: regular (sharper cube map,'
                ' 1.8), impact (powerup, 1.5), land mine (powerup, 1.0)'
                ' and TNT (soft, 0.23).'
            )
        case _Case.LOOK_TINTED:
            return (
                "Zoe's head tinted through her color mask (red channel"
                ' blue, green magenta), with a faint character reflection.'
            )
        case _Case.LOOK_BLENDED:
            return (
                'A bomb seen through a translucent, reflective box: the'
                ' box blends, drawn after the solid bomb.'
            )
        case _Case.LOOK_TINT_BLEND:
            return (
                'A tinted part that also asks to blend, which no shading'
                ' does: it draws blended and untinted, and logs a warning'
                ' once.'
            )
        case _Case.LOOK_BACKGROUND:
            return (
                'The in-game powerup box on a background color of its'
                " own (night blue, solid), covering the pane's whatever"
                ' it is.'
            )
        case _Case.LOOK_BOUNDS_SCALE:
            return (
                'The in-game powerup box with a bounds scale of 2: the'
                ' camera frames twice its bounds, so it looks half as big.'
            )
        case _Case.LOOK_POSED:
            return (
                'The bombs held still, turned 35 degrees (view yaw) and'
                ' seen from just 10 degrees above (view pitch). Dragging'
                ' still swings them around.'
            )
        case _Case.LOOK_SET_SHOT:
            return (
                'The bombs through a camera placed by hand: down low'
                ' beside the bomb, looking along the row at the TNT (55'
                ' degree field of view, no auto framing). Spin and'
                ' dragging are off: a completely fixed view.'
            )
        case _Case.LOOK_MOVING_SHOT:
            return (
                'Set Shot with a ping-pong camera: it sways forward and'
                ' to the right past the bomb and back again, over and'
                ' over, still looking at the same point (3 seconds each'
                ' way, eased in and out).'
            )
        case _Case.LOOK_MOVE_ONCE:
            return (
                'Moving Shot with looping off: it eases forward and to'
                ' the right past the bomb once (3 seconds) and stays'
                ' there.'
            )
        case _Case.NO_ENTRIES:
            return 'A mesh viewer with nothing in it.'
        case _Case.INDEX_NO_MANIFEST:
            return 'An indexed mesh ref with no package manifest.'
        case _Case.INDEX_OUT_OF_RANGE:
            return 'An indexed mesh ref past the end of its manifest.'
        case _Case.DIGEST_MISMATCH:
            return "Indexed refs whose manifest digest doesn't match."
        case _Case.MISSING_ASSET:
            return "A mesh name that isn't in its package."
        case _Case.WRONG_KIND:
            return 'A texture given where a mesh belongs.'
        case _Case.MISSING_PACKAGE:
            return "A mesh in a package that doesn't exist."
        case _Case.BAD_SPAZ:
            return 'A character viewer whose definition is garbage.'
        case _Case.UNKNOWN_KIND:
            return 'A depiction kind this client does not know.'
        case _:
            assert_never(case)


# Set Shot's camera (see _look_depiction).
_SET_SHOT_FROM = (-2.2, 0.15, 0.8)
_SET_SHOT_AT = (1.5, 0.0, -0.67)


def _look_depiction(case: _Case) -> bdep.MeshViewerDepiction:
    """A Looks case: game objects drawn as the game draws them.

    Values come from the game's own (``bomb.py``, ``powerupbox.py``,
    the spaz node); cube maps come from the scene wrapper, the only
    one carrying them.
    """
    # pylint: disable=too-many-return-statements
    from bauiv1 import _classicassets, _classiccharacterassets
    from bascenev1 import _classicassets as _sceneassets

    meshes = _classicassets.meshes
    tex = _classicassets.textures
    cubes = _sceneassets.textures
    chars = _classiccharacterassets

    def _zoe(
        part: bacommon.assetspec.MeshSpec,
        position: tuple[float, float, float],
        *,
        transparent: bool = False,
        tint2_color: tuple[float, float, float] = (1.0, 0.8, 0.1),
    ) -> bdep.MeshViewerEntry:
        return bdep.MeshViewerEntry(
            mesh=part,
            texture=chars.textures.zoe_color,
            tint_texture=chars.textures.zoe_color_mask,
            tint_color=(0.2, 0.4, 1.0),
            tint2_color=tint2_color,
            reflection=cubes.reflection_char,
            reflection_scale=(0.1, 0.1, 0.1),
            position=position,
            transparent=transparent,
            color=(1.0, 1.0, 1.0, 0.6 if transparent else 1.0),
        )

    bombs = [
        bdep.MeshViewerEntry(
            mesh=meshes.bomb,
            texture=tex.bomb_color,
            reflection=cubes.reflection_sharper,
            reflection_scale=(1.8, 1.8, 1.8),
            position=(-1.6, 0.0, 0.0),
        ),
        bdep.MeshViewerEntry(
            mesh=meshes.impact_bomb,
            texture=tex.impact_bomb_color,
            reflection=cubes.reflection_powerup,
            reflection_scale=(1.5, 1.5, 1.5),
            position=(-0.5, 0.0, 0.0),
        ),
        bdep.MeshViewerEntry(
            mesh=meshes.land_mine,
            texture=tex.land_mine,
            reflection=cubes.reflection_powerup,
            position=(0.6, -0.3, 0.0),
        ),
        bdep.MeshViewerEntry(
            mesh=meshes.tnt,
            texture=tex.tnt,
            reflection=cubes.reflection_soft,
            reflection_scale=(0.23, 0.23, 0.23),
            position=(1.7, 0.0, 0.0),
        ),
    ]

    match case:
        case _Case.LOOK_POWERUP:
            return bdep.MeshViewerDepiction(
                entries=[
                    bdep.MeshViewerEntry(
                        mesh=meshes.powerup,
                        texture=tex.powerup_punch,
                        reflection=cubes.reflection_powerup,
                    )
                ]
            )
        case _Case.LOOK_BOMBS:
            return bdep.MeshViewerDepiction(entries=bombs)
        case _Case.LOOK_POSED:
            return bdep.MeshViewerDepiction(
                entries=bombs, spin=False, view_yaw=35.0, view_pitch=10.0
            )
        case _Case.LOOK_SET_SHOT:
            # Tucked in low beside the bomb, looking down the row past
            # it toward the TNT box at its far end: aimed about 10
            # degrees left of the box (at the same distance) so the bomb
            # beside us stays in view. The gyro swings us around that
            # point.
            return bdep.MeshViewerDepiction(
                entries=bombs,
                spin=False,
                draggable=False,
                camera=bdep.MeshViewerStillCamera(
                    position=_SET_SHOT_FROM,
                    target=_SET_SHOT_AT,
                    fov_y=55.0,
                ),
            )
        case _Case.LOOK_MOVING_SHOT | _Case.LOOK_MOVE_ONCE:
            # Set Shot's camera, swaying forward and to the right and
            # back, still looking at the same point: 30% of the way
            # toward that point plus 0.7 to the right of the line of
            # sight (past the bomb, staying clear of the impact bomb).
            # Move Once makes the trip just once.
            return bdep.MeshViewerDepiction(
                entries=bombs,
                spin=False,
                draggable=False,
                camera=bdep.MeshViewerPingPongCamera(
                    loop=case is _Case.LOOK_MOVING_SHOT,
                    a=bdep.MeshViewerCameraPose(
                        position=_SET_SHOT_FROM,
                        target=_SET_SHOT_AT,
                        fov_y=55.0,
                    ),
                    b=bdep.MeshViewerCameraPose(
                        position=(-0.83, 0.105, 1.01),
                        target=_SET_SHOT_AT,
                        fov_y=55.0,
                    ),
                    travel_time=3.0,
                ),
            )
        case _Case.LOOK_TINTED:
            return bdep.MeshViewerDepiction(
                # Her hair is the mask's green channel; a loud magenta
                # there makes the tint unmistakable.
                entries=[
                    _zoe(
                        chars.meshes.zoe_head,
                        (0.0, 0.0, 0.0),
                        tint2_color=(1.0, 0.1, 0.9),
                    )
                ]
            )
        case _Case.LOOK_BLENDED:
            return bdep.MeshViewerDepiction(
                entries=[
                    # (Listed first, but drawn last: it blends.)
                    bdep.MeshViewerEntry(
                        mesh=meshes.powerup,
                        texture=tex.powerup_punch,
                        transparent=True,
                        color=(1.0, 1.0, 1.0, 0.35),
                        reflection=cubes.reflection_powerup,
                        scale=(1.6, 1.6, 1.6),
                    ),
                    bdep.MeshViewerEntry(
                        mesh=meshes.bomb,
                        texture=tex.bomb_color,
                        reflection=cubes.reflection_sharper,
                        reflection_scale=(1.8, 1.8, 1.8),
                    ),
                ]
            )
        case _Case.LOOK_BOUNDS_SCALE:
            return bdep.MeshViewerDepiction(
                entries=[
                    bdep.MeshViewerEntry(
                        mesh=meshes.powerup,
                        texture=tex.powerup_punch,
                        reflection=cubes.reflection_powerup,
                    )
                ],
                bounds_scale=2.0,
            )
        case _Case.LOOK_BACKGROUND:
            return bdep.MeshViewerDepiction(
                entries=[
                    bdep.MeshViewerEntry(
                        mesh=meshes.powerup,
                        texture=tex.powerup_punch,
                        reflection=cubes.reflection_powerup,
                    )
                ],
                background_color=(0.08, 0.1, 0.25),
            )
        case _Case.LOOK_TINT_BLEND:
            return bdep.MeshViewerDepiction(
                entries=[
                    _zoe(
                        chars.meshes.zoe_head, (0.0, 0.0, 0.0), transparent=True
                    )
                ]
            )
        case _:
            raise ValueError(f'Not a Looks case: {case}.')


def _depiction(case: _Case) -> bdep.Depiction | None:
    """The depiction a case shows (None for no viewer)."""
    # pylint: disable=too-many-return-statements
    # pylint: disable=too-many-branches
    from bacommon.assetspec import (
        AssetIndexContext,
        MeshSpec,
        TextureSpec,
        wire_digest,
    )
    from bacommon.assetpackage import ApverNum
    from bauiv1 import _classicassets
    from bauiv1lib.docui._resolve import package_asset_listing
    from bascenev1 import _classiccharacterassets

    meshes = _classicassets.meshes
    tex = _classicassets.textures
    box = bdep.MeshViewerEntry(mesh=meshes.powerup, texture=tex.powerup_punch)

    def _indexed(
        *, digest: str | None = None, index: int | None = None
    ) -> bdep.MeshViewerDepiction:
        # As a producer would build it against its vendored listing; we
        # use the client's own.
        packages = [meshes.powerup._apvernum]  # pylint: disable=W0212
        ctx = AssetIndexContext(packages, package_asset_listing)
        return bdep.MeshViewerDepiction(
            entries=[
                bdep.MeshViewerEntry(
                    mesh=(
                        ctx.to_index(meshes.powerup) if index is None else index
                    ),
                    texture=ctx.to_index(tex.powerup_punch),
                )
            ],
            packages=packages,
            domain_digest=(
                wire_digest(ctx.domain_digest()) if digest is None else digest
            ),
        )

    match case:
        case _Case.BLANK:
            return bdep.BlankDepiction()
        case _Case.NO_VIEWER:
            return None
        case _Case.BOX:
            return bdep.MeshViewerDepiction(entries=[box])
        case _Case.BOX_INDEXED:
            return _indexed()
        case _Case.SCENE:
            return bdep.MeshViewerDepiction(
                entries=[
                    bdep.MeshViewerEntry(
                        mesh=meshes.bomb,
                        texture=tex.bomb_color,
                        position=(-1.1, 0.0, 0.0),
                    ),
                    bdep.MeshViewerEntry(
                        mesh=meshes.tnt,
                        texture=tex.tnt,
                        rotation=(0.0, 30.0, 0.0),
                    ),
                    bdep.MeshViewerEntry(
                        mesh=meshes.land_mine,
                        texture=tex.land_mine,
                        position=(1.1, -0.3, 0.0),
                        rotation=(20.0, 0.0, 0.0),
                    ),
                ]
            )
        case _Case.UNTEXTURED:
            return bdep.MeshViewerDepiction(
                entries=[
                    bdep.MeshViewerEntry(
                        mesh=meshes.powerup, color=(0.4, 0.7, 1.0, 1.0)
                    )
                ]
            )
        case _Case.STILL:
            return bdep.MeshViewerDepiction(entries=[box], spin=False)
        case _Case.DOWNLOADS:
            # A test of fetching on demand needs a package the client
            # doesn't already have, so this one deliberately names a
            # superseded baclassicassets version (a-0.baclassicassets
            # .261016, which has the same box) rather than going
            # through the pinned wrapper.
            old = ApverNum(722)
            return bdep.MeshViewerDepiction(
                entries=[
                    bdep.MeshViewerEntry(
                        mesh=MeshSpec(old, 'meshes/powerup'),
                        texture=TextureSpec(old, 'textures/powerup_punch'),
                    )
                ]
            )
        case _Case.CHARACTER:
            return _classiccharacterassets.characters.zoe.get_viewer_depiction()
        case (
            _Case.LOOK_POWERUP
            | _Case.LOOK_BOMBS
            | _Case.LOOK_TINTED
            | _Case.LOOK_BLENDED
            | _Case.LOOK_TINT_BLEND
            | _Case.LOOK_BACKGROUND
            | _Case.LOOK_BOUNDS_SCALE
            | _Case.LOOK_POSED
            | _Case.LOOK_SET_SHOT
            | _Case.LOOK_MOVING_SHOT
            | _Case.LOOK_MOVE_ONCE
        ):
            return _look_depiction(case)
        case _Case.NO_ENTRIES:
            return bdep.MeshViewerDepiction(entries=[])
        case _Case.INDEX_NO_MANIFEST:
            return bdep.MeshViewerDepiction(
                entries=[bdep.MeshViewerEntry(mesh=0)]
            )
        case _Case.INDEX_OUT_OF_RANGE:
            return _indexed(index=999999)
        case _Case.DIGEST_MISMATCH:
            return _indexed(digest='mismatchmismatch')
        case _Case.MISSING_ASSET:
            return bdep.MeshViewerDepiction(
                entries=[
                    bdep.MeshViewerEntry(
                        mesh=MeshSpec(
                            meshes.powerup._apvernum,  # pylint: disable=W0212
                            'meshes/no_such_mesh',
                        )
                    )
                ]
            )
        case _Case.WRONG_KIND:
            return bdep.MeshViewerDepiction(
                entries=[
                    bdep.MeshViewerEntry(
                        mesh=MeshSpec(
                            meshes.powerup._apvernum,  # pylint: disable=W0212
                            'textures/powerup_punch',
                        )
                    )
                ]
            )
        case _Case.MISSING_PACKAGE:
            return bdep.MeshViewerDepiction(
                entries=[
                    bdep.MeshViewerEntry(
                        mesh=MeshSpec(ApverNum(999999999), 'meshes/powerup')
                    )
                ]
            )
        case _Case.BAD_SPAZ:
            return bdep.CharacterViewerDepiction('{"not": [a spaz')
        case _Case.UNKNOWN_KIND:
            return bdep.UnknownDepiction()
        case _:
            assert_never(case)


def _lit(text: str) -> LangStrSpecValue:
    # A dev-only page, so baked literals throughout.
    return LangStrSpecValue.literal(text)


def _frame_style_label(style: dui2.ViewerFrameStyle) -> LangStrSpecValue:
    match style:
        case dui2.ViewerFrameStyle.DEFAULT:
            return _lit('Default')
        case dui2.ViewerFrameStyle.NO_FRAME:
            return _lit('No Frame')
        case _:
            assert_never(style)


def _side_label(side: dui2.ViewerSide) -> LangStrSpecValue:
    match side:
        case dui2.ViewerSide.LEFT:
            return _lit('Left')
        case dui2.ViewerSide.RIGHT:
            return _lit('Right')
        case _:
            assert_never(side)


def _group_section(group: _Group, case: _Case) -> dui2.Section:
    """A group's section of case buttons (each switching in place).

    The page's state (its pane settings) rides along with each.
    """
    # pylint: disable=cyclic-import
    import bacommon.docui.routes.docuitest as rt

    match group:
        case _Group.EXAMPLES:
            title, subtitle = (
                'Examples',
                'An empty pane on purpose, no pane at all, and viewers'
                ' that should just work.',
            )
        case _Group.LOOKS:
            title, subtitle = (
                'Looks',
                'Game objects as the game draws them: cube-map'
                ' reflections, tinting, blending.',
            )
        case _Group.BAD:
            title, subtitle = (
                'Bad Data',
                'Each should show the placeholder, not a blank pane.',
            )
        case _:
            assert_never(group)
    return dui2.Section(
        title=_lit(title),
        subtitle=_lit(subtitle),
        rows=[
            dui2.ButtonRow(
                buttons=[
                    dui2.Button(
                        label=_lit(_label(c)),
                        size=(150, 70),
                        selected=c is case,
                        action=rt.Viewers(case=c.value).replace(),
                    )
                    for c in _Case
                    if _group(c) is group
                ]
            )
        ],
    )


def test_page_viewers(
    route: bacommon.docui.routes.docuitest.Viewers,
) -> bacommon.docui.v2.Response:
    """Live viewer tests."""
    # pylint: disable=cyclic-import
    import bacommon.docui.routes.docuitest as rt

    try:
        case = _Case(route.case)
    except ValueError:
        case = _Case.BOX
    state = route.get_state(ViewersState) or ViewersState()

    # Everything switches in place; the page's state (its pane
    # settings) rides along with every request.
    refresh = rt.Viewers(case=case.value).replace(default_sound=False)

    if case in (_Case.BLANK, _Case.NO_VIEWER):
        # (Their descriptions say what to expect.)
        expect = ''
    else:
        match _group(case):
            case _Group.BAD:
                expect = ' Should show the ? placeholder (and log why).'
            case _Group.EXAMPLES | _Group.LOOKS:
                expect = ' Should show it working.'
            case _:
                assert_never(_group(case))
    return dui2.Response(
        page=dui2.Page(
            title=_lit('Viewers'),
            viewer=_depiction(case),
            viewer_frame_style=state.frame_style,
            viewer_background_color=_background_color(state.background),
            viewer_side=state.side,
            state=state.encode(),
            rows=[
                dui2.Section(
                    subtitle=_lit(
                        f'{_label(case)} - {_description(case)}{expect}'
                    ),
                    rows=[
                        ViewersState.choice_row(
                            lambda s: s.frame_style,
                            choice_label=_frame_style_label,
                            label=_lit('Frame Style'),
                            on_change=refresh,
                        ),
                        ViewersState.choice_row(
                            lambda s: s.background,
                            choice_label=_background_label,
                            label=_lit('Background'),
                            on_change=refresh,
                        ),
                        ViewersState.choice_row(
                            lambda s: s.side,
                            choice_label=_side_label,
                            label=_lit('Pane Side'),
                            on_change=refresh,
                        ),
                    ],
                ),
                *(_group_section(g, case) for g in _Group),
            ],
        )
    )
