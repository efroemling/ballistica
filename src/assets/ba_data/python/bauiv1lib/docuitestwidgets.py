# Released under the MIT License. See LICENSE for details.
#
"""Doc-ui test page for control rows and page state."""

from dataclasses import replace
from typing import TYPE_CHECKING, assert_never

from bacommon.langstr import LangStrSpecValue
import bacommon.docui.v2 as dui2
from bauiv1 import _commonassets

from bauiv1lib.docuitestbuttonrows import (
    fill_and_fixed_rows,
    style_for_square,
)

if TYPE_CHECKING:
    import bacommon.docui.v2
    import bacommon.docui.routes.docuitest


_POPUP_SHORT = 'Popup text explains things; this is popup text.'
_POPUP_LONG = (
    'A longer bit of popup text, to show that it wraps. The popup sizes'
    ' itself to whatever its text needs, up to a maximum width, past'
    ' which the text wraps onto more lines and the popup grows taller'
    ' instead.\n\nExplicit line breaks work too.'
)


def _lit(text: str) -> LangStrSpecValue:
    # A dev-only page, so baked literals throughout.
    return LangStrSpecValue.literal(text)


def style_for_size(size: tuple[float, float]) -> dui2.ButtonStyle:
    """A button style whose art suits a button of this size.

    Square art looks stretched on wide buttons, so anything over 1.5x
    as wide as tall gets wider art: medium up to 3.5x, large past
    that.
    """
    width, height = size
    aspect = width / max(1.0, height)
    if aspect <= 1.5:
        return dui2.ButtonStyle.SQUARE
    if aspect <= 3.5:
        return dui2.ButtonStyle.MEDIUM
    return dui2.ButtonStyle.LARGE


def _flavor_label(
    flavor: bacommon.docui.routes.docuitest.Flavor,
) -> LangStrSpecValue:
    # Exhaustive on purpose: a new flavor is a type error here until
    # it gets a label.
    # pylint: disable=cyclic-import
    from bacommon.docui.routes.docuitest import Flavor

    match flavor:
        case Flavor.VANILLA:
            return _lit('Vanilla')
        case Flavor.CHOCOLATE:
            return _lit('Chocolate')
        case Flavor.STRAWBERRY:
            return _lit('Strawberry')
        case Flavor.MINT:
            return _lit('Mint Chocolate Chip (a long one)')
        case _:
            assert_never(flavor)


def _size_label(size: bacommon.docui.routes.docuitest.Size) -> LangStrSpecValue:
    return _lit(size.name)


def _size_label_long(
    size: bacommon.docui.routes.docuitest.Size,
) -> LangStrSpecValue:
    return _lit(
        f'{size.name} - an unreasonably long choice label to test the'
        f' button width clamp'
    )


def _band_text(
    text: str, h_align: bacommon.docui.v2.HAlign, debug: bool
) -> bacommon.docui.v2.Text:
    """A faint label for header/footer band demos, on the band midline."""
    return dui2.Text(
        text=_lit(text),
        position=(0, 0),
        size=(150, 30),
        scale=0.7,
        color=(1, 1, 1, 0.4),
        h_align=h_align,
        debug=debug,
    )


def _map_button(
    action: bacommon.docui.v2.Action, scale: float = 1.0
) -> bacommon.docui.v2.Button:
    """A button showing a map preview, for button control row demos."""
    from bauiv1 import _classiccatalogassets as assets

    # A regular button with the preview laid over it, so it still reads
    # as a button (and greys like one when disabled).
    return dui2.Button(
        size=(110, 62),
        style=dui2.ButtonStyle.MEDIUM,
        scale=scale,
        action=action,
        decorations=[
            dui2.Image(
                texture=assets.textures.big_g_preview,
                mask_texture=assets.textures.map_preview_mask,
                mesh_opaque=assets.meshes.level_select_button_opaque,
                mesh_transparent=(
                    assets.meshes.level_select_button_transparent
                ),
                position=(0, 0),
                size=(96, 48),
            )
        ],
    )


