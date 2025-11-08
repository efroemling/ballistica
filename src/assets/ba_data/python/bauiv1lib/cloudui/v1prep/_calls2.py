# Released under the MIT License. See LICENSE for details.
#
"""Prep functionality for our UI.

We do all layout math and bake out partial ui calls in a background
thread so there's as little work to do in the ui thread as possible.
"""

from __future__ import annotations

from functools import partial
from typing import TYPE_CHECKING, assert_never

import bacommon.cloudui.v1 as clui1
import bauiv1 as bui

from bauiv1lib.cloudui.v1prep._types import DecorationPrep

if TYPE_CHECKING:
    from typing import Callable

    from bauiv1lib.cloudui import CloudUIWindow


def prep_decorations(
    decorations: list[clui1.Decoration],
    center_x: float,
    center_y: float,
    scale: float,
    tdelay: float | None,
    *,
    highlight: bool,
    out_decoration_preps: list[DecorationPrep],
) -> None:
    """Prep appropriate decoration types for a list of decorations."""
    for decoration in decorations:
        dectypeid = decoration.get_type_id()
        if dectypeid is clui1.DecorationTypeID.UNKNOWN:
            if bui.do_once():
                bui.uilog.exception(
                    'CloudUI receieved unknown decoration;'
                    ' this is likely a server error.'
                )
        elif dectypeid is clui1.DecorationTypeID.TEXT:
            assert isinstance(decoration, clui1.Text)
            prep_text(
                decoration,
                (center_x, center_y),
                scale,
                tdelay,
                out_decoration_preps,
                highlight=highlight,
            )

        elif dectypeid is clui1.DecorationTypeID.IMAGE:
            assert isinstance(decoration, clui1.Image)
            prep_image(
                decoration,
                (center_x, center_y),
                scale,
                tdelay,
                out_decoration_preps,
                highlight=highlight,
            )
        elif dectypeid is clui1.DecorationTypeID.DISPLAY_ITEM:
            assert isinstance(decoration, clui1.DisplayItem)

            prep_display_item(
                decoration,
                (center_x, center_y),
                scale,
                tdelay,
                out_decoration_preps,
                highlight=highlight,
            )
            print('WOULD PREP DISPLAY ITEM')
        else:
            assert_never(dectypeid)


def prep_text(
    text: clui1.Text,
    bcenter: tuple[float, float],
    bscale: float,
    tdelay: float | None,
    out_decoration_preps: list[DecorationPrep],
    *,
    highlight: bool,
) -> None:
    """Prep decorations for text."""
    # pylint: disable=too-many-branches
    xoffs = bcenter[0] + text.position[0] * bscale
    yoffs = bcenter[1] + text.position[1] * bscale

    if text.h_align is clui1.HAlign.LEFT:
        h_align = 'left'
    elif text.h_align is clui1.HAlign.CENTER:
        h_align = 'center'
    elif text.h_align is clui1.HAlign.RIGHT:
        h_align = 'right'
    else:
        assert_never(text.h_align)

    if text.v_align is clui1.VAlign.TOP:
        v_align = 'top'
    elif text.v_align is clui1.VAlign.CENTER:
        v_align = 'center'
    elif text.v_align is clui1.VAlign.BOTTOM:
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
                text=text.text,
                literal=not text.is_lstr,
                transition_delay=tdelay,
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

        if text.h_align is clui1.HAlign.LEFT:
            mwxoffs = xoffs
        elif text.h_align is clui1.HAlign.CENTER:
            mwxoffs = xoffs - mwfull * 0.5
        elif text.h_align is clui1.HAlign.RIGHT:
            mwxoffs = xoffs - mwfull
        else:
            assert_never(text.h_align)

        if text.v_align is clui1.VAlign.TOP:
            mwyoffs = yoffs - mhfull
        elif text.v_align is clui1.VAlign.CENTER:
            mwyoffs = yoffs - mhfull * 0.5
        elif text.v_align is clui1.VAlign.BOTTOM:
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
                ),
                textures={'texture': 'white'},
                meshes={},
                highlight=True,
            )
        )


