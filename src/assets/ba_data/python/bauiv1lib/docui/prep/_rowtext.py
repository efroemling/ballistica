# Released under the MIT License. See LICENSE for details.
#
"""Prep for the text every doc-ui row can carry: titles and footnotes.

A row's title/subtitle sit above its content and its footnote below;
all row types share these, so they are laid out here once and the
row-specific prep in :mod:`bauiv1lib.docui.prep._calls` and
:mod:`bauiv1lib.docui.prep._controlrows` places its content between
them.
"""

from dataclasses import replace
from functools import partial
from typing import TYPE_CHECKING, assert_never

from bacommon.langstr import LangStrSpecValue
import bacommon.docui.v2 as dui2
import bauiv1 as bui

from bauiv1lib.docui.prep._types import NO_WRAP

if TYPE_CHECKING:
    from bacommon.langstr import LangStrSpec

    from bauiv1lib.docui.prep._types import NativeLangStrFn, RowPrep

#: Row types carrying a title/subtitle/footnote (all of them, at
#: present).
type TitledRow = dui2.ButtonRow | dui2.AnyControlRow


#: Row title text scale. The title's reserved space (its strip heights
#: and its spacing from a control row's label) scales along with it.
_ROW_TITLE_SCALE = 1.15

#: Row subtitle and footnote text scale.
_ROW_SUBTITLE_SCALE = 0.7

#: Row title flatness and shadow when a row doesn't specify them (half
#: flat, full shadow; labels and button text use text-widget defaults
#: of fully shaded, half shadow).
_ROW_TITLE_FLATNESS = 0.5
_ROW_TITLE_SHADOW = 1.0

# Vertical space a row's title/subtitle take: a single-line strip,
# plus this much per additional line of text (title at
# _ROW_TITLE_SCALE, subtitle at _ROW_SUBTITLE_SCALE). A title alone
# sits a bit lower than one with a subtitle under it.
_ROW_TITLE_HEIGHT_WITH_SUBTITLE = 30.0 * _ROW_TITLE_SCALE
_ROW_TITLE_HEIGHT_NO_SUBTITLE = 38.0 * _ROW_TITLE_SCALE
_ROW_TITLE_LINE_HEIGHT = 30.0 * _ROW_TITLE_SCALE
_ROW_SUBTITLE_HEIGHT = 30.0
_ROW_SUBTITLE_LINE_HEIGHT = 22.0

#: A footnote is a subtitle on the bottom of its row: same scale,
#: color and per-line height. Its strip is the text's lines plus this
#: much padding *below*; the text hugs the top of the strip so it
#: reads as part of its own row rather than the next one -- the mirror
#: of a subtitle, which hugs the content below it.
_ROW_FOOTNOTE_PADDING_BOTTOM = 10.0

#: How far (center to center) a control row's label sits from the
#: nearest line of its subtitle above or footnote below: the same as a
#: subtitle from its title, so the row reads as one unit. The strips
#: alone would leave it 40-44 away.
_CONTROL_LABEL_TEXT_SPACING = 30.0

#: The same for a title directly above the label (no subtitle): a bit
#: more, as both are full-size text (the title larger still), so the
#: gap between their glyphs matches the others'. The strips alone
#: would leave it about 60 away.
_CONTROL_LABEL_TITLE_SPACING = 34.0 * _ROW_TITLE_SCALE

# From the last line of a title/subtitle strip to the strip's bottom
# (the same whatever the line count; see prep_row_titles()), and from
# a footnote strip's top to its first line.
_TITLE_LAST_LINE_TO_BOTTOM = _ROW_TITLE_HEIGHT_NO_SUBTITLE - (
    _ROW_TITLE_HEIGHT_WITH_SUBTITLE * 0.5
)
_SUBTITLE_LAST_LINE_TO_BOTTOM = _ROW_SUBTITLE_HEIGHT * 0.5
_FOOTNOTE_TOP_TO_FIRST_LINE = _ROW_SUBTITLE_LINE_HEIGHT * 0.5


#: Time-varying texts already warned about in wrapped fields (see
#: :func:`wrapped_text`), so each warns once per run.
_warned_live_texts: set[str] = set()


