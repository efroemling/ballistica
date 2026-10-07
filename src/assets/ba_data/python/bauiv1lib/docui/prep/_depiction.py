# Released under the MIT License. See LICENSE for details.
#
"""Prep for doc-ui depiction decorations.

A depiction decoration gives a box (center + size) and an alignment;
an image widget showing the depiction does the rest -- fitting one with
a shape of its own into the box by the alignment, drawing it, and
showing a placeholder for kinds this build can't draw. See
``docs/initiatives/depictions.md``.
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
)

if TYPE_CHECKING:
    from typing import Literal

    from bacommon.assetspec import TextureSpec


def prep_depiction(
    decoration: dui2.Depiction,
    bcenter: tuple[float, float],
    bscale: float,
    tdelay: float | None,
    out_decoration_preps: list[DecorationPrep],
    *,
    highlight: bool,
    suffix: str | None = None,
) -> None:
    """Prep a depiction decoration.

    ``suffix`` is the decoration's suffix, already evaluated.
    """
    width = decoration.size[0] * bscale
    height = decoration.size[1] * bscale
    left = bcenter[0] + decoration.position[0] * bscale - width * 0.5
    bottom = bcenter[1] + decoration.position[1] * bscale - height * 0.5

    out_decoration_preps.append(
        DecorationPrep(
            call=partial(
                bui.imagewidget,
                position=(left, bottom),
                size=(width, height),
                depiction=dataclass_to_json(decoration.depiction),
                depiction_h_align=h_align_arg(decoration.h_align),
                depiction_v_align=v_align_arg(decoration.v_align),
                transition_delay=tdelay,
                transition_type='scale',
                depth_range=decoration.depth_range,
                depiction_debug=decoration.debug,
                depiction_suffix=suffix,
                depiction_color_override=decoration.color_override,
                depiction_use_color_override=(
                    decoration.color_override is not None
                ),
            ),
            textures={},
            meshes={},
            highlight=highlight and decoration.highlight,
            anim=(
                None
                if decoration.anim_id is None
                else AnimTargetPrep(
                    anim_id=decoration.anim_id,
                    kind=AnimTargetKind.IMAGE,
                    position=(left, bottom),
                    size=(width, height),
                )
            ),
        )
    )

    if decoration.debug:
        out_decoration_preps.append(
            DecorationPrep(
                call=partial(
                    bui.imagewidget,
                    position=(left, bottom),
                    size=(width, height),
                    color=(1, 0, 0),
                    opacity=0.2,
                    transition_delay=tdelay,
                    transition_type='scale',
                ),
                textures={'texture': _texname(_builtinassets.textures.white)},
                meshes={},
                highlight=True,
            )
        )


def h_align_arg(val: dui2.HAlign) -> Literal['left', 'center', 'right']:
    """A depiction h-align as image/button widget args take it.

    :meta private:
    """
    if val is dui2.HAlign.LEFT:
        return 'left'
    if val is dui2.HAlign.CENTER:
        return 'center'
    if val is dui2.HAlign.RIGHT:
        return 'right'
    assert_never(val)


def v_align_arg(val: dui2.VAlign) -> Literal['top', 'center', 'bottom']:
    """A depiction v-align as image/button widget args take it.

    :meta private:
    """
    if val is dui2.VAlign.TOP:
        return 'top'
    if val is dui2.VAlign.CENTER:
        return 'center'
    if val is dui2.VAlign.BOTTOM:
        return 'bottom'
    assert_never(val)


def _texname(spec: TextureSpec) -> str:
    # Safe up-call: _calls only imports prep modules from inside
    # functions, so by the time this runs it is fully imported.
    # pylint: disable-next=cyclic-import
    from bauiv1lib.docui.prep._calls import refstr

    return refstr(spec)