def prep_image(
    image: clui1.Image,
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

    if image.h_align is clui1.HAlign.LEFT:
        xoffsfin = xoffs
    elif image.h_align is clui1.HAlign.CENTER:
        xoffsfin = xoffs - widthfull * 0.5
    elif image.h_align is clui1.HAlign.RIGHT:
        xoffsfin = xoffs - widthfull
    else:
        assert_never(image.h_align)

    if image.v_align is clui1.VAlign.TOP:
        yoffsfin = yoffs - heightfull
    elif image.v_align is clui1.VAlign.CENTER:
        yoffsfin = yoffs - heightfull * 0.5
    elif image.v_align is clui1.VAlign.BOTTOM:
        yoffsfin = yoffs
    else:
        assert_never(image.v_align)

    textures: dict[str, str] = {'texture': image.texture}
    if image.tint_texture is not None:
        textures['tint_texture'] = image.tint_texture
    if image.mask_texture is not None:
        textures['mask_texture'] = image.mask_texture

    meshes: dict[str, str] = {}
    if image.mesh_opaque is not None:
        meshes['mesh_opaque'] = image.mesh_opaque
    if image.mesh_transparent is not None:
        meshes['mesh_transparent'] = image.mesh_transparent

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
                depth_range=image.depth_range,
            ),
            textures=textures,
            meshes=meshes,
            highlight=highlight and image.highlight,
        )
    )


def prep_row_debug(
    size: tuple[float, float],
    pos: tuple[float, float],
    tdelay: float | None,
    out_decoration_preps: list[DecorationPrep],
) -> None:
    """Prep debug decorations for a row."""

    textures: dict[str, str] = {'texture': 'white'}

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

    textures: dict[str, str] = {'texture': 'white'}

    out_decoration_preps.append(
        DecorationPrep(
            call=partial(
                bui.imagewidget,
                position=(xoffs, yoffs),
                size=bsize,
                color=(0.0, 0.0, 1),
                opacity=0.15,
                transition_delay=tdelay,
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
    textures: dict[str, str] = {'texture': 'white'}

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
            ),
            textures=textures,
            meshes={},
            highlight=True,
        )
    )


def prep_display_item(
    display_item: clui1.DisplayItem,
    parent_center: tuple[float, float],
    parent_scale: float,
    tdelay: float | None,
    out_decoration_preps: list[DecorationPrep],
    *,
    highlight: bool,
) -> None:
    """Prep decorations for a display-item."""

    # Calc center and size of our bounds based on parent.
    our_center = (
        parent_center[0] + display_item.position[0] * parent_scale,
        parent_center[1] + display_item.position[1] * parent_scale,
    )
    bounds_size = (
        parent_scale * display_item.size[0],
        parent_scale * display_item.size[1],
    )

    # Draw our bounds if debug mode is enabled.
    if display_item.debug:
        out_decoration_preps.append(
            DecorationPrep(
                call=partial(
                    bui.imagewidget,
                    color=(1, 1, 0),
                    opacity=0.1,
                    position=(
                        our_center[0] - bounds_size[0] * 0.5,
                        our_center[1] - bounds_size[1] * 0.5,
                    ),
                    size=bounds_size,
                    transition_delay=tdelay,
                ),
                textures={'texture': 'white'},
                meshes={},
                highlight=highlight and display_item.highlight,
            )
        )

    # Calc our width and height based on our aspect ratio so we fit in
    # the provided bounds.
    aspect_ratio = 0.75  # Bit less tall than wide.

    if bounds_size[0] * aspect_ratio > bounds_size[1]:
        print('size to height')
        height = bounds_size[1]
        width = height / aspect_ratio
    else:
        width = bounds_size[0]
        height = width * aspect_ratio

    # Show our constrained bounds in debug mode.
    if display_item.debug:
        out_decoration_preps.append(
            DecorationPrep(
                call=partial(
                    bui.imagewidget,
                    color=(1, 0.5, 0),
                    opacity=0.2,
                    position=(
                        our_center[0] - width * 0.5,
                        our_center[1] - height * 0.5,
                    ),
                    size=(width, height),
                    transition_delay=tdelay,
                ),
                textures={'texture': 'white'},
                meshes={},
                highlight=highlight and display_item.highlight,
            )
        )
