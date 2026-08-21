# Released under the MIT License. See LICENSE for details.
#
"""Prep functionality for our UI.

We do all layout math and bake out partial ui calls in a background
thread so there's as little work to do in the ui thread as possible.
"""

from functools import partial
from typing import TYPE_CHECKING, assert_never

from efro.dataclassio import dataclass_to_json
import bacommon.docui.v2 as dui2
import bauiv1 as bui
from bauiv1 import builtinassets

from bacommon.docui.framefit import fit_bounds, aligned_box

from bauiv1lib.docui.prep._types import DecorationPrep

if TYPE_CHECKING:
    from typing import Any, Callable

    from bacommon.langstr import LangStrSpec
    from bacommon.assetspec import TextureSpec, MeshSpec
    from bacommon.docui.framefit import Bounds
    from bauiv1lib.docui import DocUIWindow


def _native(lstr: 'LangStrSpec | int', packages: list[str]) -> bui.LangStr:
    """Native handle bound against a payload's package list.

    Accepts the folded index form only to reject it: indices are
    unfolded during resolve (``_resolve.deindex_langstrs``), so one
    reaching render means that step was skipped or failed. Stating the
    assumption here beats every call site assuming it silently.
    """
    if isinstance(lstr, int):
        raise RuntimeError(
            f'Unfolded language-string index {lstr} reached render; the'
            f' page was not resolved, or unfolding failed.'
        )
    return bui.LangStr(dataclass_to_json(lstr), packages=packages)


def _btex(name: str) -> str:
    """Qualified ref for a texture in the builtin asset-package."""
    return f'{builtinassets.__asset_package__}:textures/{name}'


def _refstr(ref: 'TextureSpec | MeshSpec | int') -> str:
    """Qualified engine name for a typed asset ref.

    Delegates so the un-de-indexed-index check lives in exactly one
    place. This was previously typed ``Any``, which meant a widened
    asset-slot type could pass an integer straight through to the
    renderer without mypy noticing -- the sibling in ``_calls`` caught
    it, this one did not.
    """
    from bauiv1lib.docui.prep._calls import refstr

    return refstr(ref)


def prep_decorations(
    decorations: list[dui2.Decoration],
    center_x: float,
    center_y: float,
    scale: float,
    tdelay: float | None,
    *,
    packages: list[str],
    highlight: bool,
    out_decoration_preps: list[DecorationPrep],
) -> None:
    """Prep appropriate decoration types for a list of decorations."""
    for decoration in decorations:
        dectypeid = decoration.get_type_id()
        if dectypeid is dui2.DecorationTypeID.UNKNOWN:
            if bui.do_once():
                bui.uilog.exception(
                    'DocUI receieved unknown decoration;'
                    ' this is likely a server error.'
                )
        elif dectypeid is dui2.DecorationTypeID.TEXT:
            assert isinstance(decoration, dui2.Text)
            prep_text(
                decoration,
                (center_x, center_y),
                scale,
                tdelay,
                out_decoration_preps,
                packages=packages,
                highlight=highlight,
            )

        elif dectypeid is dui2.DecorationTypeID.IMAGE:
            assert isinstance(decoration, dui2.Image)
            prep_image(
                decoration,
                (center_x, center_y),
                scale,
                tdelay,
                out_decoration_preps,
                highlight=highlight,
            )
        elif dectypeid is dui2.DecorationTypeID.DISPLAY_ITEM:
            # This build depicts nothing itself; producers send frames
            # to anything at or past FRAME_DEPICTION_MIN_BUILD, and
            # this build is one. Reaching here means a producer got the
            # audience wrong, so say so rather than drawing nothing
            # silently.
            if bui.do_once():
                bui.uilog.error(
                    'DocUI received a display-item decoration, which'
                    ' this build no longer draws; the producer should'
                    ' have sent a frame.'
                )
        elif dectypeid is dui2.DecorationTypeID.FRAME:
            assert isinstance(decoration, dui2.Frame)
            prep_frame(
                decoration,
                (center_x, center_y),
                scale,
                tdelay,
                out_decoration_preps,
                packages=packages,
                highlight=highlight,
            )
        else:
            assert_never(dectypeid)


