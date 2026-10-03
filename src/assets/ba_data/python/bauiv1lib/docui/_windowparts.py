# Released under the MIT License. See LICENSE for details.
#
"""Pieces of a doc-ui window that get built apart from it."""

from typing import TYPE_CHECKING

from efro.dataclassio import dataclass_to_json
import bacommon.docui.v2 as dui2

import bauiv1 as bui
from bauiv1 import _classiccatalogassets
from bauiv1lib.utils import scroll_fade_bottom, scroll_fade_top

if TYPE_CHECKING:
    import bacommon.depiction as bdep
    from bacommon.docui import DocUIResponse

    from bauiv1lib.docui._controller import DocUIController

#: Tint for the frame the viewer pane's mask draws around it.
_VIEWER_FRAME_COLOR = (0.45, 0.4, 0.62)

#: What the viewer pane shows while it has nothing to (and what its
#: content fades in from): the window backing's color as it reads on
#: screen (the default container tint times its texture, measured off a
#: screenshot), so an empty pane blends into the window around it.
_VIEWER_BLANK_COLOR = (0.3, 0.28, 0.37)

#: The depiction each pane key last showed, so a rebuilt window's pane
#: carries on showing it until its page arrives (see ViewerPane).
_g_last_depictions: dict[str, str] = {}


class ViewerPane:
    """A doc-ui window's viewer pane.

    An image (:func:`bauiv1.imagewidget`) showing whatever
    the window's page says to (its :attr:`~bacommon.docui.v2.Page.viewer`
    depiction), styled as a pane (rounded, framed, blending into the
    window while empty) and passing presses along (a live viewer's
    poke-to-jump). Kinds it can't show get the usual placeholder.

    :meta private:
    """

    def __init__(
        self,
        controller: DocUIController,
        parent: bui.Widget,
        position: tuple[float, float],
        size: tuple[float, float],
    ) -> None:
        # Live viewers are kept by key so that what they show carries on
        # through the window showing it being rebuilt (as happens
        # whenever ui-scale or screen size changes) and through pages
        # replacing each other. So the key needs to be the same for any
        # window standing in for another; the type of controller behind
        # them is that.
        self._key = f'{controller.get_window_extra_type_id()}|viewer'
        self.widget = bui.imagewidget(
            parent=parent,
            position=position,
            size=size,
            depiction_key=self._key,
            depiction_take_input=True,
            # Rounded edges and a frame.
            mask_texture=_classiccatalogassets.textures.viewer_mask.get(),
            depiction_frame_color=_VIEWER_FRAME_COLOR,
            depiction_backing_color=_VIEWER_BLANK_COLOR,
            # Until our page arrives, carry on showing whatever we last
            # showed (a rebuilt window's page arrives a moment after it
            # does; the page then decides).
            depiction=_g_last_depictions.get(self._key, ''),
        )

    def apply_response(self, response: DocUIResponse | None) -> None:
        """Show what a response's page says to (nothing, if not v2)."""
        if isinstance(response, dui2.Response):
            self.apply_depiction(response.page.viewer)
        else:
            self.apply_depiction(None)

    def apply_depiction(self, depiction: bdep.Depiction | None) -> None:
        """Show a page's viewer depiction (None for nothing)."""
        json = '' if depiction is None else dataclass_to_json(depiction)
        _g_last_depictions[self._key] = json
        bui.imagewidget(edit=self.widget, depiction=json)


def show_vis_area_bounds(
    parent: bui.Widget,
    left: float,
    top: float,
    width: float,
    height: float,
    *,
    top_left: bool = False,
) -> None:
    """Label the corners of a window's visible area (for debugging).

    The top left one is off unless asked for since it is always under
    the window's back/close button.

    :meta private:
    """
    corners: list[tuple[str, float, float, str, str]] = [
        ('TR', left + width, top, 'right', 'top'),
        ('BL', left, top - height, 'left', 'bottom'),
        ('BR', left + width, top - height, 'right', 'bottom'),
    ]
    if top_left:
        corners.append(('TL', left, top, 'left', 'top'))
    for text, x, y, h_align, v_align in corners:
        bui.textwidget(
            parent=parent,
            position=(x, y),
            size=(0, 0),
            color=(1, 1, 1, 0.5),
            scale=0.5,
            text=text,
            h_align=h_align,
            v_align=v_align,
        )


def add_toolbar_scroll_fades(
    root: bui.Widget,
    position: tuple[float, float],
    size: tuple[float, float],
    *,
    bottom: bool,
) -> None:
    """Fade a full-screen scroll area's content toward the toolbars.

    Along the top always; along the bottom only with ``bottom`` (a
    minimal toolbar has nothing down there).
    """
    scroll_fade_top(root, position[0], position[1], size[0], size[1])
    if bottom:
        scroll_fade_bottom(root, position[0], position[1], size[0], size[1])


# How the busy-spinner shown over a pressed widget (a button, an input
# row's control) appears: invisible for this long, then a fade-in this
# long. Quick round trips thus show nothing at all rather than the
# one-frame flash the old instant spinner gave, while slower ones get
# a soft appearance right where the press was. Sharper than the
# widget's default 0.5/0.5, which the window-centered page-load
# spinner keeps. Tuned in one place for every such spinner.
REFRESH_SPINNER_FADE_DELAY = 0.2
REFRESH_SPINNER_FADE_DURATION = 0.2


def make_busy_spinner(
    *,
    origin_widget: bui.Widget | None,
    spinner_positions: list[tuple[bui.Widget, tuple[float, float]]],
    root_widget: bui.Widget,
    window_center: tuple[float, float],
    restored: bool,
) -> bui.Widget:
    """Make the spinner a doc-ui window shows while it is busy.

    A press shows its spinner where the press was: in the pressed
    widget's parent, at the spot registered for that widget if any,
    else its center. Otherwise the spinner goes at the window's center.
    """
    parent = None if origin_widget is None else origin_widget.parent
    if parent is not None:
        assert origin_widget is not None
        position = origin_widget.center
        for widget, widgetposition in spinner_positions:
            if widget == origin_widget:
                position = widgetposition
                break
        return bui.spinnerwidget(
            parent=parent,
            position=position,
            size=48,
            fade_delay=REFRESH_SPINNER_FADE_DELAY,
            fade_duration=REFRESH_SPINNER_FADE_DURATION,
        )
    return bui.spinnerwidget(
        parent=root_widget,
        position=window_center,
        size=48,
        # With restored windows we're likely to have stuff under the
        # spinner. Bomb looks nicer but simple is more readable in those
        # cases.
        style='simple' if restored else 'bomb',
        # (Default fade timing: this one was never instant.)
    )
