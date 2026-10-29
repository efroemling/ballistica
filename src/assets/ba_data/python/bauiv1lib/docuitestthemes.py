# Released under the MIT License. See LICENSE for details.
#
"""Doc-ui test pages: page themes (the same content with various looks).

A page's look is a few flat values on the page itself
(:attr:`bacommon.docui.v2.Page.row_spacing`, ``h_inset``,
``button_color``, ``default_button_color``), plus the window frame's
colors, which come with the link that opens it
(:attr:`bacommon.docui.v2.Browse.background_color` and
``cancel_button_color``; the same on popups).
"""

from dataclasses import replace
from typing import TYPE_CHECKING, NamedTuple, assert_never

import bacommon.docui.v2 as dui2
import bacommon.docui.routes.docuitest as rt

from bauiv1lib.docuitestwidgets import _lit, style_for_size

if TYPE_CHECKING:
    import bacommon.docui.v2
    import bacommon.docui.routes.docuitest

type _Rgb = tuple[float, float, float]

_RED = (0.85, 0.25, 0.25)
_BLUE = (0.3, 0.45, 0.95)
_ORANGE = (0.9, 0.6, 0.15)

#: Every button's size here.
_SIZE = (150.0, 60.0)

#: A button color of its own, which no page value may change.
_OWN_COLOR = (0.62, 0.35, 0.75, 1.0)


class _Frame(NamedTuple):
    """A variant's link values: the window frame's colors."""

    background_color: _Rgb | None = None
    cancel_button_color: _Rgb | None = None


class _Look(NamedTuple):
    """A variant's page values."""

    h_inset: float | None = None
    v_inset: float | None = None
    row_spacing: float | None = None
    button_color: _Rgb | None = None
    default_button_color: _Rgb | None = None
    text: dui2.TextStyles | None = None


def test_page_themes(
    route: (
        bacommon.docui.routes.docuitest.Themes
        | bacommon.docui.routes.docuitest.ThemesPopup
    ),
) -> bacommon.docui.v2.Response:
    """The page-themes test pages: a window's and a popup's."""
    match route:
        case rt.Themes():
            return _page_window(route)
        case rt.ThemesPopup():
            return _page_popup(route)
        case _:
            assert_never(route)


def _variant_label(variant: rt.ThemeVariant) -> str:
    # pylint: disable=too-many-return-statements
    match variant:
        case rt.ThemeVariant.DEFAULT:
            return 'Default'
        case rt.ThemeVariant.POPUP_LOOK:
            return 'Popup Look'
        case rt.ThemeVariant.BUTTON_COLOR:
            return 'Button Color'
        case rt.ThemeVariant.ROLE_COLORS:
            return 'Role Colors'
        case rt.ThemeVariant.TIGHT:
            return 'Tight'
        case rt.ThemeVariant.ROOMY:
            return 'Roomy'
        case rt.ThemeVariant.DARK:
            return 'Dark'
        case rt.ThemeVariant.TEXT_STYLES:
            return 'Text Styles'
        case _:
            assert_never(variant)


def _variant_note(variant: rt.ThemeVariant, *, popup: bool) -> str:
    """What to look for in a variant."""
    # pylint: disable=too-many-return-statements
    match variant:
        case rt.ThemeVariant.DEFAULT:
            if popup:
                return (
                    'Sets nothing: a popup\'s green frame, but the usual'
                    ' spacing and buttons (a popup page wanting the'
                    ' popup look sets those itself; see Popup Look).'
                )
            return 'Sets nothing: the usual look.'
        case rt.ThemeVariant.POPUP_LOOK:
            return (
                'The popup look: the link sets the green frame, and the'
                ' page sets its button color, h_inset 20 and row'
                ' spacing 16 (the POPUP_* values in bacommon), plus a'
                ' v_inset of 0 (rows run right to the top and bottom'
                ' of the scroll area).'
            )
        case rt.ThemeVariant.BUTTON_COLOR:
            return (
                'The page sets an orange button color: plain buttons go'
                ' orange, Own Color keeps its purple and Default keeps'
                ' the default-button color.'
            )
        case rt.ThemeVariant.ROLE_COLORS:
            return (
                'The page sets a red default-button color and the link'
                ' a blue close/back button (a press of back/escape'
                ' presses it). Own Color keeps its purple; plain'
                ' buttons are as usual.'
            )
        case rt.ThemeVariant.TIGHT:
            return (
                'h_inset 12, 12 between rows (just room for a'
                ' scrolling row\'s bar). Text, the checkbox and button'
                ' rows all start 12 in; side fades shrink to match.'
            )
        case rt.ThemeVariant.ROOMY:
            return 'h_inset 60, 42 between rows.'
        case rt.ThemeVariant.DARK:
            return (
                'The link sets a dark frame with a matching close/back'
                ' button; the page sets matching button and'
                ' default-button colors.'
            )
        case rt.ThemeVariant.TEXT_STYLES:
            return (
                'The page sets default text looks (Page.text): warm'
                ' titles (sections\' too), subtitles, footnotes,'
                ' control labels and button labels. Anything that sets'
                ' its own text look keeps it.'
            )
        case _:
            assert_never(variant)