def prep_frame(
    frame: dui2.Frame,
    bcenter: tuple[float, float],
    bscale: float,
    tdelay: float | None,
    out_decoration_preps: list[DecorationPrep],
    *,
    packages: list[str],
    highlight: bool,
) -> None:
    """Prep a frame and everything inside it.

    The frame's children are prepped into their own list and wrapped in
    a single self-contained call, so the frame survives prep as one
    thing rather than dissolving into its siblings. That is what lets
    frame-level properties (a group transition, clipping, an eventual
    rotation) have somewhere to live; flattening would silently drop
    them.

    The result is an ordinary :class:`DecorationPrep`, so the doc-ui
    instantiate path runs frames with no special case. Its texture and
    mesh maps are empty because the wrapped call resolves its own
    children's assets.
    """
    # pylint: disable=cyclic-import
    # Safe up-call: _calls only imports us from inside a function, so
    # by the time this runs it is fully imported.
    from bauiv1lib.docui.prep._calls import instantiate_decorations

    # Children are positioned relative to the frame's own origin, so
    # compose the frame's placement onto the incoming transform and let
    # the normal per-decoration prep do the rest.
    # The frame's own space, before any fitting. The size box lives
    # here; only the content moves and shrinks.
    base_scale = bscale * frame.scale
    base_cx = bcenter[0] + frame.position[0] * bscale
    base_cy = bcenter[1] + frame.position[1] * bscale

    cscale = base_scale
    cx = base_cx
    cy = base_cy

    # A sized frame fits its children into its box instead: measure
    # their combined extent, center that, and shrink if needed. Both
    # adjustments fold into the transform above, so the children prep
    # exactly as they otherwise would.
    content = _measure_children(frame, packages, quiet=frame.size is None)
    if frame.size is not None:
        if content is None:
            bui.uilog.error(
                'Sized doc-ui frame has unmeasurable children; drawing'
                ' them unfitted. Sized frames take text and images only.'
            )
        else:
            fit = fit_bounds(content, frame.size, frame.h_align, frame.v_align)
            cscale *= fit.scale
            cx += fit.offset[0] * cscale
            cy += fit.offset[1] * cscale

    if frame.debug:
        _prep_frame_debug(
            frame,
            content,
            base=((base_cx, base_cy), base_scale),
            fitted=((cx, cy), cscale),
            tdelay=tdelay,
            out_decoration_preps=out_decoration_preps,
        )

    child_preps: list[DecorationPrep] = []
    prep_decorations(
        frame.decorations,
        cx,
        cy,
        cscale,
        tdelay,
        packages=packages,
        highlight=highlight and frame.highlight,
        out_decoration_preps=child_preps,
    )

    def _instantiate(
        parent: bui.Widget, draw_controller: bui.Widget | None = None
    ) -> None:
        instantiate_decorations(
            child_preps, parent=parent, draw_controller=draw_controller
        )

    out_decoration_preps.append(
        DecorationPrep(
            call=_instantiate,
            textures={},
            meshes={},
            highlight=frame.highlight,
        )
    )


def _measure_children(
    frame: dui2.Frame, packages: list[str], quiet: bool
) -> Bounds | None:
    """Return the combined extent of a frame's children, or None.

    None means some child's size cannot be known before drawing, which
    is a contract violation for a sized frame but merely uninteresting
    for an unsized one -- hence ``quiet``.
    """
    out: Bounds | None = None
    for child in frame.decorations:
        bounds = _child_bounds(child, packages)
        if bounds is None:
            if not quiet:
                bui.uilog.error(
                    'Sized doc-ui frame contains a %s, which cannot be'
                    ' measured.',
                    type(child).__name__,
                )
            return None
        out = bounds if out is None else out.union(bounds)
    return out


def _child_bounds(child: dui2.Decoration, packages: list[str]) -> Bounds | None:
    """Return a child's extent in frame-local units.

    None means "not measurable" -- a nested frame or display-item,
    whose own contents would have to be resolved first.
    """
    dectypeid = child.get_type_id()

    if dectypeid is dui2.DecorationTypeID.IMAGE:
        assert isinstance(child, dui2.Image)
        return aligned_box(
            child.position,
            child.size[0],
            child.size[1],
            child.h_align,
            child.v_align,
        )

    if dectypeid is dui2.DecorationTypeID.TEXT:
        assert isinstance(child, dui2.Text)
        # Rendered extent is the string's measured size times the
        # text's own scale; the frame transform supplies the rest.
        text = _native(child.text, packages).evaluate()
        return aligned_box(
            child.position,
            bui.get_string_width(text, suppress_warning=True) * child.scale,
            bui.get_string_height(text, suppress_warning=True) * child.scale,
            child.h_align,
            child.v_align,
        )

    return None