def _test_menu(
    route: bacommon.docui.routes.docuitest.Widgets,
    state: bacommon.docui.routes.docuitest.WidgetTestState,
) -> bacommon.docui.v2.Menu:
    """A menu with one item per kind of action, plus a disabled one."""
    # pylint: disable=cyclic-import
    import bacommon.docui.routes.docuitest as rt

    wstate = rt.WidgetTestState

    return dui2.Menu(
        items=[
            # Replace: re-requests the page with a state change.
            dui2.MenuItem(
                label=_lit('Presses +1 (replace)'),
                action=route.replace(
                    sets=[wstate.assign(lambda s: s.presses, state.presses + 1)]
                ),
            ),
            # Local; no request. Rows update in place.
            dui2.MenuItem(
                label=_lit('Check Both (local)'),
                action=wstate.assign_locally(
                    wstate.assign(lambda s: s.plain, True),
                    wstate.assign(lambda s: s.live, True),
                ),
            ),
            dui2.MenuItem(
                label=_lit('Show a Message (local-action)'),
                action=rt.TestAction(testparam=345).local(),
            ),
            dui2.MenuItem(
                label=_lit("What's This? (popup text)"),
                action=dui2.PopupText(text=_lit(_POPUP_SHORT)),
            ),
            dui2.MenuItem(
                label=_lit('Not Available (disabled)'),
                action=rt.TestAction(testparam=456).local(),
                disabled=True,
            ),
            # Browse: opens a new window.
            dui2.MenuItem(
                label=_lit('Nav Test (browse)'),
                action=rt.NavTest().browse(layout=dui2.WindowLayout.SMALL),
            ),
        ]
    )


