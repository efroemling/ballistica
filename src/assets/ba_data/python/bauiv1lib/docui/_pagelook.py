# Released under the MIT License. See LICENSE for details.
#
"""Doc-ui page looks: a page's look values, defaults applied.

See :class:`bacommon.docui.v2.Page` (``row_spacing``, ``spacing``, ``h_inset``,
``v_inset``, ``button_color``, ``default_button_color``) for the
page's values, and :class:`bacommon.docui.v2.Browse` /
:class:`bacommon.docui.v2.Popup` for the window frame's colors, which
come with the link instead.
"""

from dataclasses import dataclass

import bacommon.docui.v2 as dui2
import bauiv1 as bui

type Rgb = tuple[float, float, float]

#: The engine's own start-button color: what a page's default button
#: gets unless it says otherwise.
_DEFAULT_DEFAULT_BUTTON_COLOR: Rgb = (0.2, 0.8, 0.55)


@dataclass(frozen=True)
class RowSpacing:
    """A page's room between rows by kind, defaults applied.

    See :class:`bacommon.docui.v2.Spacing`.
    """

    title: float
    subtitle: float
    footnote: float
    button_row: float
    control_row: float
    section: float

    @classmethod
    def of(cls, page: dui2.Page) -> RowSpacing:
        """A page's spacing: its own, else its flat row spacing, else
        the defaults."""
        flat = page.row_spacing
        base = (
            _DEFAULT_SPACING
            if flat is None
            else RowSpacing(flat, flat, flat, flat, flat, flat)
        )
        own = page.spacing
        if own is None:
            return base

        def _pick(val: float | None, fallback: float) -> float:
            return fallback if val is None else val

        return RowSpacing(
            title=_pick(own.title, base.title),
            subtitle=_pick(own.subtitle, base.subtitle),
            footnote=_pick(own.footnote, base.footnote),
            button_row=_pick(own.button_row, base.button_row),
            control_row=_pick(own.control_row, base.control_row),
            section=_pick(own.section, base.section),
        )


_DEFAULT_SPACING = RowSpacing(
    title=dui2.DEFAULT_TITLE_SPACING,
    subtitle=dui2.DEFAULT_SUBTITLE_SPACING,
    footnote=dui2.DEFAULT_FOOTNOTE_SPACING,
    button_row=dui2.DEFAULT_BUTTON_ROW_SPACING,
    control_row=dui2.DEFAULT_CONTROL_ROW_SPACING,
    section=dui2.DEFAULT_SECTION_SPACING,
)


@dataclass(frozen=True)
class PageLook:
    """A page's look values with defaults applied.

    A button color left None means the engine's own. The default-button
    color is always given, as it is set afresh for each page a window
    shows.
    """

    h_inset: float
    v_inset: float
    spacing: RowSpacing
    button_color: Rgb | None
    default_button_color: Rgb

    @classmethod
    def of(cls, page: dui2.Page | None) -> PageLook:
        """The look a page asks for (the defaults for no page)."""
        if page is None:
            return DEFAULT_LOOK
        return PageLook(
            h_inset=(
                dui2.DEFAULT_H_INSET if page.h_inset is None else page.h_inset
            ),
            v_inset=(
                dui2.DEFAULT_V_INSET if page.v_inset is None else page.v_inset
            ),
            spacing=RowSpacing.of(page),
            button_color=page.button_color,
            default_button_color=(
                _DEFAULT_DEFAULT_BUTTON_COLOR
                if page.default_button_color is None
                else page.default_button_color
            ),
        )

    def fade_key(self) -> tuple[float, float]:
        """What a window's scroll-area fades depend on in a look.

        Its insets: fades end by where content starts (see
        :func:`~bauiv1lib.docui._panes.edge_fades`).
        """
        return (self.h_inset, self.v_inset)


#: The look of a page that sets nothing (and of a window before its
#: first page arrives).
DEFAULT_LOOK = PageLook(
    h_inset=dui2.DEFAULT_H_INSET,
    v_inset=dui2.DEFAULT_V_INSET,
    spacing=_DEFAULT_SPACING,
    button_color=None,
    default_button_color=_DEFAULT_DEFAULT_BUTTON_COLOR,
)


def apply_frame_colors(
    root: bui.Widget,
    background_color: Rgb | None,
    cancel_button_color: Rgb | None,
) -> None:
    """Set a window's frame colors on its root container.

    Only what's given; the engine's own colors stay otherwise.
    """
    if background_color is not None:
        bui.containerwidget(edit=root, color=background_color)
    if cancel_button_color is not None:
        bui.containerwidget(edit=root, cancel_button_color=cancel_button_color)
