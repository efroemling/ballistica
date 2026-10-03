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
from bauiv1 import _builtinassets

from bauiv1lib.docui.prep._types import (
    AnimTargetKind,
    AnimTargetPrep,
    DecorationPrep,
    MenuPrep,
)
from bauiv1lib.docui.prep._depiction import prep_depiction

if TYPE_CHECKING:
    from bacommon.assetpackage import ApverNum

    from typing import Any, Callable

    from bacommon.langstr import LangStrSpec
    from bacommon.assetspec import TextureSpec, MeshSpec
    from bauiv1lib.docui import DocUIWindow


def _native(lstr: 'LangStrSpec | int', packages: list[ApverNum]) -> bui.LangStr:
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
    # LEGACY: builds a qualified path by hand, which nothing should
    # do -- the parts are private now precisely to flag it. Kept
    # only until this file's callers hold handles instead; see
    # docs/followups.md "hand-built asset paths".
    # pylint: disable-next=protected-access
    return f'{_builtinassets._ASSET_PACKAGE}:textures/{name}'


def _refstr(ref: 'TextureSpec | MeshSpec | int') -> str:
    """Qualified engine name for a typed asset ref.

    Delegates so the un-de-indexed-index check lives in exactly one
    place. This was previously typed ``Any``, which meant a widened
    asset-slot type could pass an integer straight through to the
    renderer without mypy noticing -- the sibling in ``_calls`` caught
    it, this one did not.
    """
    # Safe up-call: _calls only imports us from inside functions, so by
    # the time this runs it is fully imported.
    # pylint: disable-next=cyclic-import
    from bauiv1lib.docui.prep._calls import refstr

    return refstr(ref)


