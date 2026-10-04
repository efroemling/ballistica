# Released under the MIT License. See LICENSE for details.
#
"""Prep for doc-ui buttons, wherever they live.

Buttons show up in rows of them and as the control of a button control
row; both build theirs here so a button looks and acts the same in
either.
"""

from functools import partial
from typing import TYPE_CHECKING, assert_never

from efro.util import strict_partial
from efro.dataclassio import dataclass_to_json
import bacommon.docui.v2 as dui2
import bauiv1 as bui

from bauiv1lib.docui.prep._types import (
    AnimTargetKind,
    AnimTargetPrep,
    ButtonPrep,
)
from bauiv1lib.docui.prep._depiction import h_align_arg, v_align_arg
from bauiv1lib.docui.prep._calls2 import (
    prep_button_debug,
    prep_decorations,
    prep_menu,
    prep_popup_text,
)

if TYPE_CHECKING:
    from bacommon.assetpackage import ApverNum

    from bauiv1lib.docui._window import DocUIWindow
    from bauiv1lib.docui.prep._types import NativeLangStrFn

#: Size of a button that doesn't give one.
_DEFAULT_BUTTON_SIZE = (150.0, 100.0)


def button_size(button: dui2.Button) -> tuple[float, float]:
    """A button's width and height, before its scale is applied.

    :meta private:
    """
    return _DEFAULT_BUTTON_SIZE if button.size is None else button.size


def button_padded_size(button: dui2.Button) -> tuple[float, float]:
    """Room a button takes up: its size plus its padding, at its scale.

    :meta private:
    """
    width, height = button_size(button)
    return (
        (width + button.padding_left + button.padding_right) * button.scale,
        (height + button.padding_top + button.padding_bottom) * button.scale,
    )


def _button_type(style: dui2.ButtonStyle) -> str:
    """The button-widget type for a button style."""
    btype: str
    match style:
        case dui2.ButtonStyle.SQUARE:
            btype = 'square'
        case dui2.ButtonStyle.TAB:
            btype = 'tab'
        case dui2.ButtonStyle.SMALL:
            btype = 'small'
        case dui2.ButtonStyle.MEDIUM:
            btype = 'medium'
        case dui2.ButtonStyle.LARGE:
            btype = 'large'
        case dui2.ButtonStyle.LARGER:
            btype = 'larger'
        case dui2.ButtonStyle.BACK:
            btype = 'back'
        case dui2.ButtonStyle.BACK_SMALL:
            btype = 'backSmall'
        case dui2.ButtonStyle.SQUARE_WIDE:
            btype = 'squareWide'
        case _:
            assert_never(style)
    return btype


def _depiction_kwds(button: dui2.Button) -> dict:
    """Button-widget args for a button's depiction body (none if none).

    Left out entirely without one, so plain buttons don't grow a
    depiction slot.
    """
    if button.depiction is None:
        return {}
    return {
        'depiction': dataclass_to_json(button.depiction),
        'depiction_h_align': h_align_arg(button.depiction_h_align),
        'depiction_v_align': v_align_arg(button.depiction_v_align),
        'depiction_hit_area': button.depiction_hit_area,
        'depiction_debug': button.debug,
    }


