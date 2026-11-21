# Released under the MIT License. See LICENSE for details.
#
"""Fill- and fixed-row demos for the doc-ui widgets test page."""

from dataclasses import replace

from bacommon.langstr import LangStrSpecValue
import bacommon.docui.v2 as dui2


def _lit(text: str) -> LangStrSpecValue:
    # A dev-only page, so baked literals throughout.
    return LangStrSpecValue.literal(text)


def style_for_square(size: tuple[float, float]) -> dui2.ButtonStyle:
    """Square backing for squarish buttons; medium for wide ones.

    :meta private:
    """
    return (
        dui2.ButtonStyle.SQUARE
        if size[0] <= size[1] * 1.5
        else dui2.ButtonStyle.MEDIUM
    )


def _fill_button(label: str, width: float = 100.0) -> dui2.Button:
    """A button for fill-row demos (a do-nothing large one).

    Its width only matters relative to its row-mates'.
    """
    return dui2.Button(
        label=_lit(label),
        style=dui2.ButtonStyle.LARGE,
        size=(width, 60.0),
        action=dui2.Local(),
    )


def _fixed_button(
    label: str, size: tuple[float, float] = (150.0, 50.0)
) -> dui2.Button:
    """A do-nothing button at its own size, for fixed-row demos."""
    return dui2.Button(
        label=_lit(label),
        size=size,
        style=style_for_square(size),
        action=dui2.Local(),
    )