def prep_decorations(
    decorations: list[dui2.Decoration],
    center_x: float,
    center_y: float,
    scale: float,
    tdelay: float | None,
    *,
    packages: list[ApverNum],
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
        elif dectypeid is dui2.DecorationTypeID.DEPICTION:
            assert isinstance(decoration, dui2.Depiction)
            prep_depiction(
                decoration,
                (center_x, center_y),
                scale,
                tdelay,
                out_decoration_preps,
                highlight=highlight,
            )
        else:
            assert_never(dectypeid)


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
    packages: list[ApverNum],
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

    if text.image_left is not None or text.image_right is not None:
        _prep_text_with_images(
            text,
            (xoffs, yoffs),
            bscale,
            tdelay,
            out_decoration_preps,
            packages=packages,
            highlight=highlight,
        )
    else:
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
                anim=(
                    None
                    if text.anim_id is None
                    else AnimTargetPrep(
                        anim_id=text.anim_id,
                        kind=AnimTargetKind.TEXT,
                        position=(xoffs, yoffs),
                        scale=text.scale * bscale,
                        opacity=1.0 if text.color is None else text.color[3],
                        color=None if text.color is None else text.color[:3],
                    )
                ),
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


def _text_image_box(img: dui2.TextImage) -> tuple[float, float]:
    """An end image's layout box (size less insets), in text units.

    This is the box layout uses; the full image still draws around it.
    """
    left, bottom, right, top = img.insets
    return (
        img.size[0] * (1.0 - left - right),
        img.size[1] * (1.0 - bottom - top),
    )


def _text_image_footprint(img: dui2.TextImage | None) -> float:
    """Width an end image adds to its text's unit, in text units."""
    return 0.0 if img is None else _text_image_box(img)[0]


def _place_text_unit(
    text: dui2.Text,
    anchor: tuple[float, float],
    bscale: float,
    textw: float,
    texth: float,
) -> tuple[float, float, float]:
    """Fit and align a text-with-images unit.

    Returns the unit's left edge, its vertical center, and the final
    text-units-to-screen scale.
    """
    left = text.image_left
    right = text.image_right
    unitw = _text_image_footprint(left) + textw + _text_image_footprint(right)
    unith = max(
        texth,
        0.0 if left is None else _text_image_box(left)[1],
        0.0 if right is None else _text_image_box(right)[1],
    )

    # Text units to screen units; then shrink to fit. A zero box
    # dimension means unconstrained, as for plain text.
    scale = text.scale * bscale
    maxw = text.size[0] * bscale
    maxh = text.size[1] * bscale
    if 0.0 < maxw < unitw * scale:
        scale = maxw / unitw
    if 0.0 < maxh < unith * scale:
        scale = min(scale, maxh / unith)

    width = unitw * scale
    if text.h_align is dui2.HAlign.LEFT:
        minx = anchor[0]
    elif text.h_align is dui2.HAlign.CENTER:
        minx = anchor[0] - width * 0.5
    elif text.h_align is dui2.HAlign.RIGHT:
        minx = anchor[0] - width
    else:
        assert_never(text.h_align)

    height = unith * scale
    if text.v_align is dui2.VAlign.TOP:
        centery = anchor[1] - height * 0.5
    elif text.v_align is dui2.VAlign.CENTER:
        centery = anchor[1]
    elif text.v_align is dui2.VAlign.BOTTOM:
        centery = anchor[1] + height * 0.5
    else:
        assert_never(text.v_align)

    return minx, centery, scale


def _prep_text_with_images(
    text: dui2.Text,
    anchor: tuple[float, float],
    bscale: float,
    tdelay: float | None,
    out_decoration_preps: list[DecorationPrep],
    *,
    packages: list[ApverNum],
    highlight: bool,
) -> None:
    """Prep a text and its end images as one measured, fitted unit.

    The unit -- left image, text, right image -- is measured in text
    units, shrunk (never grown) to fit the text's size box on each
    constrained axis, then placed at the anchor by the text's own
    alignment. Everything is done here so the text widget itself needs
    no maxwidth handling (it would shrink the text alone and strand the
    images).
    """
    lstr = _native(text.text, packages)
    evaluated = lstr.evaluate()
    textw = bui.get_string_width(evaluated, suppress_warning=True)

    left = text.image_left
    right = text.image_right
    leftw = _text_image_footprint(left)
    minx, centery, scale = _place_text_unit(
        text,
        anchor,
        bscale,
        textw,
        bui.get_string_height(evaluated, suppress_warning=True),
    )

    highlight = highlight and text.highlight

    out_decoration_preps.append(
        DecorationPrep(
            call=partial(
                bui.textwidget,
                position=(minx + leftw * scale, centery),
                scale=scale,
                flatness=text.flatness,
                shadow=text.shadow,
                h_align='left',
                v_align='center',
                size=(0, 0),
                color=text.color,
                text=lstr,
                literal=True,
                transition_delay=tdelay,
                transition_type='scale',
                depth_range=text.depth_range,
            ),
            textures={},
            meshes={},
            highlight=highlight,
            # The text and its images all animate as the text's id
            # (each piece about its own center).
            anim=(
                None
                if text.anim_id is None
                else AnimTargetPrep(
                    anim_id=text.anim_id,
                    kind=AnimTargetKind.TEXT,
                    position=(minx + leftw * scale, centery),
                    scale=scale,
                    opacity=1.0 if text.color is None else text.color[3],
                    color=None if text.color is None else text.color[:3],
                )
            ),
        )
    )

    # Place each image's layout box: the left one at the unit's outer
    # left edge, the right one just past the text, both centered on the
    # line. The full image then draws around that box, shifted by its
    # purely visual offset.
    for img, boxx in (
        (left, minx),
        (right, minx + (leftw + textw) * scale),
    ):
        if img is None:
            continue
        boxy = centery - _text_image_box(img)[1] * scale * 0.5
        imgpos = (
            boxx + (img.offset[0] - img.insets[0] * img.size[0]) * scale,
            boxy + (img.offset[1] - img.insets[1] * img.size[1]) * scale,
        )
        imgsize = (img.size[0] * scale, img.size[1] * scale)
        imgopacity = 1.0 if img.color is None else img.color[3]
        out_decoration_preps.append(
            DecorationPrep(
                call=partial(
                    bui.imagewidget,
                    position=imgpos,
                    size=imgsize,
                    color=None if img.color is None else img.color[:3],
                    opacity=imgopacity,
                    transition_delay=tdelay,
                    transition_type='scale',
                    depth_range=text.depth_range,
                ),
                textures={'texture': _refstr(img.texture)},
                meshes={},
                highlight=highlight,
                anim=(
                    None
                    if text.anim_id is None
                    else AnimTargetPrep(
                        anim_id=text.anim_id,
                        kind=AnimTargetKind.IMAGE,
                        position=imgpos,
                        size=imgsize,
                        opacity=imgopacity,
                    )
                ),
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

    # 9-patch borders are in the image's own units, so they scale with
    # its size.
    npatch = image.nine_patch
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
                tint3_color=image.tint3_color,
                nine_patch_insets=None if npatch is None else npatch.insets,
                nine_patch_borders=(
                    None
                    if npatch is None
                    else tuple(b * bscale for b in npatch.borders)
                ),
                nine_patch_tile=(
                    None if npatch is None else (npatch.tile_h, npatch.tile_v)
                ),
                transition_delay=tdelay,
                transition_type='scale',
                depth_range=image.depth_range,
            ),
            textures=textures,
            meshes=meshes,
            highlight=highlight and image.highlight,
            anim=(
                None
                if image.anim_id is None
                else AnimTargetPrep(
                    anim_id=image.anim_id,
                    kind=AnimTargetKind.IMAGE,
                    position=(xoffsfin, yoffsfin),
                    size=(widthfull, heightfull),
                    opacity=1.0 if image.color is None else image.color[3],
                )
            ),
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


def _backing_imagewidget(
    *,
    parent: bui.Widget,
    texture: bui.Texture,
    position: tuple[float, float],
    size: tuple[float, float],
    color: tuple[float, float, float],
    opacity: float,
    transition_delay: float | None,
) -> bui.Widget:
    """An image widget drawn behind everything else on its page.

    The page's container gives its children a single shared depth
    slice, where a card's opaque contents would depth-fight it.
    """
    img = bui.imagewidget(
        parent=parent,
        texture=texture,
        position=position,
        size=size,
        color=color,
        opacity=opacity,
        transition_delay=transition_delay,
        transition_type='scale',
    )
    bui.widget(edit=img, draw_behind=True)
    return img


def prep_section_backing(
    size: tuple[float, float],
    pos: tuple[float, float],
    *,
    color: tuple[float, float, float, float],
    texture: TextureSpec | int | None,
    tdelay: float | None,
    out_decoration_preps: list[DecorationPrep],
) -> None:
    """Prep a section's backing: a tinted rect (or texture) behind it."""
    out_decoration_preps.append(
        DecorationPrep(
            call=partial(
                _backing_imagewidget,
                position=pos,
                size=size,
                color=color[:3],
                opacity=color[3],
                transition_delay=tdelay,
            ),
            textures={
                'texture': (
                    _btex('white') if texture is None else _refstr(texture)
                )
            },
            meshes={},
            highlight=False,
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


def prep_menu(menu: dui2.Menu, packages: list[ApverNum]) -> MenuPrep:
    """Prep the menu a button with a menu action pops up."""
    labels = [_native(item.label, packages) for item in menu.items]

    # The menu sizes itself by measuring these on the logic thread when
    # it opens. Measuring here (we are in a background thread) gets any
    # lazy OS font loads they incur out of the way first.
    for label in labels:
        bui.get_string_width(label.evaluate(), suppress_warning=True)

    return MenuPrep(
        labels=labels,
        disabled=[item.disabled for item in menu.items],
        actions=[item.action for item in menu.items],
    )