def test_page_widgets(
    route: bacommon.docui.routes.docuitest.Widgets,
) -> bacommon.docui.v2.Response:
    """Control rows, plus a readout of the state each request carried."""
    # pylint: disable=cyclic-import
    import bacommon.docui.routes.docuitest as rt
    from bauiv1lib.docuitestlayouts import with_test_viewer

    wstate = rt.WidgetTestState

    # State arrives with whatever request the page fired at us; a
    # first visit has none, so we start from defaults.
    arrived = route.get_state(wstate)
    state = wstate() if arrived is None else arrived

    debug = route.debug

    return dui2.Response(
        page=with_test_viewer(
            route.viewer_side,
            route.theme,
            title=_lit('Widgets'),
            # Declared once, here; everything below refers to it.
            state=state.encode(),
            rows=[
                # One tall flat panel: the state this request carried,
                # one field per line.
                dui2.TitleRow(_lit('Page State')),
                dui2.ButtonRow(
                    content_align=dui2.HAlign.CENTER,
                    debug=debug,
                    buttons=[
                        dui2.Button(
                            texture=_commonassets.textures.white,
                            # Fits a small layout's column (600, less
                            # row buffers and h-scroll insets; 540
                            # overflowed its h-scroll by 4).
                            size=(530, 290),
                            style=dui2.ButtonStyle.MEDIUM,
                            color=(0, 0, 0, 0.25),
                            # Button labels only center; a text
                            # decoration can be left-aligned.
                            decorations=[
                                dui2.Text(
                                    _lit(
                                        (
                                            'The request for this page'
                                            ' carried:'
                                            if arrived is not None
                                            else 'The request for this page'
                                            ' carried no state (showing'
                                            ' defaults):'
                                        )
                                        + f'\n\nplain = {state.plain}'
                                        f'\nlive = {state.live}'
                                        f'\npresses = {state.presses}'
                                        f'\ntext_short = {state.text_short!r}'
                                        f'\ntext_medium ='
                                        f' {state.text_medium!r}'
                                        f'\ntext_long = {state.text_long!r}'
                                        f'\ntext_live = {state.text_live!r}'
                                        f'\nflavor = {state.flavor}'
                                        f'\nflavor_live = {state.flavor_live}'
                                        f'\ntopping = {state.topping}'
                                        f'\ndifficulty = {state.difficulty!r}'
                                        f'\nregion = {state.region!r}'
                                        f'\ntint = {state.tint}'
                                        f'\nvolume = {state.volume}'
                                        f'\n\ntrigger ='
                                        f' {route.get_trigger()!r}'
                                    ),
                                    position=(-250, 0),
                                    size=(500, 270),
                                    scale=0.6,
                                    h_align=dui2.HAlign.LEFT,
                                    color=(0.8, 1.0, 0.8, 1.0),
                                    flatness=1.0,
                                    shadow=0.0,
                                    debug=debug,
                                ),
                            ],
                        ),
                    ],
                ),
                # No on-change action, so toggling this does nothing
                # until something else on the page fires a request.
                dui2.TitleRow(_lit('Checkboxes (title only)')),
                wstate.checkbox_row(
                    lambda s: s.plain,
                    label=_lit('Plain (goes out with the next request)'),
                    debug=debug,
                ),
                # Re-requests the page the moment it changes.
                wstate.checkbox_row(
                    lambda s: s.live,
                    label=_lit('Live (re-requests the page when changed)'),
                    on_change=route.replace(default_sound=False),
                    debug=debug,
                ),
                dui2.FootnoteRow(
                    _lit('A footnote: small text below the control.')
                ),
                wstate.checkbox_row(
                    lambda s: s.checked_disabled,
                    label=_lit(
                        'Disabled, checked (selectable; not toggleable)'
                    ),
                    disabled=True,
                    debug=debug,
                ),
                wstate.checkbox_row(
                    lambda s: s.unchecked_disabled,
                    label=_lit('Disabled, unchecked'),
                    disabled=True,
                    debug=debug,
                ),
                # Text inputs. Labels get up to half the row (squished
                # to fit past that); the box gets whatever is left.
                dui2.TitleRow(_lit('Text Inputs (title + subtitle)')),
                dui2.SubtitleRow(
                    _lit(
                        'Labels take up to 2/3; boxes get 1/3 to 2/3'
                        '\n(a two-line subtitle)'
                    )
                ),
                wstate.text_input_row(
                    lambda s: s.text_short,
                    label=_lit('Hi'),
                    max_chars=16,
                    debug=debug,
                ),
                dui2.FootnoteRow(
                    _lit(
                        'Text-input footnote (title + subtitle + footnote).'
                        '\nA second line; the strip grows to fit.'
                    )
                ),
                wstate.text_input_row(
                    lambda s: s.text_medium,
                    label=_lit('A Medium Length Label'),
                    debug=debug,
                ),
                wstate.text_input_row(
                    lambda s: s.text_long,
                    label=_lit(
                        'A way too long label which goes on and on and'
                        ' should wind up getting squished down to fit'
                        ' into its half of the row'
                    ),
                    debug=debug,
                ),
                dui2.SubtitleRow(_lit('(subtitle only, no title)')),
                wstate.text_input_row(
                    lambda s: s.text_live,
                    label=_lit('Live (re-requests when applied)'),
                    on_change=route.replace(default_sound=False),
                    debug=debug,
                ),
                wstate.text_input_row(
                    lambda s: s.text_disabled,
                    label=_lit('Disabled (selectable; not editable)'),
                    disabled=True,
                    debug=debug,
                ),
                # Choices.
                dui2.TitleRow(_lit('Choices (right-aligned title)')),
                dui2.SubtitleRow(_lit('and subtitle')),
                wstate.choice_row(
                    lambda s: s.flavor,
                    choice_label=_flavor_label,
                    label=_lit('Flavor'),
                    title_align=dui2.HAlign.RIGHT,
                    debug=debug,
                ),
                dui2.FootnoteRow(_lit('and footnote')),
                wstate.choice_row(
                    lambda s: s.flavor_live,
                    choice_label=_flavor_label,
                    label=_lit('Live flavor (re-requests when picked)'),
                    on_change=route.replace(default_sound=False),
                    debug=debug,
                ),
                wstate.choice_row(
                    lambda s: s.size,
                    choice_label=_size_label,
                    label=_lit('Size (short choices)'),
                    debug=debug,
                ),
                wstate.choice_row(
                    lambda s: s.size_long,
                    choice_label=_size_label_long,
                    label=_lit('Size (long choices)'),
                    debug=debug,
                ),
                wstate.choice_row(
                    lambda s: s.topping,
                    choice_label=_flavor_label,
                    none_label=_lit('No Topping'),
                    label=_lit('Topping (optional)'),
                    debug=debug,
                ),
                # String choices: the page defines the options.
                wstate.choice_row(
                    lambda s: s.difficulty,
                    choices=[
                        ('easy', _lit('Easy')),
                        ('normal', _lit('Normal')),
                        ('hard', _lit('Hard')),
                    ],
                    label=_lit('Difficulty (string choices)'),
                    debug=debug,
                ),
                dui2.FootnoteRow(_lit('Choice-row footnote.')),
                wstate.choice_row(
                    lambda s: s.region,
                    choices=[
                        ('us', _lit('United States')),
                        ('eu', _lit('Europe')),
                        ('asia', _lit('Asia')),
                    ],
                    none_label=_lit('Any Region'),
                    label=_lit('Region (optional string choices)'),
                    debug=debug,
                ),
                # Disabled rows, one of each form: selectable, but their
                # menus won't open (a press sounds an error).
                wstate.choice_row(
                    lambda s: s.flavor_disabled,
                    choice_label=_flavor_label,
                    label=_lit('Disabled flavor'),
                    disabled=True,
                    debug=debug,
                ),
                wstate.choice_row(
                    lambda s: s.topping_disabled,
                    choice_label=_flavor_label,
                    none_label=_lit('No Topping'),
                    label=_lit('Disabled topping (optional)'),
                    disabled=True,
                    debug=debug,
                ),
                wstate.choice_row(
                    lambda s: s.difficulty_disabled,
                    choices=[
                        ('easy', _lit('Easy')),
                        ('normal', _lit('Normal')),
                        ('hard', _lit('Hard')),
                    ],
                    label=_lit('Disabled difficulty (string choices)'),
                    disabled=True,
                    debug=debug,
                ),
                wstate.choice_row(
                    lambda s: s.region_disabled,
                    choices=[
                        ('us', _lit('United States')),
                        ('eu', _lit('Europe')),
                        ('asia', _lit('Asia')),
                    ],
                    none_label=_lit('Any Region'),
                    label=_lit('Disabled region (optional string choices)'),
                    disabled=True,
                    debug=debug,
                ),
                # Slider: the sound-settings volume shape. on_drag is a
                # local action reading the live value from page state
                # (throttled like ConfigSlider); on_change re-requests.
                dui2.TitleRow(_lit('Slider\n(a two-line title)')),
                wstate.slider_row(
                    lambda s: s.volume,
                    min_value=0.0,
                    max_value=1.0,
                    increment=0.05,
                    as_percent=True,
                    label=_lit('Volume (messages while dragging)'),
                    on_drag=rt.ShowVolume().local(default_sound=False),
                    drag_interval=0.5,
                    drag_delay=0.5,
                    on_change=route.replace(default_sound=False),
                    debug=debug,
                ),
                dui2.FootnoteRow(
                    _lit('Slider footnote: drag applies at 0.5s cadence.')
                ),
                wstate.slider_row(
                    lambda s: s.volume_disabled,
                    min_value=0.0,
                    max_value=1.0,
                    increment=0.05,
                    as_percent=True,
                    label=_lit('Disabled (selectable; not adjustable)'),
                    disabled=True,
                    debug=debug,
                ),
                # Number: each '-'/'+' press steps the value and
                # re-requests; holding a button repeats.
                dui2.TitleRow(_lit('Number')),
                wstate.number_row(
                    lambda s: s.series_length,
                    min_value=1.0,
                    max_value=21.0,
                    increment=2.0,
                    label=_lit('Series length (re-requests per press)'),
                    on_change=route.replace(default_sound=False),
                    debug=debug,
                ),
                dui2.FootnoteRow(_lit('Number-row footnote.')),
                wstate.number_row(
                    lambda s: s.series_length_disabled,
                    min_value=1.0,
                    max_value=21.0,
                    increment=2.0,
                    label=_lit('Disabled (selectable; not adjustable)'),
                    disabled=True,
                    debug=debug,
                ),
                # Color: picks update state locally; the request fires
                # once when the picker closes with a change.
                dui2.TitleRow(_lit('Color')),
                wstate.color_row(
                    lambda s: s.tint,
                    label=_lit('Tint (re-requests when picker closes)'),
                    on_change=route.replace(default_sound=False),
                    debug=debug,
                ),
                dui2.FootnoteRow(_lit('Color-row footnote.')),
                wstate.color_row(
                    lambda s: s.tint_disabled,
                    label=_lit('Disabled (selectable; picker won\'t open)'),
                    disabled=True,
                    debug=debug,
                ),
                # Button control rows: a label with whatever button the
                # page likes at the right, and no value of their own.
                # Here the button shows a 'current selection' (a map
                # preview) and browses somewhere, as a picker would.
                dui2.TitleRow(_lit('Button Control')),
                dui2.ButtonControlRow(
                    button=_map_button(rt.NavTest().browse()),
                    label=_lit('Map (browses when pressed)'),
                    debug=debug,
                ),
                dui2.FootnoteRow(
                    _lit(
                        'Button-control-row footnote, styled as a warning'
                        ' (footnote_color/flatness/shadow).'
                    ),
                    color=(1.0, 0.45, 0.3, 1.0),
                    flatness=1.0,
                    shadow=0.0,
                ),
                dui2.ButtonControlRow(
                    button=_map_button(rt.NavTest().browse()),
                    label=_lit('Disabled (selectable; not pressable)'),
                    disabled=True,
                    debug=debug,
                ),
                # Text all around a big button: the label squishes to
                # fit beside it, and the title and footnote stay above
                # and below it wherever they are long enough to run
                # into it (in a narrow window, say). Text that stops
                # short of the button sits beside it instead.
                dui2.TitleRow(
                    _lit(
                        'A title long enough to reach all the way over'
                        ' to the button at the right'
                    )
                ),
                dui2.ButtonControlRow(
                    button=_map_button(rt.NavTest().browse(), scale=1.6),
                    label=_lit(
                        'A long label which gets squished to fit beside'
                        ' its button'
                    ),
                    debug=debug,
                ),
                dui2.FootnoteRow(
                    _lit(
                        'And a footnote doing the same down here, which'
                        ' goes on long enough to pass under the button.'
                    )
                ),
                # Extreme: a very tall button, with a title and a
                # several-line footnote running over and under it. They
                # keep the same clearance from the button whatever its
                # height. (Then a short one with the same text, for
                # contrast.)
                *(
                    row
                    for label, height in (('Tall', 150.0), ('Short', 35.0))
                    for row in (
                        dui2.TitleRow(
                            _lit(
                                'A title running all the way over to the'
                                ' button at the right, as long titles do'
                            )
                        ),
                        dui2.ButtonControlRow(
                            button=dui2.Button(
                                label=_lit(label),
                                style=style_for_square((140.0, height)),
                                size=(140.0, height),
                                action=dui2.Local(),
                            ),
                            label=_lit('Label'),
                            debug=debug,
                        ),
                        dui2.FootnoteRow(
                            _lit(
                                'A footnote running under the button at the'
                                ' right.\nIt has a few lines, each of them'
                                ' long enough to reach the button.\nThe last'
                                ' line too, so all of it stays clear of the'
                                ' button.'
                            )
                        ),
                    )
                ),
                # Text rows standing alone (attach off): spaced from
                # both neighbors like rows rather than hugging one.
                dui2.TitleRow(
                    _lit('A standalone title (attach=False)'), attach=False
                ),
                dui2.SubtitleRow(
                    _lit('And a standalone subtitle, attached to nothing.'),
                    attach=False,
                ),
                # Fill and fixed rows (see docuitestbuttonrows).
                *fill_and_fixed_rows(debug),
                # Control rows get the same spacing and header/footer
                # bands button rows do. (The typed-state helpers don't
                # take these, so they get set on what the helpers
                # return.)
                dui2.TitleRow(_lit('Control-Row Spacing & Bands')),
                replace(
                    wstate.checkbox_row(
                        lambda s: s.spacing_top_demo,
                        label=_lit('spacing_top=40 (big gap above)'),
                        debug=debug,
                    ),
                    spacing_top=40.0,
                ),
                replace(
                    wstate.checkbox_row(
                        lambda s: s.spacing_bottom_demo,
                        label=_lit('spacing_bottom=40 (big gap below)'),
                        debug=debug,
                    ),
                    spacing_bottom=40.0,
                ),
                # (Bands attached from header/footer rows.)
                dui2.HeaderRow(
                    50.0,
                    decorations_left=[
                        _band_text('header left', dui2.HAlign.LEFT, debug)
                    ],
                    decorations_center=[
                        _band_text('header center', dui2.HAlign.CENTER, debug)
                    ],
                    decorations_right=[
                        _band_text('header right', dui2.HAlign.RIGHT, debug)
                    ],
                ),
                wstate.checkbox_row(
                    lambda s: s.bands_demo,
                    label=_lit('Header and footer bands (50 tall)'),
                    debug=debug,
                ),
                dui2.FooterRow(
                    50.0,
                    decorations_left=[
                        _band_text('footer left', dui2.HAlign.LEFT, debug)
                    ],
                    decorations_center=[
                        _band_text('footer center', dui2.HAlign.CENTER, debug)
                    ],
                    decorations_right=[
                        _band_text('footer right', dui2.HAlign.RIGHT, debug)
                    ],
                ),
                # The same button enabled and disabled, side by side. Both
                # carry the same action; only the enabled one runs it (the
                # disabled one selects on tap and answers presses with an
                # error sound).
                dui2.TitleRow(_lit('Buttons: normal and disabled')),
                dui2.ButtonRow(
                    debug=debug,
                    buttons=[
                        dui2.Button(
                            label=_lit('Presses +1'),
                            size=(220, 60),
                            style=dui2.ButtonStyle.MEDIUM,
                            action=route.replace(
                                sets=[
                                    wstate.assign(
                                        lambda s: s.presses,
                                        state.presses + 1,
                                    )
                                ]
                            ),
                        ),
                        dui2.Button(
                            label=_lit('Presses +1 (disabled)'),
                            size=(220, 60),
                            style=dui2.ButtonStyle.MEDIUM,
                            action=route.replace(
                                sets=[
                                    wstate.assign(
                                        lambda s: s.presses,
                                        state.presses + 1,
                                    )
                                ]
                            ),
                            disabled=True,
                        ),
                    ],
                ),
                # The same menu button enabled and disabled. A press on
                # the enabled one pops up its menu; picking an item runs
                # that item's action as if a button had been pressed
                # with it. The disabled one never opens. Menu buttons
                # draw like any other button, so a small '...' works too.
                dui2.TitleRow(_lit('Menu buttons: normal and disabled')),
                dui2.ButtonRow(
                    debug=debug,
                    buttons=[
                        dui2.Button(
                            label=_lit('Menu'),
                            size=(220, 60),
                            style=dui2.ButtonStyle.MEDIUM,
                            action=_test_menu(route, state),
                        ),
                        dui2.Button(
                            label=_lit('Menu (disabled)'),
                            size=(220, 60),
                            style=dui2.ButtonStyle.MEDIUM,
                            action=_test_menu(route, state),
                            disabled=True,
                        ),
                        dui2.Button(
                            label=_lit('...'),
                            size=(70, 60),
                            style=dui2.ButtonStyle.SQUARE,
                            action=_test_menu(route, state),
                        ),
                    ],
                ),
                dui2.FootnoteRow(
                    _lit(
                        'Picking an item runs its action; one item is'
                        ' itself disabled.'
                    )
                ),
                # Popup text: a press pops up the text at the button,
                # sized to fit it, with an ok button. A small '?' is
                # the intended use; the long one shows wrapping.
                dui2.TitleRow(_lit('Popup text buttons')),
                dui2.ButtonRow(
                    debug=debug,
                    buttons=[
                        dui2.Button(
                            label=_lit('?'),
                            size=(60, 60),
                            style=dui2.ButtonStyle.SQUARE,
                            action=dui2.PopupText(text=_lit(_POPUP_SHORT)),
                        ),
                        dui2.Button(
                            label=_lit('Long Text'),
                            size=(200, 60),
                            style=dui2.ButtonStyle.MEDIUM,
                            action=dui2.PopupText(text=_lit(_POPUP_LONG)),
                        ),
                        # Past the height cap; squishes to fit.
                        dui2.Button(
                            label=_lit('Huge Text'),
                            size=(200, 60),
                            style=dui2.ButtonStyle.MEDIUM,
                            action=dui2.PopupText(
                                text=_lit('\n\n'.join([_POPUP_LONG] * 6))
                            ),
                        ),
                    ],
                ),
                dui2.FootnoteRow(
                    _lit('Ok or a press outside the popup closes it.')
                ),
                # Small buttons, where label margins are fractions of
                # the button's size (capped at fixed amounts on bigger
                # ones) so labels keep a usable share of the space.
                dui2.TitleRow(_lit('Small buttons')),
                dui2.ButtonRow(
                    debug=debug,
                    buttons=[
                        dui2.Button(
                            label=_lit(label),
                            size=size,
                            style=style_for_square(size),
                            action=dui2.Local(),
                        )
                        for label, size in [
                            ('?', (24.0, 24.0)),
                            ('OK', (40.0, 24.0)),
                            ('Small Label', (80.0, 24.0)),
                            ('Two\nLines', (60.0, 36.0)),
                        ]
                    ],
                ),
                dui2.ButtonRow(
                    content_align=dui2.HAlign.RIGHT,
                    debug=debug,
                    buttons=[
                        dui2.Button(
                            label=_lit('Check Both'),
                            size=(180, 60),
                            style=dui2.ButtonStyle.MEDIUM,
                            # Local; no request. Rows update in place.
                            action=wstate.assign_locally(
                                wstate.assign(lambda s: s.plain, True),
                                wstate.assign(lambda s: s.live, True),
                            ),
                        ),
                        dui2.Button(
                            label=_lit('Presses +1'),
                            size=(180, 60),
                            style=dui2.ButtonStyle.MEDIUM,
                            # A link only says what it *changes*; the
                            # rest of the state rides along untouched.
                            action=route.replace(
                                sets=[
                                    wstate.assign(
                                        lambda s: s.presses,
                                        state.presses + 1,
                                    )
                                ]
                            ),
                        ),
                        dui2.Button(
                            label=_lit('Submit'),
                            size=(180, 60),
                            style=dui2.ButtonStyle.MEDIUM,
                            default=True,
                            action=route.replace(),
                        ),
                        dui2.Button(
                            label=_lit('Hide Debug' if debug else 'Show Debug'),
                            size=(180, 60),
                            style=dui2.ButtonStyle.MEDIUM,
                            action=replace(route, debug=not debug).replace(),
                        ),
                        # Control-row navigation at a page's edges (a
                        # control row as the very last row).
                        dui2.Button(
                            label=_lit('Nav Test'),
                            size=(180, 60),
                            style=dui2.ButtonStyle.MEDIUM,
                            action=rt.NavTest().browse(
                                layout=dui2.WindowLayout.SMALL
                            ),
                        ),
                    ],
                ),
                dui2.FootnoteRow(
                    _lit('Button-row footnote (follows the title alignment).')
                ),
            ],
        )
    )