def wrapped_text(
    text: LangStrSpec,
    *,
    maxwidth: float,
    scale: float,
    native: NativeLangStrFn,
    where: str,
) -> LangStrSpec:
    """Word-wrap a row/section text to fit its column.

    Evaluates in the current language ignoring the string's own
    line-wrapping hints (we wrap it here instead; the two would
    compound) and wraps to ``maxwidth`` at ``scale``, the text widget's
    own values, so it never needs to shrink. Wrapped text comes back
    as a literal, with no hints of its own. Time-varying text
    (countdowns and such) can't be wrapped once up front, so it comes
    back as-is, with a once-per-text warning naming ``where`` it is;
    it still carries its hints then, so callers must display (and
    measure) results with ``wrap=NO_WRAP``, which leaves it a single
    line, squished to fit. Measures text, so call from a background
    thread (as prep runs).

    :meta private:
    """
    flat, until_change = native(text).evaluate_timed(wrap=False)
    if until_change is not None:
        if flat not in _warned_live_texts:
            _warned_live_texts.add(flat)
            bui.uilog.warning(
                'Doc-ui %s holds time-varying text (%r); wrapping skipped.'
                ' Wrapped fields (titles, subtitles, footnotes, popup'
                ' text) want text that stays put.',
                where,
                flat,
            )
        return text
    return LangStrSpecValue.literal(bui.wrap_text(flat, maxwidth, scale))


def wrap_row_texts(
    row: TitledRow,
    *,
    width: float,
    margins: tuple[float, float, float, float],
    buffers: tuple[float, float],
    header_insets: tuple[float, float],
    center: tuple[float, float],
    native: NativeLangStrFn,
    where: str,
) -> TitledRow:
    """A copy of a row with its title/subtitle/footnote wrapped.

    Each is wrapped to the width and scale its text widget gets (see
    :func:`prep_row_titles` and :func:`prep_row_footnote`, which take
    the same geometry), so everything downstream -- strip heights,
    reach checks, the widgets -- just sees text with more lines. The
    row itself (likely shared with a cached page) is left alone.

    :meta private:
    """
    if row.title is None and row.subtitle is None and row.footnote is None:
        return row
    _x, maxwidth = row_text_x_and_maxwidth(
        row_title_align(row),
        width=width,
        margins=margins,
        buffers=buffers,
        header_insets=header_insets,
        center=center,
    )

    def _wrap(
        text: LangStrSpec | int | None, scale: float, field: str
    ) -> LangStrSpec | int | None:
        # (Indices are unfolded before prep; native() rejects any that
        # aren't, so leave that to it.)
        if text is None or isinstance(text, int):
            return text
        return wrapped_text(
            text,
            maxwidth=maxwidth,
            scale=scale,
            native=native,
            where=f'{where} {field}',
        )

    return replace(
        row,
        title=_wrap(row.title, _ROW_TITLE_SCALE, 'title'),
        subtitle=_wrap(row.subtitle, _ROW_SUBTITLE_SCALE, 'subtitle'),
        footnote=_wrap(row.footnote, _ROW_SUBTITLE_SCALE, 'footnote'),
    )


def control_width(
    avail: float, *, label_want: float, control_want: float
) -> float:
    """How wide a control row's control gets beside its label.

    ``avail`` is the row's width less the label gap; the label gets
    whatever the control doesn't. Each side gets its natural (wanted)
    width if both fit; otherwise neither is squeezed below half the
    space unless it wants less, and whatever one side doesn't need goes
    to the other -- so a long label and a long control split it evenly.

    :meta private:
    """
    return max(0.0, min(control_want, max(avail * 0.5, avail - label_want)))


def label_want_width(label: bui.LangStr | None) -> float:
    """A row label's natural width (0 with no label).

    Measures text, so call from a background thread (as prep runs).

    :meta private:
    """
    if label is None:
        return 0.0
    return bui.get_string_width(label.evaluate(), suppress_warning=True)


def line_count(text: LangStrSpec | int, native: NativeLangStrFn) -> int:
    """How many lines a row text renders as.

    Only line breaks in the text count; the widgets never wrap on
    their own, but prep wraps row and section text to its column up
    front (see :func:`wrap_row_texts`), so those breaks are already
    in it. Evaluated in the current language; a switch re-renders the
    page, so strips follow the text.

    :meta private:
    """
    return native(text, wrap=NO_WRAP).evaluate().count('\n') + 1


def _row_title_height(row: TitledRow, native: NativeLangStrFn) -> float:
    """Vertical space a row's title takes (0 for none)."""
    if row.title is None:
        return 0.0
    base = (
        _ROW_TITLE_HEIGHT_NO_SUBTITLE
        if row.subtitle is None
        else _ROW_TITLE_HEIGHT_WITH_SUBTITLE
    )
    return base + _ROW_TITLE_LINE_HEIGHT * (line_count(row.title, native) - 1)


