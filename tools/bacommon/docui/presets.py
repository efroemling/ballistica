# Released under the MIT License. See LICENSE for details.
#
"""Canned doc-ui styling built from plain v2 rows and buttons.

Higher-level looks that recur across pages (a stack of grouped
section buttons, say) live here so their spacing numbers have one
owner. Everything returned is ordinary :mod:`bacommon.docui.v2` data,
so callers can still adjust what they get back, and nothing here
touches the wire format.
"""

from enum import Enum
from typing import TYPE_CHECKING, assert_never

import bacommon.docui.v2 as dui2

if TYPE_CHECKING:
    from typing import Sequence

    # (Signatures spell types out in full rather than via the dui2
    # alias; the docs can't resolve the alias.)
    import bacommon.docui.v2
    from bacommon.langstr import LangStrSpec


class SectionButtonSize(Enum):
    """Sizes of :func:`section_button`."""

    #: A lone button under some other content.
    MEDIUM = 'medium'

    #: The standard full-width button leading to another page.
    LARGE = 'large'


def section_button(
    label: LangStrSpec,
    action: bacommon.docui.v2.Action,
    *,
    size: SectionButtonSize = SectionButtonSize.LARGE,
) -> bacommon.docui.v2.Button:
    """Return a button leading to a page section (or doing one thing).

    In a :attr:`~bacommon.docui.v2.ButtonRowLayout.FILL` row (one or
    several side by side) its width only matters relative to its
    neighbors'; its style and height are what count.
    """
    style: dui2.ButtonStyle
    dims: tuple[float, float]
    match size:
        case SectionButtonSize.MEDIUM:
            style, dims = dui2.ButtonStyle.MEDIUM, (310.0, 50.0)
        case SectionButtonSize.LARGE:
            # Nearly as wide as a small layout's 600-wide column. A
            # button row there shows 586 of its content (the h-scroll's
            # borders and margins take the rest) and adds 50 of buffers
            # and padding around the button, so anything past 536 lets
            # the row scroll (and past 550 grows page arrows). Keep
            # some slack under that.
            style, dims = dui2.ButtonStyle.LARGE, (520.0, 60.0)
        case _:
            assert_never(size)
    return dui2.Button(label=label, style=style, size=dims, action=action)


def button_stack(
    groups: Sequence[Sequence[bacommon.docui.v2.Button]],
    *,
    group_spacing: float = 27.0,
    first_group_spacing: float | None = None,
) -> list[bacommon.docui.v2.Row]:
    """Return rows showing buttons one per row, grouped.

    Each button gets a :attr:`~bacommon.docui.v2.ButtonRowLayout.FILL`
    row of its own, so it spans the column exactly as control rows do
    (its own width is ignored). Buttons within a group sit tight together;
    groups are separated by ``group_spacing`` (the first by
    ``first_group_spacing`` if given, for when the stack follows
    something that wants a different gap). For several buttons side by
    side, use such a row with several buttons directly.
    """
    rows: list[dui2.Row] = []
    for gindex, group in enumerate(groups):
        top = (
            first_group_spacing
            if gindex == 0 and first_group_spacing is not None
            else group_spacing
        )
        for i, button in enumerate(group):
            # (These numbers reproduce the button-row stacks this once
            # built, whose h-scroll lifted its content 6 units: 8/6
            # padding there is 2/12 here, and the -9 keeps a group's
            # buttons as tight as they were.)
            rows.append(
                dui2.ButtonRow(
                    layout=dui2.ButtonRowLayout.FILL,
                    spacing_top=top if i == 0 else -9.0,
                    padding_top=2.0,
                    padding_bottom=12.0,
                    buttons=[button],
                )
            )
    return rows