def _frame(variant: rt.ThemeVariant) -> _Frame:
    """The frame colors a variant's link (browse or popup) carries."""
    match variant:
        case (
            rt.ThemeVariant.DEFAULT
            | rt.ThemeVariant.BUTTON_COLOR
            | rt.ThemeVariant.TIGHT
            | rt.ThemeVariant.ROOMY
            | rt.ThemeVariant.TEXT_STYLES
        ):
            return _Frame()
        case rt.ThemeVariant.POPUP_LOOK:
            return _Frame(
                dui2.POPUP_BACKGROUND_COLOR, dui2.POPUP_BACKGROUND_COLOR
            )
        case rt.ThemeVariant.ROLE_COLORS:
            return _Frame(cancel_button_color=_BLUE)
        case rt.ThemeVariant.DARK:
            return _Frame((0.16, 0.16, 0.2), (0.5, 0.28, 0.3))
        case _:
            assert_never(variant)


def _look(variant: rt.ThemeVariant) -> _Look:
    """The look values a variant's page carries."""
    # pylint: disable=too-many-return-statements
    match variant:
        case rt.ThemeVariant.DEFAULT:
            return _Look()
        case rt.ThemeVariant.POPUP_LOOK:
            return _Look(
                h_inset=dui2.POPUP_H_INSET,
                # (No vertical inset: trying it out.)
                v_inset=0.0,
                row_spacing=dui2.POPUP_ROW_SPACING,
                button_color=dui2.POPUP_BUTTON_COLOR,
            )
        case rt.ThemeVariant.BUTTON_COLOR:
            return _Look(button_color=_ORANGE)
        case rt.ThemeVariant.ROLE_COLORS:
            return _Look(default_button_color=_RED)
        case rt.ThemeVariant.TIGHT:
            return _Look(h_inset=12.0, row_spacing=12.0)
        case rt.ThemeVariant.ROOMY:
            return _Look(h_inset=60.0, row_spacing=42.0)
        case rt.ThemeVariant.DARK:
            return _Look(
                button_color=(0.32, 0.32, 0.42),
                default_button_color=(0.25, 0.55, 0.4),
            )
        case rt.ThemeVariant.TEXT_STYLES:
            return _Look(
                text=dui2.TextStyles(
                    title=dui2.TextStyle(color=(1.0, 0.82, 0.4, 1.0)),
                    subtitle=dui2.TextStyle(color=(0.95, 0.7, 0.5, 1.0)),
                    footnote=dui2.TextStyle(
                        color=(0.85, 0.6, 0.5, 1.0), flatness=1.0
                    ),
                    label=dui2.TextStyle(
                        color=(1.0, 0.9, 0.6, 1.0), shadow=0.0
                    ),
                    button=dui2.TextStyle(
                        color=(1.0, 0.95, 0.75, 1.0), flatness=1.0
                    ),
                )
            )
        case _:
            assert_never(variant)


def _button(
    label: str,
    *,
    color: tuple[float, float, float, float] | None = None,
    default: bool = False,
) -> dui2.Button:
    return dui2.Button(
        label=_lit(label),
        size=_SIZE,
        style=style_for_size(_SIZE),
        color=color,
        default=default,
        action=dui2.Local(),
    )


def _sample_rows(
    variant: rt.ThemeVariant, *, popup: bool
) -> list[bacommon.docui.v2.Row]:
    """The content every variant shows."""
    return [
        dui2.TitleRow(_lit(_variant_label(variant))),
        dui2.SubtitleRow(_lit(_variant_note(variant, popup=popup))),
        dui2.ButtonRow(
            buttons=[
                _button('Plain'),
                _button('Own Color', color=_OWN_COLOR),
                _button('Default', default=True),
                _button('Plain'),
            ],
        ),
        rt.ThemesState.checkbox_row(
            lambda s: s.checked,
            label=_lit('A checkbox (its label starts at the h_inset)'),
        ),
        dui2.TitleRow(_lit('A fill row')),
        dui2.ButtonRow(
            layout=dui2.ButtonRowLayout.FILL,
            buttons=[_button('One'), _button('Two')],
        ),
        dui2.Section(
            title=_lit('A card'),
            backing=dui2.SectionBacking(
                color=(0.35, 0.55, 1.0, 0.3), content_inset=20.0
            ),
            rows=[
                dui2.ButtonRow(
                    layout=dui2.ButtonRowLayout.FILL,
                    buttons=[_button('Three'), _button('Four')],
                ),
            ],
        ),
    ]