def _prep_frame_debug(
    frame: dui2.Frame,
    content: Bounds | None,
    *,
    base: tuple[tuple[float, float], float],
    fitted: tuple[tuple[float, float], float],
    tdelay: float | None,
    out_decoration_preps: list[DecorationPrep],
) -> None:
    """Draw a frame's size box and the extent its children occupy.

    Two rects rather than one, and in two different spaces: the box is
    where content was asked to go, drawn in the frame's own space, and
    the extent is where it ended up, drawn in the fitted space. Content
    that overflows its box or sits off-center in it therefore looks
    wrong here rather than having to be inferred.
    """
    base_center, base_scale = base
    fit_center, fit_scale = fitted

    if frame.size is not None:
        out_decoration_preps.append(
            _debug_rect(
                (
                    base_center[0] - frame.size[0] * 0.5 * base_scale,
                    base_center[1] - frame.size[1] * 0.5 * base_scale,
                ),
                (
                    frame.size[0] * base_scale,
                    frame.size[1] * base_scale,
                ),
                (0, 1, 1),
                0.25,
                tdelay,
            )
        )

    if content is not None:
        out_decoration_preps.append(
            _debug_rect(
                (
                    fit_center[0] + content.minx * fit_scale,
                    fit_center[1] + content.miny * fit_scale,
                ),
                (
                    content.width * fit_scale,
                    content.height * fit_scale,
                ),
                (1, 0, 1),
                0.25,
                tdelay,
            )
        )


def _debug_rect(
    position: tuple[float, float],
    size: tuple[float, float],
    color: tuple[float, float, float],
    opacity: float,
    tdelay: float | None,
) -> DecorationPrep:
    """A flat translucent rect, for showing bounds during development."""
    return DecorationPrep(
        call=partial(
            bui.imagewidget,
            position=position,
            size=size,
            color=color,
            opacity=opacity,
            transition_delay=tdelay,
            transition_type='scale',
        ),
        textures={'texture': _btex('white')},
        meshes={},
        highlight=True,
    )


def prep_text(
    text: dui2.Text,
    bcenter: tuple[float, float],
    bscale: float,
    tdelay: float | None,
    out_decoration_preps: list[DecorationPrep],
    *,
    packages: list[str],
    highlight: bool,
) -> None:
    """Prep decorations for text."""
    # pylint: disable=too-many-branches
    xoffs = bcenter[0] + text.position[0] * bscale
    yoffs = bcenter[1] + text.position[1] * bscale

    if text.h_align is dui2.HAlign.LEFT:
        h_align = 'left'
    elif text.h_align is dui2.HAlign.CENTER:
        h_align = 'center'
    elif text.h_align is dui2.HAlign.RIGHT:
        h_align = 'right'
    else:
        assert_never(text.h_align)

    if text.v_align is dui2.VAlign.TOP:
        v_align = 'top'
    elif text.v_align is dui2.VAlign.CENTER:
        v_align = 'center'
    elif text.v_align is dui2.VAlign.BOTTOM:
        v_align = 'bottom'
    else:
        assert_never(text.v_align)

    out_decoration_preps.append(
        DecorationPrep(
            call=partial(
                bui.textwidget,
                position=(xoffs, yoffs),
                scale=text.scale * bscale,
                maxwidth=text.size[0] * bscale,
                max_height=text.size[1] * bscale,
                flatness=text.flatness,
                shadow=text.shadow,
                h_align=h_align,
                v_align=v_align,
                size=(0, 0),
                color=text.color,
                text=_native(text.text, packages),
                literal=True,
                transition_delay=tdelay,
                transition_type='scale',
                depth_range=text.depth_range,
            ),
            textures={},
            meshes={},
            highlight=highlight and text.highlight,
        )
    )
    # Draw square around max width/height in debug mode.
    if text.debug:
        mwfull = bscale * text.size[0]
        mhfull = bscale * text.size[1]

        if text.h_align is dui2.HAlign.LEFT:
            mwxoffs = xoffs
        elif text.h_align is dui2.HAlign.CENTER:
            mwxoffs = xoffs - mwfull * 0.5
        elif text.h_align is dui2.HAlign.RIGHT:
            mwxoffs = xoffs - mwfull
        else:
            assert_never(text.h_align)

        if text.v_align is dui2.VAlign.TOP:
            mwyoffs = yoffs - mhfull
        elif text.v_align is dui2.VAlign.CENTER:
            mwyoffs = yoffs - mhfull * 0.5
        elif text.v_align is dui2.VAlign.BOTTOM:
            mwyoffs = yoffs
        else:
            assert_never(text.v_align)

        out_decoration_preps.append(
            DecorationPrep(
                call=partial(
                    bui.imagewidget,
                    position=(mwxoffs, mwyoffs),
                    size=(mwfull, mhfull),
                    color=(1, 0, 0),
                    opacity=0.2,
                    transition_delay=tdelay,
                    transition_type='scale',
                ),
                textures={'texture': _btex('white')},
                meshes={},
                highlight=True,
            )
        )


