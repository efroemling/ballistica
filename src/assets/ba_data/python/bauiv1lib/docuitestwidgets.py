# Released under the MIT License. See LICENSE for details.
#
"""Doc-ui test page for control rows and page state."""

from dataclasses import replace
from typing import TYPE_CHECKING, assert_never

from bacommon.langstr import LangStrSpecValue
import bacommon.docui.v2 as dui2
from bauiv1 import _builtinassets

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


def _fill_button(label: str, width: float = 100.0) -> bacommon.docui.v2.Button:
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
) -> bacommon.docui.v2.Button:
    """A do-nothing button at its own size, for fixed-row demos."""
    return dui2.Button(
        label=_lit(label),
        size=size,
        style=_style_for(size),
        action=dui2.Local(),
    )


def _style_for(size: tuple[float, float]) -> dui2.ButtonStyle:
    """Square backing for squarish buttons; medium for wide ones."""
    return (
        dui2.ButtonStyle.SQUARE
        if size[0] <= size[1] * 1.5
        else dui2.ButtonStyle.MEDIUM
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

    wstate = rt.WidgetTestState

    # State arrives with whatever request the page fired at us; a
    # first visit has none, so we start from defaults.
    arrived = route.get_state(wstate)
    state = wstate() if arrived is None else arrived

    debug = route.debug

    return dui2.Response(
        page=dui2.Page(
            title=_lit('Widgets'),
            # Declared once, here; everything below refers to it.
            state=state.encode(),
            rows=[
                # One tall flat panel: the state this request carried,
                # one field per line.
                dui2.ButtonRow(
                    title=_lit('Page State'),
                    content_align=dui2.HAlign.CENTER,
                    debug=debug,
                    buttons=[
                        dui2.Button(
                            texture=_builtinassets.textures.white,
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
                wstate.checkbox_row(
                    lambda s: s.plain,
                    label=_lit('Plain (goes out with the next request)'),
                    title=_lit('Checkboxes (title only)'),
                    debug=debug,
                ),
                # Re-requests the page the moment it changes.
                wstate.checkbox_row(
                    lambda s: s.live,
                    label=_lit('Live (re-requests the page when changed)'),
                    footnote=_lit('A footnote: small text below the control.'),
                    on_change=route.replace(default_sound=False),
                    debug=debug,
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
                wstate.text_input_row(
                    lambda s: s.text_short,
                    label=_lit('Hi'),
                    max_chars=16,
                    title=_lit('Text Inputs (title + subtitle)'),
                    subtitle=_lit(
                        'Labels take up to 2/3; boxes get 1/3 to 2/3'
                        '\n(a two-line subtitle)'
                    ),
                    footnote=_lit(
                        'Text-input footnote (title + subtitle + footnote).'
                        '\nA second line; the strip grows to fit.'
                    ),
                    debug=debug,
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
                wstate.text_input_row(
                    lambda s: s.text_live,
                    label=_lit('Live (re-requests when applied)'),
                    subtitle=_lit('(subtitle only, no title)'),
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
                wstate.choice_row(
                    lambda s: s.flavor,
                    choice_label=_flavor_label,
                    label=_lit('Flavor'),
                    title=_lit('Choices (right-aligned title)'),
                    subtitle=_lit('and subtitle'),
                    footnote=_lit('and footnote'),
                    title_align=dui2.HAlign.RIGHT,
                    debug=debug,
                ),
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
                    footnote=_lit('Choice-row footnote.'),
                    debug=debug,
                ),
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
                wstate.slider_row(
                    lambda s: s.volume,
                    min_value=0.0,
                    max_value=1.0,
                    increment=0.05,
                    as_percent=True,
                    label=_lit('Volume (messages while dragging)'),
                    title=_lit('Slider\n(a two-line title)'),
                    footnote=_lit(
                        'Slider footnote: drag applies at 0.5s cadence.'
                    ),
                    on_drag=rt.ShowVolume().local(default_sound=False),
                    drag_interval=0.5,
                    drag_delay=0.5,
                    on_change=route.replace(default_sound=False),
                    debug=debug,
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
                wstate.number_row(
                    lambda s: s.series_length,
                    min_value=1.0,
                    max_value=21.0,
                    increment=2.0,
                    label=_lit('Series length (re-requests per press)'),
                    title=_lit('Number'),
                    footnote=_lit('Number-row footnote.'),
                    on_change=route.replace(default_sound=False),
                    debug=debug,
                ),
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
                wstate.color_row(
                    lambda s: s.tint,
                    label=_lit('Tint (re-requests when picker closes)'),
                    title=_lit('Color'),
                    footnote=_lit('Color-row footnote.'),
                    on_change=route.replace(default_sound=False),
                    debug=debug,
                ),
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
                dui2.ButtonControlRow(
                    button=_map_button(rt.NavTest().browse()),
                    label=_lit('Map (browses when pressed)'),
                    title=_lit('Button Control'),
                    footnote=_lit(
                        'Button-control-row footnote, styled as a warning'
                        ' (footnote_color/flatness/shadow).'
                    ),
                    footnote_color=(1.0, 0.45, 0.3, 1.0),
                    footnote_flatness=1.0,
                    footnote_shadow=0.0,
                    debug=debug,
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
                dui2.ButtonControlRow(
                    button=_map_button(rt.NavTest().browse(), scale=1.6),
                    label=_lit(
                        'A long label which gets squished to fit beside'
                        ' its button'
                    ),
                    title=_lit(
                        'A title long enough to reach all the way over'
                        ' to the button at the right'
                    ),
                    footnote=_lit(
                        'And a footnote doing the same down here, which'
                        ' goes on long enough to pass under the button.'
                    ),
                    debug=debug,
                ),
                # Extreme: a very tall button, with a title and a
                # several-line footnote running over and under it. They
                # keep the same clearance from the button whatever its
                # height. (Then a short one with the same text, for
                # contrast.)
                *(
                    dui2.ButtonControlRow(
                        button=dui2.Button(
                            label=_lit(label),
                            style=_style_for((140.0, height)),
                            size=(140.0, height),
                            action=dui2.Local(),
                        ),
                        label=_lit('Label'),
                        title=_lit(
                            'A title running all the way over to the'
                            ' button at the right, as long titles do'
                        ),
                        footnote=_lit(
                            'A footnote running under the button at the'
                            ' right.\nIt has a few lines, each of them long'
                            ' enough to reach the button.\nThe last line'
                            ' too, so all of it stays clear of the button.'
                        ),
                        debug=debug,
                    )
                    for label, height in (('Tall', 150.0), ('Short', 35.0))
                ),
                # Fill rows: one or more buttons sharing the full width
                # control rows span, so their edges line up with the
                # labels and controls above and below. They never scroll
                # sideways (nothing clips).
                dui2.ButtonRow(
                    layout=dui2.ButtonRowLayout.FILL,
                    title=_lit('Fill Rows'),
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
                    footnote=_lit('Fill-row footnote.'),
                    debug=debug,
                ),
                # Widths share the row in proportion to the buttons' own.
                dui2.ButtonRow(
                    layout=dui2.ButtonRowLayout.FILL,
                    buttons=[
                        _fill_button('1x'),
                        _fill_button('2x', width=200.0),
                    ],
                    footnote=_lit('Sized 100 and 200: a 1:2 split.'),
                    debug=debug,
                ),
                # All the text a fill row takes, between plain ones, to
                # judge its spacing against its neighbors.
                dui2.ButtonRow(
                    layout=dui2.ButtonRowLayout.FILL,
                    buttons=[_fill_button('Plain Above')],
                    debug=debug,
                ),
                dui2.ButtonRow(
                    layout=dui2.ButtonRowLayout.FILL,
                    title=_lit('Titled Fill Row'),
                    subtitle=_lit('With a subtitle under its title'),
                    footnote=_lit('And a footnote under its buttons.'),
                    buttons=[_fill_button('A'), _fill_button('B')],
                    debug=debug,
                ),
                dui2.ButtonRow(
                    layout=dui2.ButtonRowLayout.FILL,
                    buttons=[_fill_button('Plain Below')],
                    debug=debug,
                ),
                # Fixed rows: buttons at their own sizes, straight on
                # the page (nothing clips), aligned like a scrolling
                # row's. First the same buttons both ways: they should
                # land in the same place.
                dui2.ButtonRow(
                    title=_lit('Fixed Rows'),
                    subtitle=_lit('A scrolling row, then a fixed one'),
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
                    footnote=_lit('Eight 150-wide buttons, shrunk to fit.'),
                    debug=debug,
                ),
                # Content offset: the group shifts from the row's center
                # -- the same point band decorations are placed from --
                # so a button lines up under band art at the same x
                # whatever the layout's width or insets.
                dui2.ButtonRow(
                    layout=dui2.ButtonRowLayout.FIXED,
                    center_content=True,
                    content_offset=-200.0,
                    header_height=40.0,
                    header_decorations_center=[
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
                    buttons=[_fixed_button('Offset -200', (180.0, 40.0))],
                    footnote=_lit(
                        'content_offset=-200: centered under band art'
                        ' at x=-200.'
                    ),
                    debug=debug,
                ),
                dui2.ButtonRow(
                    layout=dui2.ButtonRowLayout.FIXED,
                    center_content=True,
                    content_offset=150.0,
                    buttons=[
                        _fixed_button('Group', (120.0, 40.0)),
                        _fixed_button('Shifted', (120.0, 40.0)),
                    ],
                    footnote=_lit(
                        'Two buttons, content_offset=150: they move as a'
                        ' group, spacing unchanged.'
                    ),
                    debug=debug,
                ),
                dui2.ButtonRow(
                    layout=dui2.ButtonRowLayout.FIXED,
                    center_content=True,
                    content_offset=5000.0,
                    buttons=[_fixed_button('Clamped', (150.0, 40.0))],
                    footnote=_lit(
                        'content_offset=5000: slides back in at the'
                        ' right edge rather than leaving the row.'
                    ),
                    debug=debug,
                ),
                # Control rows get the same spacing and header/footer
                # bands button rows do. (The typed-state helpers don't
                # take these, so they get set on what the helpers
                # return.)
                replace(
                    wstate.checkbox_row(
                        lambda s: s.spacing_top_demo,
                        title=_lit('Control-Row Spacing & Bands'),
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
                replace(
                    wstate.checkbox_row(
                        lambda s: s.bands_demo,
                        label=_lit('Header and footer bands (50 tall)'),
                        debug=debug,
                    ),
                    header_height=50.0,
                    header_decorations_left=[
                        _band_text('header left', dui2.HAlign.LEFT, debug)
                    ],
                    header_decorations_center=[
                        _band_text('header center', dui2.HAlign.CENTER, debug)
                    ],
                    header_decorations_right=[
                        _band_text('header right', dui2.HAlign.RIGHT, debug)
                    ],
                    footer_height=50.0,
                    footer_decorations_left=[
                        _band_text('footer left', dui2.HAlign.LEFT, debug)
                    ],
                    footer_decorations_center=[
                        _band_text('footer center', dui2.HAlign.CENTER, debug)
                    ],
                    footer_decorations_right=[
                        _band_text('footer right', dui2.HAlign.RIGHT, debug)
                    ],
                ),
                # The same button enabled and disabled, side by side. Both
                # carry the same action; only the enabled one runs it (the
                # disabled one selects on tap and answers presses with an
                # error sound).
                dui2.ButtonRow(
                    title=_lit('Buttons: normal and disabled'),
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
                dui2.ButtonRow(
                    title=_lit('Menu buttons: normal and disabled'),
                    footnote=_lit(
                        'Picking an item runs its action; one item is'
                        ' itself disabled.'
                    ),
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
                # Popup text: a press pops up the text at the button,
                # sized to fit it, with an ok button. A small '?' is
                # the intended use; the long one shows wrapping.
                dui2.ButtonRow(
                    title=_lit('Popup text buttons'),
                    footnote=_lit('Ok or a press outside the popup closes it.'),
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
                # Small buttons, where label margins are fractions of
                # the button's size (capped at fixed amounts on bigger
                # ones) so labels keep a usable share of the space.
                dui2.ButtonRow(
                    title=_lit('Small buttons'),
                    debug=debug,
                    buttons=[
                        dui2.Button(
                            label=_lit(label),
                            size=size,
                            style=_style_for(size),
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
                    footnote=_lit(
                        'Button-row footnote (follows the title alignment).'
                    ),
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
                    ],
                ),
            ],
        )
    )
