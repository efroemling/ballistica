# Released under the MIT License. See LICENSE for details.
#
"""The doc-ui sections test page.

:meta private:
"""

from typing import TYPE_CHECKING

import bacommon.docui.v2 as dui2
from bacommon.langstr import LangStrSpecValue
from bauiv1 import _uiv1assets

if TYPE_CHECKING:
    import bacommon.docui.routes.docuitest
    import bacommon.docui.v2


def _lit(text: str) -> LangStrSpecValue:
    # Dev-only page, so baked literals.
    return LangStrSpecValue.literal(text)


def _btn(label: str) -> bacommon.docui.v2.Button:
    """A do-nothing large button (for fill rows; equal widths)."""
    return dui2.Button(
        label=_lit(label),
        style=dui2.ButtonStyle.LARGE,
        size=(100.0, 60.0),
        action=dui2.Local(),
    )


def test_page_sections(
    route: bacommon.docui.routes.docuitest.Sections,
) -> bacommon.docui.v2.Response:
    """Sections: headings, notes, backings and the spacing around them.

    :meta private:
    """
    # pylint: disable=cyclic-import
    import bacommon.docui.routes.docuitest as rt

    debug = route.debug
    center = dui2.HAlign.CENTER

    def _fill(*labels: str) -> bacommon.docui.v2.ButtonRow:
        return dui2.ButtonRow(
            layout=dui2.ButtonRowLayout.FILL,
            buttons=[_btn(label) for label in labels],
            debug=debug,
        )

    # A flat translucent card the full column width, its content inset
    # as much as rows' already is from the column, so they lay out
    # exactly as they would without it.
    flat = dui2.SectionBacking(color=(0.35, 0.55, 1.0, 0.3), content_inset=37.0)

    # Inbox-message style: the slab the classic inbox draws, pinned so
    # its visible shape's edges land on the card's (and so on its
    # button rows' clipping), whatever width the card gets. (Pins are
    # where the texture's alpha reaches half; its soft shadow spills a
    # little past them.)
    slab = dui2.SectionBacking(
        texture=_uiv1assets.textures.button_square_wide,
        color=(0.42, 0.4, 0.6, 0.9),
        h_pin=(0.028, 0.032),
        v_pin=(0.074, 0.074),
        max_width=540.0,
        content_inset=24.0,
        padding_top=14.0,
        padding_bottom=14.0,
    )

    def _narrow(label: str, *, big: bool = False) -> bacommon.docui.v2.Row:
        """A lone narrow centered button, as inbox messages have."""
        return dui2.ButtonRow(
            layout=dui2.ButtonRowLayout.FIXED,
            content_align=dui2.HAlign.CENTER,
            debug=debug,
            buttons=[
                dui2.Button(
                    label=_lit(label),
                    size=(190, 56) if big else (180, 40),
                    label_scale=1.1 if big else 0.7,
                    label_color=(
                        (0.4, 1.0, 0.4, 1.0) if big else (0.6, 0.8, 0.7, 1.0)
                    ),
                    color=(0.45, 0.43, 0.6, 1.0),
                    action=dui2.Local(),
                )
            ],
        )

    return dui2.Response(
        page=dui2.Page(
            title=_lit('Sections'),
            rows=[
                # The simplest section: just a heading over its rows,
                # standing a little apart from what follows.
                dui2.Section(
                    title=_lit('A Plain Section'),
                    debug=debug,
                    rows=[_fill('One'), _fill('Two', 'Three')],
                ),
                # Every bit of text a section takes.
                dui2.Section(
                    title=_lit('Heading, Subtitle & Note'),
                    subtitle=_lit('A subtitle under the heading.'),
                    footnote=_lit('A note under the section\'s rows.'),
                    title_align=center,
                    debug=debug,
                    rows=[_fill('Four'), _fill('Five', 'Six')],
                ),
                # A flat backing, heading-less and unpadded: exactly the
                # union of its rows' bounds (toggle debug to compare).
                dui2.Section(
                    backing=flat,
                    debug=debug,
                    rows=[
                        _fill('Seven'),
                        dui2.ButtonRow(
                            layout=dui2.ButtonRowLayout.FILL,
                            title=_lit('A row title inside it'),
                            footnote=_lit('A row footnote inside it.'),
                            buttons=[_btn('Eight'), _btn('Nine')],
                            debug=debug,
                        ),
                    ],
                ),
                # Inbox-message prototypes: back-to-back slab cards,
                # their headings inside them.
                dui2.Section(
                    title=_lit('Check out this sweet link'),
                    title_align=center,
                    backing=slab,
                    debug=debug,
                    rows=[_narrow('Google'), _narrow('Ok', big=True)],
                ),
                dui2.Section(
                    title=_lit('I can has cheezburger?'),
                    title_align=center,
                    backing=slab,
                    debug=debug,
                    rows=[
                        dui2.ButtonRow(
                            layout=dui2.ButtonRowLayout.FILL,
                            buttons=[
                                dui2.Button(
                                    label=_lit('Decline'),
                                    style=dui2.ButtonStyle.LARGE,
                                    size=(100.0, 60.0),
                                    color=(0.6, 0.3, 0.45, 1.0),
                                    label_color=(1.0, 0.4, 0.4, 1.0),
                                    action=dui2.Local(),
                                ),
                                dui2.Button(
                                    label=_lit('Accept'),
                                    style=dui2.ButtonStyle.LARGE,
                                    size=(100.0, 60.0),
                                    color=(0.45, 0.43, 0.6, 1.0),
                                    label_color=(0.4, 1.0, 0.4, 1.0),
                                    action=dui2.Local(),
                                ),
                            ],
                            debug=debug,
                        )
                    ],
                ),
                # A long button row in a card clips at the card's (that
                # is, the slab's) edges.
                dui2.Section(
                    title=_lit('A long row clips at the card edge'),
                    title_align=center,
                    backing=slab,
                    debug=debug,
                    rows=[
                        dui2.ButtonRow(
                            buttons=[
                                dui2.Button(
                                    label=_lit(f'#{num}'),
                                    size=(110, 60),
                                    action=dui2.Local(),
                                )
                                for num in range(1, 11)
                            ],
                            debug=debug,
                        )
                    ],
                ),
                # Cards pulled edge to edge: sections normally stand 26
                # apart (the page's 10 row spacing plus a heading's 16
                # standoff above), so -26 has the slabs' solid edges
                # just touch.
                *[
                    dui2.Section(
                        title=_lit(f'Edge-to-edge card {num}'),
                        title_align=center,
                        backing=slab,
                        spacing_top=0.0 if num == 1 else -26.0,
                        debug=debug,
                        rows=[_narrow(f'Button {num}')],
                    )
                    for num in range(1, 4)
                ],
                # A plain row after a section stands apart from it.
                dui2.ButtonRow(
                    title=_lit('Plain rows after a section'),
                    center_content=True,
                    buttons=[
                        dui2.Button(
                            label=_lit('Hide Debug' if debug else 'Show Debug'),
                            size=(200, 60),
                            action=rt.Sections(debug=not debug).replace(),
                        ),
                    ],
                    debug=debug,
                ),
            ],
        )
    )