def _row_subtitle_height(row: TitledRow, native: NativeLangStrFn) -> float:
    """Vertical space a row's subtitle takes (0 for none)."""
    if row.subtitle is None:
        return 0.0
    return _ROW_SUBTITLE_HEIGHT + _ROW_SUBTITLE_LINE_HEIGHT * (
        line_count(row.subtitle, native) - 1
    )


def row_footnote_height(row: TitledRow, native: NativeLangStrFn) -> float:
    """Vertical space a row's footnote takes (0 for none).

    Grows with the text's line count like the title and subtitle do
    (see :func:`row_titles_height`).

    :meta private:
    """
    if row.footnote is None:
        return 0.0
    return (
        _row_footnote_spacing(row)
        + _ROW_SUBTITLE_LINE_HEIGHT * line_count(row.footnote, native)
        + _ROW_FOOTNOTE_PADDING_BOTTOM
    )


def _row_footnote_spacing(row: TitledRow) -> float:
    """The gap between a row's content and its footnote (0 with none).

    The footnote's counterpart to ``_row_title_spacing()``: it sits at
    the top of the footnote strip, so a control row's tuck (which
    measures from the strip's top) leaves it intact on top of the
    usual label spacing.
    """
    if row.footnote is None:
        return 0.0
    return row.spacing_footnote


def control_row_titles_tuck(row: TitledRow, label_from_top: float) -> float:
    """How far a control row's control pulls up into its title strips.

    ``label_from_top`` is how far below the control area's top its
    label's center sits. The result brings the label to
    ``_CONTROL_LABEL_TEXT_SPACING`` from a subtitle's last line, or
    ``_CONTROL_LABEL_TITLE_SPACING`` from a title's (0 with neither).

    :meta private:
    """
    if row.subtitle is not None:
        above = _SUBTITLE_LAST_LINE_TO_BOTTOM
        spacing = _CONTROL_LABEL_TEXT_SPACING
    elif row.title is not None:
        above = _TITLE_LAST_LINE_TO_BOTTOM
        spacing = _CONTROL_LABEL_TITLE_SPACING
    else:
        return 0.0
    return max(0.0, above + label_from_top - spacing)


def control_row_footnote_tuck(
    row: TitledRow, label_from_bottom: float
) -> float:
    """How far a control row's footnote pulls up toward its control.

    ``label_from_bottom`` is how far above the control area's bottom
    its label's center sits. The result brings the footnote's first
    line to ``_CONTROL_LABEL_TEXT_SPACING`` from the label (0 with no
    footnote).

    :meta private:
    """
    if row.footnote is None:
        return 0.0
    return max(
        0.0,
        label_from_bottom
        + _FOOTNOTE_TOP_TO_FIRST_LINE
        - _CONTROL_LABEL_TEXT_SPACING,
    )


def row_text_reaches(
    row: TitledRow,
    text: LangStrSpec | int | None,
    scale: float,
    *,
    left: float,
    limit: float,
    native: NativeLangStrFn,
) -> bool:
    """Whether a row's title/subtitle/footnote text reaches ``limit``.

    Text that isn't left-aligned always counts (it sits at or toward
    the row's right); left-aligned text starts at ``left`` (where
    titles line up with labels) and counts if its widest line runs
    past ``limit``. Over-long text squishes to fit rather than
    reaching further, but by then it spans the row anyway. Measures
    text, so call from a background thread (as prep runs).

    :meta private:
    """
    if text is None:
        return False
    if row_title_align(row) is not dui2.HAlign.LEFT:
        return True
    textwidth = bui.get_string_width(
        native(text, wrap=NO_WRAP).evaluate(), suppress_warning=True
    )
    return left + scale * textwidth > limit


def titles_clear_rise(
    row: TitledRow,
    *,
    left: float,
    limit: float,
    clearance: float,
    native: NativeLangStrFn,
) -> float:
    """How far up into a row's titles something beside them can reach.

    For a control at the row's right, from ``limit`` on, that is taller
    than the row's label: measured up from the bottom of the titles
    (:func:`row_titles_height` of them), this is how far it can rise
    before it runs into title or subtitle text. It can sit beside text
    that stops short of it, all the way to the top of the titles, and
    stays ``clearance`` short of text that does not (strips keep some
    spare room around their text, which counts toward it).

    :meta private:
    """
    spacing = _row_title_spacing(row)
    if row_text_reaches(
        row,
        row.subtitle,
        _ROW_SUBTITLE_SCALE,
        left=left,
        limit=limit,
        native=native,
    ):
        return spacing - clearance
    if row_text_reaches(
        row,
        row.title,
        _ROW_TITLE_SCALE,
        left=left,
        limit=limit,
        native=native,
    ):
        return spacing + _row_subtitle_height(row, native) - clearance
    return row_titles_height(row, native)