def prep_button(
    button: dui2.Button,
    *,
    position: tuple[float, float],
    widgetid: str,
    tdelay: float | None,
    packages: list[ApverNum],
    native: NativeLangStrFn,
    show_buffers_h: tuple[float, float] | None,
    disabled: bool,
) -> ButtonPrep:
    """Prep a button whose bottom left corner sits at ``position``.

    ``tdelay`` is when it scales in (None to pop in instantly).
    ``show_buffers_h`` is how much to keep in view to its left and
    right when it is selected, for a button in a row that scrolls
    sideways; None for one that isn't, which also leaves its
    directional navigation to whoever places it. ``disabled`` is
    whether it winds up disabled (its own flag or its row's).

    :meta private:
    """
    # Safe up-call: _calls (which imports us) is loaded by the time
    # anything gets prepped.
    from bauiv1lib.docui.prep._calls import (  # pylint: disable=cyclic-import
        refstr,
    )

    bwidth, bheight = button_size(button)
    bscale = button.scale
    center_x = position[0] + bwidth * bscale * 0.5
    center_y = position[1] + bheight * bscale * 0.5

    editkwds: dict = {'depth_range': button.depth_range}
    if show_buffers_h is not None:
        # TODO: Calc left/right vals properly based on our size and
        # padding.
        editkwds['show_buffer_left'] = show_buffers_h[0]
        editkwds['show_buffer_right'] = show_buffers_h[1]
        # Rows of buttons explicitly assign all neighbor selection;
        # anything left over should go to toolbars.
        editkwds['auto_select_toolbars_only'] = True

    buttonprep = ButtonPrep(
        buttoncall=partial(
            bui.buttonwidget,
            id=widgetid,
            position=position,
            size=(bwidth, bheight),
            scale=bscale,
            color=(None if button.color is None else button.color[:3]),
            textcolor=button.label_color,
            text_flatness=(button.label_flatness),
            text_scale=button.label_scale,
            button_type=_button_type(button.style),
            opacity=(1.0 if button.color is None else button.color[3]),
            label=('' if button.label is None else native(button.label)),
            text_literal=True,
            autoselect=True,
            enable_sound=False,
            transition_delay=tdelay,
            transition_type='scale',
            icon_color=button.icon_color,
            iconscale=button.icon_scale,
            better_bg_fit=True,
            enabled=not disabled,
            **_depiction_kwds(button),
        ),
        buttoneditcall=partial(bui.widget, **editkwds),
        decorations=[],
        textures={},
        widgetid=widgetid,
        action=button.action,
        popup=(
            prep_menu(button.action, packages)
            if isinstance(button.action, dui2.Menu)
            else (
                prep_popup_text(button.action, packages)
                if isinstance(button.action, dui2.PopupText)
                else None
            )
        ),
        anim=(
            None
            if button.anim_id is None
            else AnimTargetPrep(
                anim_id=button.anim_id,
                kind=AnimTargetKind.BUTTON,
                position=position,
                size=(bwidth, bheight),
                scale=bscale,
                opacity=1.0 if button.color is None else button.color[3],
            )
        ),
    )
    if button.texture is not None:
        buttonprep.textures['texture'] = refstr(button.texture)

    if button.icon is not None:
        buttonprep.textures['icon'] = refstr(button.icon)

    if button.debug:
        prep_button_debug(
            (bwidth * bscale, bheight * bscale),
            (center_x, center_y),
            tdelay,
            buttonprep.decorations,
        )
    prep_decorations(
        [] if button.decorations is None else button.decorations,
        center_x,
        center_y,
        bscale,
        tdelay,
        packages=packages,
        highlight=True,
        out_decoration_preps=buttonprep.decorations,
    )
    return buttonprep


def instantiate_button(
    buttonprep: ButtonPrep, *, parent: bui.Widget, window: DocUIWindow
) -> bui.Widget:
    """Create the widgets for a prepped button (it and its decorations).

    :meta private:
    """
    # pylint: disable=cyclic-import
    # Safe up-call, as in prep_button().
    from bauiv1lib.docui.prep._decorations import instantiate_decorations

    kwds: dict = {
        'parent': parent,
        'on_activate_call': strict_partial(
            window.controller.run_button_action,
            window,
            buttonprep.widgetid,
            buttonprep.action,
            buttonprep.popup,
        ),
    }
    for texarg, texname in buttonprep.textures.items():
        kwds[texarg] = bui.texture_from_ref(texname)
    btn = buttonprep.buttoncall(**kwds)
    assert buttonprep.buttoneditcall is not None
    buttonprep.buttoneditcall(edit=btn)
    if buttonprep.anim is not None:
        window.anim_targets.register(buttonprep.anim, btn)
    instantiate_decorations(
        buttonprep.decorations,
        parent=parent,
        draw_controller=btn,
        anim_targets=window.anim_targets,
    )
    return btn