def prep_image(
    image: dui2.Image,
    bcenter: tuple[float, float],
    bscale: float,
    tdelay: float | None,
    out_decoration_preps: list[DecorationPrep],
    *,
    highlight: bool,
) -> None:
    """Prep decorations for an image."""
    xoffs = bcenter[0] + image.position[0] * bscale
    yoffs = bcenter[1] + image.position[1] * bscale

    widthfull = bscale * image.size[0]
    heightfull = bscale * image.size[1]

    if image.h_align is dui2.HAlign.LEFT:
        xoffsfin = xoffs
    elif image.h_align is dui2.HAlign.CENTER:
        xoffsfin = xoffs - widthfull * 0.5
    elif image.h_align is dui2.HAlign.RIGHT:
        xoffsfin = xoffs - widthfull
    else:
        assert_never(image.h_align)

    if image.v_align is dui2.VAlign.TOP:
        yoffsfin = yoffs - heightfull
    elif image.v_align is dui2.VAlign.CENTER:
        yoffsfin = yoffs - heightfull * 0.5
    elif image.v_align is dui2.VAlign.BOTTOM:
        yoffsfin = yoffs
    else:
        assert_never(image.v_align)

    textures: dict[str, str] = {'texture': _refstr(image.texture)}
    if image.tint_texture is not None:
        textures['tint_texture'] = _refstr(image.tint_texture)
    if image.mask_texture is not None:
        textures['mask_texture'] = _refstr(image.mask_texture)

    meshes: dict[str, str] = {}
    if image.mesh_opaque is not None:
        meshes['mesh_opaque'] = _refstr(image.mesh_opaque)
    if image.mesh_transparent is not None:
        meshes['mesh_transparent'] = _refstr(image.mesh_transparent)

    out_decoration_preps.append(
        DecorationPrep(
            call=partial(
                bui.imagewidget,
                position=(xoffsfin, yoffsfin),
                size=(widthfull, heightfull),
                color=None if image.color is None else image.color[:3],
                opacity=1.0 if image.color is None else image.color[3],
                tint_color=image.tint_color,
                tint2_color=image.tint2_color,
                transition_delay=tdelay,
                transition_type='scale',
                depth_range=image.depth_range,
            ),
            textures=textures,
            meshes=meshes,
            highlight=highlight and image.highlight,
        )
    )

    # Show the box in debug mode. Worth having separately from the art:
    # a texture with a transparent margin draws smaller than its bounds.
    if image.debug:
        out_decoration_preps.append(
            _debug_rect(
                (xoffsfin, yoffsfin),
                (widthfull, heightfull),
                (0, 1, 0),
                0.2,
                tdelay,
            )
        )


def prep_row_debug(
    size: tuple[float, float],
    pos: tuple[float, float],
    tdelay: float | None,
    out_decoration_preps: list[DecorationPrep],
) -> None:
    """Prep debug decorations for a row."""

    textures: dict[str, str] = {'texture': _btex('white')}

    # Shrink the square we draw a tiny bit so rows butted up to
    # eachother can be seen.
    border_shrink = 1.0

    out_decoration_preps.append(
        DecorationPrep(
            call=partial(
                bui.imagewidget,
                position=(pos[0], pos[1] + border_shrink),
                size=(size[0], size[1] - 2.0 * border_shrink),
                color=(0, 0, 1.0),
                opacity=0.1,
                transition_delay=tdelay,
                transition_type='scale',
            ),
            textures=textures,
            meshes={},
            highlight=True,
        )
    )


def prep_row_debug_button(
    bsize: tuple[float, float],
    bcorner: tuple[float, float],
    tdelay: float | None,
    out_decoration_preps: list[DecorationPrep],
) -> None:
    """Prep debug decorations for a button."""
    xoffs = bcorner[0]
    yoffs = bcorner[1]

    textures: dict[str, str] = {'texture': _btex('white')}

    out_decoration_preps.append(
        DecorationPrep(
            call=partial(
                bui.imagewidget,
                position=(xoffs, yoffs),
                size=bsize,
                color=(0.0, 0.0, 1),
                opacity=0.15,
                transition_delay=tdelay,
                transition_type='scale',
            ),
            textures=textures,
            meshes={},
            highlight=True,
        )
    )


def prep_button_debug(
    bsize: tuple[float, float],
    bcenter: tuple[float, float],
    tdelay: float | None,
    out_decoration_preps: list[DecorationPrep],
) -> None:
    """Prep debug decorations for a button."""
    textures: dict[str, str] = {'texture': _btex('white')}

    out_decoration_preps.append(
        DecorationPrep(
            call=partial(
                bui.imagewidget,
                position=(
                    bcenter[0] - bsize[0] * 0.5,
                    bcenter[1] - bsize[1] * 0.5,
                ),
                size=bsize,
                color=(0, 1, 0),
                opacity=0.1,
                transition_delay=tdelay,
                transition_type='scale',
            ),
            textures=textures,
            meshes={},
            highlight=True,
        )
    )