def footnote_clear_drop(
    row: TitledRow,
    *,
    left: float,
    limit: float,
    clearance: float,
    native: NativeLangStrFn,
) -> float:
    """How far down into a row's footnote something beside it can reach.

    The footnote's answer to :func:`titles_clear_rise`, measured down
    from the top of its strip.

    :meta private:
    """
    if row_text_reaches(
        row,
        row.footnote,
        _ROW_SUBTITLE_SCALE,
        left=left,
        limit=limit,
        native=native,
    ):
        return _row_footnote_spacing(row) - clearance
    return row_footnote_height(row, native)


def prep_row_footnote(
    row: TitledRow,
    rowprep: RowPrep,
    *,
    y: float,
    width: float,
    margins: tuple[float, float, float, float],
    buffers: tuple[float, float],
    header_insets: tuple[float, float],
    center: tuple[float, float],
    tdelaybase: float | None,
    tscale: float = 1.0,
    native: NativeLangStrFn,
) -> None:
    """Prep a row's footnote text (if any) in the strip above ``y``.

    Shared by every row type, like :func:`prep_row_titles`; the strip
    is :func:`row_footnote_height` tall and the row's height already
    includes it.

    :meta private:
    """
    if row.footnote is None:
        return
    title_align = row_title_align(row)
    title_x, maxwidth = row_text_x_and_maxwidth(
        title_align,
        width=width,
        margins=margins,
        buffers=buffers,
        header_insets=header_insets,
        center=center,
    )
    # The text block sits just under the row's footnote spacing at the
    # top of the strip; the padding sits below it (see
    # _ROW_FOOTNOTE_PADDING_BOTTOM).
    text_top = y + row_footnote_height(row, native) - _row_footnote_spacing(row)
    text_height = _ROW_SUBTITLE_LINE_HEIGHT * line_count(row.footnote, native)
    rowprep.titlecalls.append(
        partial(
            bui.textwidget,
            position=(title_x, text_top - text_height * 0.5),
            size=(0, 0),
            text=native(row.footnote, wrap=NO_WRAP),
            color=(
                (0.6, 0.74, 0.6)
                if row.footnote_color is None
                else row.footnote_color
            ),
            flatness=row.footnote_flatness,
            shadow=row.footnote_shadow,
            scale=_ROW_SUBTITLE_SCALE,
            maxwidth=max(1.0, maxwidth),
            h_align=title_align.name.lower(),
            v_align='center',
            literal=True,
            transition_delay=(
                None if tdelaybase is None else (tdelaybase + 0.1 * tscale)
            ),
            transition_type='scale',
        )
    )


def row_titles_height(row: TitledRow, native: NativeLangStrFn) -> float:
    """Total vertical space a row's title + subtitle take (0 for none).

    Each grows with its text's line breaks (including those prep's
    wrapping added; see :func:`line_count`), evaluated in the current
    language. A language switch re-renders the page, so
    the strips follow the text. Includes the row's ``spacing_title``
    gap below them when there is either.

    :meta private:
    """
    height = _row_title_height(row, native) + _row_subtitle_height(row, native)
    return height + _row_title_spacing(row)


def _row_title_spacing(row: TitledRow) -> float:
    """The gap between a row's titles and its content (0 with none).

    It sits below the title/subtitle strips, so a control row's tuck
    (which measures from the strips) leaves it intact on top of the
    usual label spacing.
    """
    if row.title is None and row.subtitle is None:
        return 0.0
    return row.spacing_title


def row_title_align(row: TitledRow) -> dui2.HAlign:
    """A row's effective title alignment.

    An explicit ``title_align`` wins; otherwise a ButtonRow's legacy
    ``center_title`` flag applies. Footnotes follow it too.

    :meta private:
    """
    if row.title_align is not None:
        return row.title_align
    if isinstance(row, dui2.ButtonRow) and row.center_title:
        return dui2.HAlign.CENTER
    return dui2.HAlign.LEFT