def fill_and_fixed_rows(debug: bool) -> list[dui2.Row]:
    """The widgets page's fill-row and fixed-row demos.

    :meta private:
    """
    return [
        # Fill rows: one or more buttons sharing the full width
        # control rows span, so their edges line up with the
        # labels and controls above and below. They never scroll
        # sideways (nothing clips).
        dui2.TitleRow(_lit('Fill Rows')),
        dui2.ButtonRow(
            layout=dui2.ButtonRowLayout.FILL,
            buttons=[_fill_button('One Button')],
            debug=debug,
        ),
        dui2.ButtonRow(
            layout=dui2.ButtonRowLayout.FILL,
            buttons=[_fill_button('Left'), _fill_button('Right')],
            debug=debug,
        ),
        dui2.ButtonRow(
            layout=dui2.ButtonRowLayout.FILL,
            buttons=[
                _fill_button('One'),
                _fill_button('Two'),
                _fill_button('Three'),
            ],
            debug=debug,
        ),
        dui2.FootnoteRow(_lit('Fill-row footnote.')),
        # Widths share the row in proportion to the buttons' own.
        dui2.ButtonRow(
            layout=dui2.ButtonRowLayout.FILL,
            buttons=[
                _fill_button('1x'),
                _fill_button('2x', width=200.0),
            ],
            debug=debug,
        ),
        dui2.FootnoteRow(_lit('Sized 100 and 200: a 1:2 split.')),
        # All the text a fill row takes, between plain ones, to
        # judge its spacing against its neighbors.
        dui2.ButtonRow(
            layout=dui2.ButtonRowLayout.FILL,
            buttons=[_fill_button('Plain Above')],
            debug=debug,
        ),
        dui2.TitleRow(_lit('Titled Fill Row')),
        dui2.SubtitleRow(_lit('With a subtitle under its title')),
        dui2.ButtonRow(
            layout=dui2.ButtonRowLayout.FILL,
            buttons=[_fill_button('A'), _fill_button('B')],
            debug=debug,
        ),
        dui2.FootnoteRow(_lit('And a footnote under its buttons.')),
        dui2.ButtonRow(
            layout=dui2.ButtonRowLayout.FILL,
            buttons=[_fill_button('Plain Below')],
            debug=debug,
        ),
        # Row entry: arrowing into a row lands on its row_selected
        # button rather than its first (a dialog's Save, say).
        dui2.TitleRow(_lit('Row Entry Selection')),
        dui2.SubtitleRow(
            _lit('Arrow into these: selection lands on the flagged button')
        ),
        dui2.ButtonRow(
            layout=dui2.ButtonRowLayout.FILL,
            buttons=[
                _fill_button('Cancel'),
                replace(_fill_button('Save (row_selected)'), row_selected=True),
            ],
            debug=debug,
        ),
        dui2.ButtonRow(
            buttons=[
                (
                    replace(_fixed_button(f'#{num} (entry)'), row_selected=True)
                    if num == 4
                    else _fixed_button(f'#{num}')
                )
                for num in range(1, 9)
            ],
            debug=debug,
        ),
        dui2.FootnoteRow(
            _lit(
                'A scrolling row starts on its flagged button, then'
                ' remembers the last one selected in it.'
            )
        ),
        # Fixed rows: buttons at their own sizes, straight on
        # the page (nothing clips), aligned like a scrolling
        # row's. First the same buttons both ways: they should
        # land in the same place.
        dui2.TitleRow(_lit('Fixed Rows')),
        dui2.SubtitleRow(_lit('A scrolling row, then a fixed one')),
        dui2.ButtonRow(
            buttons=[_fixed_button('Alpha'), _fixed_button('Beta')],
            debug=debug,
        ),
        dui2.ButtonRow(
            layout=dui2.ButtonRowLayout.FIXED,
            buttons=[_fixed_button('Alpha'), _fixed_button('Beta')],
            debug=debug,
        ),
        dui2.ButtonRow(
            layout=dui2.ButtonRowLayout.FIXED,
            content_align=dui2.HAlign.CENTER,
            buttons=[_fixed_button('Centered', (180.0, 40.0))],
            debug=debug,
        ),
        dui2.ButtonRow(
            layout=dui2.ButtonRowLayout.FIXED,
            content_align=dui2.HAlign.RIGHT,
            buttons=[
                _fixed_button('Right', (120.0, 40.0)),
                _fixed_button('Aligned', (120.0, 40.0)),
            ],
            debug=debug,
        ),
        # Mixed heights center on the tallest.
        dui2.ButtonRow(
            layout=dui2.ButtonRowLayout.FIXED,
            content_align=dui2.HAlign.CENTER,
            buttons=[
                _fixed_button('Short', (120.0, 35.0)),
                _fixed_button('Tall', (120.0, 80.0)),
                _fixed_button('Short', (120.0, 35.0)),
            ],
            debug=debug,
        ),
        # Too many to fit: they all shrink together.
        dui2.ButtonRow(
            layout=dui2.ButtonRowLayout.FIXED,
            buttons=[_fixed_button(f'#{num}') for num in range(1, 9)],
            debug=debug,
        ),
        dui2.FootnoteRow(_lit('Eight 150-wide buttons, shrunk to fit.')),
        # One button wider than any layout: it shrinks alone.
        dui2.ButtonRow(
            layout=dui2.ButtonRowLayout.FIXED,
            buttons=[_fixed_button('Too Wide', (2000.0, 120.0))],
            debug=debug,
        ),
        dui2.FootnoteRow(_lit('One 2000x120 button, shrunk to fit.')),
        # Content offset: the group shifts from the row's center
        # -- the same point band decorations are placed from --
        # so a button lines up under band art at the same x
        # whatever the layout's width or insets.
        dui2.HeaderRow(
            40.0,
            decorations_center=[
                dui2.Text(
                    text=_lit('x=-200'),
                    position=(-200.0, 9.0),
                    size=(150.0, 20.0),
                    scale=0.6,
                    color=(1.0, 1.0, 1.0, 0.5),
                    debug=debug,
                ),
                dui2.Text(
                    text=_lit('▼'),
                    position=(-200.0, -9.0),
                    size=(30.0, 20.0),
                    scale=0.7,
                    color=(1.0, 1.0, 1.0, 0.5),
                    debug=debug,
                ),
            ],
        ),
        dui2.ButtonRow(
            layout=dui2.ButtonRowLayout.FIXED,
            center_content=True,
            content_offset=-200.0,
            buttons=[_fixed_button('Offset -200', (180.0, 40.0))],
            debug=debug,
        ),
        dui2.FootnoteRow(
            _lit('content_offset=-200: centered under band art at x=-200.')
        ),
        dui2.ButtonRow(
            layout=dui2.ButtonRowLayout.FIXED,
            center_content=True,
            content_offset=150.0,
            buttons=[
                _fixed_button('Group', (120.0, 40.0)),
                _fixed_button('Shifted', (120.0, 40.0)),
            ],
            debug=debug,
        ),
        dui2.FootnoteRow(
            _lit(
                'Two buttons, content_offset=150: they move as a'
                ' group, spacing unchanged.'
            )
        ),
        dui2.ButtonRow(
            layout=dui2.ButtonRowLayout.FIXED,
            center_content=True,
            content_offset=5000.0,
            buttons=[_fixed_button('Clamped', (150.0, 40.0))],
            debug=debug,
        ),
        dui2.FootnoteRow(
            _lit(
                'content_offset=5000: slides back in at the'
                ' right edge rather than leaving the row.'
            )
        ),
    ]
