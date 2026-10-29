# Released under the MIT License. See LICENSE for details.
#
"""A page's default text looks (``Page.text``) in doc-ui prep.

Applied once, up front, by filling each element's unset style fields
(a row's ``title_color``, a button's ``label_flatness``, ...) from the
page's :class:`~bacommon.docui.v2.TextStyles`; everything after just
reads the element's own fields as before, falling back to the usual
looks where both are unset. So for any text: its own value, else the
page's, else the usual.
"""

from dataclasses import replace
from typing import TYPE_CHECKING

import bacommon.docui.v2 as dui2

if TYPE_CHECKING:
    from bauiv1lib.docui.prep._controlrows import ColumnRow


def _fill(
    obj: object, prefix: str, style: dui2.TextStyle | None, *, shadow: bool
) -> dict:
    """Kwargs filling ``obj``'s unset ``<prefix>_*`` style fields."""
    if style is None:
        return {}
    out: dict = {}
    pairs = [('color', style.color), ('flatness', style.flatness)]
    if shadow:
        pairs.append(('shadow', style.shadow))
    for name, val in pairs:
        field = f'{prefix}_{name}'
        if val is not None and getattr(obj, field) is None:
            out[field] = val
    return out


def _texts(obj: object, styles: dui2.TextStyles) -> dict:
    """Kwargs filling a row's title/subtitle/footnote.

    (Headings, a section's included, are rows here too: they take the
    page's title look.)
    """
    return {
        **_fill(obj, 'title', styles.title, shadow=True),
        **_fill(obj, 'subtitle', styles.subtitle, shadow=True),
        **_fill(obj, 'footnote', styles.footnote, shadow=True),
    }


def styled_button(
    button: dui2.Button, styles: dui2.TextStyles | None
) -> dui2.Button:
    """A button with the page's label look filled in.

    :meta private:
    """
    if styles is None:
        return button
    kwargs = _fill(button, 'label', styles.button, shadow=False)
    return replace(button, **kwargs) if kwargs else button


def styled_row(row: ColumnRow, styles: dui2.TextStyles | None) -> ColumnRow:
    """A row with the page's text looks filled in (buttons included).

    :meta private:
    """
    if styles is None:
        return row
    kwargs = _texts(row, styles)
    if isinstance(row, dui2.ButtonRow):
        kwargs['buttons'] = [styled_button(b, styles) for b in row.buttons]
    else:
        kwargs.update(_fill(row, 'label', styles.label, shadow=True))
        if isinstance(row, dui2.ButtonControlRow):
            kwargs['button'] = styled_button(row.button, styles)
    return replace(row, **kwargs)