def prep_row_titles(
    row: TitledRow,
    rowprep: RowPrep,
    *,
    y: float,
    width: float,
    margins: tuple[float, float, float, float],
    buffers: tuple[float, float],
    header_insets: tuple[float, float],
    center: tuple[float, float],
    tdelaybase: float | None,
    tscale: float = 1.0,
    native: NativeLangStrFn,
) -> float:
    """Prep a row's title/subtitle text (if any); return the new y.

    Shared by every row type that carries titles.

    :meta private:
    """
    title_align = row_title_align(row)
    title_x, maxwidth = row_text_x_and_maxwidth(
        title_align,
        width=width,
        margins=margins,
        buffers=buffers,
        header_insets=header_insets,
        center=center,
    )
    h_align = title_align.name.lower()

    if row.title is not None:
        # The text sits centered in the strip's top 30 units per line;
        # a title with no subtitle keeps its spare 8 below it.
        title_height = _row_title_height(row, native)
        text_height = (
            _ROW_TITLE_HEIGHT_WITH_SUBTITLE
            + _ROW_TITLE_LINE_HEIGHT * (line_count(row.title, native) - 1)
        )
        rowprep.titlecalls.append(
            partial(
                bui.textwidget,
                position=(title_x, y - text_height * 0.5),
                size=(0, 0),
                text=native(row.title, wrap=NO_WRAP),
                # A touch brighter and bigger than control-row labels and
                # button text, so titles read as headings over them.
                color=(
                    (0.95, 1.0, 0.97, 1.0)
                    if row.title_color is None
                    else row.title_color
                ),
                flatness=(
                    _ROW_TITLE_FLATNESS
                    if row.title_flatness is None
                    else row.title_flatness
                ),
                shadow=(
                    _ROW_TITLE_SHADOW
                    if row.title_shadow is None
                    else row.title_shadow
                ),
                scale=_ROW_TITLE_SCALE,
                maxwidth=maxwidth,
                h_align=h_align,
                v_align='center',
                literal=True,
                transition_delay=(
                    None if tdelaybase is None else (tdelaybase + 0.1 * tscale)
                ),
                transition_type='scale',
            )
        )
        y -= title_height
    if row.subtitle is not None:
        subtitle_height = _row_subtitle_height(row, native)
        rowprep.titlecalls.append(
            partial(
                bui.textwidget,
                position=(title_x, y - subtitle_height * 0.5),
                size=(0, 0),
                text=native(row.subtitle, wrap=NO_WRAP),
                color=(
                    (0.6, 0.74, 0.6)
                    if row.subtitle_color is None
                    else row.subtitle_color
                ),
                flatness=row.subtitle_flatness,
                shadow=row.subtitle_shadow,
                scale=_ROW_SUBTITLE_SCALE,
                maxwidth=maxwidth,
                h_align=h_align,
                v_align='center',
                literal=True,
                transition_delay=(
                    None if tdelaybase is None else (tdelaybase + 0.2 * tscale)
                ),
                transition_type='scale',
            )
        )
        y -= subtitle_height
    return y - _row_title_spacing(row)


def row_text_x_and_maxwidth(
    align: dui2.HAlign,
    *,
    width: float,
    margins: tuple[float, float, float, float],
    buffers: tuple[float, float],
    header_insets: tuple[float, float],
    center: tuple[float, float],
) -> tuple[float, float]:
    """X position and max width for a row's text given its alignment.

    Left- and right-aligned text sits in from the margins; centered
    text goes where ``center`` (x, maxwidth) says: the middle of the
    page's column, or of a card's.

    :meta private:
    """
    margin_left, margin_right = margins[0], margins[1]
    left_buffer, right_buffer = buffers
    header_inset_left, header_inset_right = header_insets
    maxwidth = (
        width
        - margin_left
        - margin_right
        - left_buffer
        - right_buffer
        - header_inset_left
        - header_inset_right
    )
    if align is dui2.HAlign.LEFT:
        return margin_left + left_buffer + header_inset_left, max(1.0, maxwidth)
    if align is dui2.HAlign.CENTER:
        return center[0], max(1.0, center[1])
    if align is dui2.HAlign.RIGHT:
        # (Measured against debug bounds, this sits right-aligned
        # titles as far in from their buttons' edge as left-aligned
        # ones are from theirs: ~20 units.)
        return (
            width - margin_right - right_buffer - header_inset_right,
            max(1.0, maxwidth),
        )
    assert_never(align)