def _page(
    variant: rt.ThemeVariant,
    *,
    title: str,
    state: rt.ThemesState,
    rows: list[bacommon.docui.v2.Row],
) -> bacommon.docui.v2.Page:
    """A page carrying a variant's look values."""
    return themed_page(
        dui2.Page(title=_lit(title), state=state.encode(), rows=rows),
        variant,
    )


def themed_page(
    page: bacommon.docui.v2.Page, variant: rt.ThemeVariant
) -> bacommon.docui.v2.Page:
    """A page with a theme's look values applied.

    Only the values the theme sets replace the page's own. (Its frame
    colors go on the link that opens it; see :func:`theme_frame`.)

    :meta private:
    """
    look = _look(variant)
    return replace(
        page,
        h_inset=page.h_inset if look.h_inset is None else look.h_inset,
        v_inset=page.v_inset if look.v_inset is None else look.v_inset,
        row_spacing=(
            page.row_spacing if look.row_spacing is None else look.row_spacing
        ),
        button_color=(
            page.button_color
            if look.button_color is None
            else look.button_color
        ),
        default_button_color=(
            page.default_button_color
            if look.default_button_color is None
            else look.default_button_color
        ),
        text=page.text if look.text is None else look.text,
    )


def theme_frame(
    variant: rt.ThemeVariant,
) -> tuple[_Rgb | None, _Rgb | None]:
    """A theme's frame colors, for the link opening a page in it.

    The ``background_color`` and ``cancel_button_color`` to give
    :meth:`~bacommon.docui.routes.DocUIRoute.browse`.

    :meta private:
    """
    frame = _frame(variant)
    return frame.background_color, frame.cancel_button_color


def theme_label(variant: rt.ThemeVariant) -> str:
    """A theme's name, for buttons picking it.

    :meta private:
    """
    return _variant_label(variant)


def _page_window(
    route: bacommon.docui.routes.docuitest.Themes,
) -> bacommon.docui.v2.Response:
    """The window page: links to every variant, then the sample.

    (Links first, so hopping between variants needs no scrolling.)
    """
    arrived = route.get_state(rt.ThemesState)
    state = rt.ThemesState() if arrived is None else arrived
    return dui2.Response(
        page=_page(
            route.variant,
            title='Page Themes',
            state=state,
            rows=[
                dui2.TitleRow(_lit('Open In A Window')),
                dui2.ButtonRow(
                    buttons=[
                        dui2.Button(
                            label=_lit(_variant_label(v)),
                            size=_SIZE,
                            style=style_for_size(_SIZE),
                            # (Fixed ids, for automation.)
                            widget_id=f'win_{v.value}',
                            # (The one we arrived by starts selected and
                            # in view, for hopping on from it.)
                            selected=v is route.variant,
                            # (Each takes this window's place rather than
                            # stacking up history: back always returns to
                            # wherever this page was opened from.)
                            action=rt.Themes(variant=v).browse(
                                background_color=_frame(v).background_color,
                                cancel_button_color=(
                                    _frame(v).cancel_button_color
                                ),
                                add_to_history=False,
                            ),
                        )
                        for v in rt.ThemeVariant
                    ],
                ),
                dui2.TitleRow(_lit('Open In A Popup')),
                dui2.SubtitleRow(
                    _lit(
                        'Popups get a green frame unless their link says'
                        ' otherwise; everything else is up to the page.'
                    )
                ),
                dui2.ButtonRow(
                    buttons=[
                        dui2.Button(
                            label=_lit(_variant_label(v)),
                            size=_SIZE,
                            style=style_for_size(_SIZE),
                            widget_id=f'pop_{v.value}',
                            action=rt.ThemesPopup(variant=v).popup(
                                background_color=_frame(v).background_color,
                                cancel_button_color=(
                                    _frame(v).cancel_button_color
                                ),
                            ),
                        )
                        for v in rt.ThemeVariant
                    ],
                ),
                *_sample_rows(route.variant, popup=False),
            ],
        ),
    )


def _page_popup(
    route: bacommon.docui.routes.docuitest.ThemesPopup,
) -> bacommon.docui.v2.Response:
    """The popup page: the sample, with the variant's look values."""
    arrived = route.get_state(rt.ThemesState)
    state = rt.ThemesState() if arrived is None else arrived
    return dui2.Response(
        page=_page(
            route.variant,
            title=f'Themes: {_variant_label(route.variant)}',
            state=state,
            rows=_sample_rows(route.variant, popup=True),
        ),
    )
