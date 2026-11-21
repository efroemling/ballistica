# Released under the MIT License. See LICENSE for details.
#
"""Routes for the doc-ui test domain."""

from enum import Enum
from dataclasses import dataclass
from typing import TYPE_CHECKING, Annotated, override

from efro.dataclassio import ioprepped, IOAttrs

import bacommon.docui.v2 as dui2
from bacommon.docui.routes import (
    DocUIRoute,
    DocUILocalActionBase,
    DocUIState,
    PopupRoute,
    family_members,
)

if TYPE_CHECKING:
    import bacommon.docui.v2


class TestRoute(DocUIRoute):
    """Family class for doc-ui test routes."""

    @override
    @classmethod
    def get_route_types(cls) -> tuple[type[DocUIRoute], ...]:
        return family_members(AnyTestRoute)

    @override
    @classmethod
    def get_window_layout(cls) -> dui2.WindowLayout:
        # Test pages are dense showcases built for the full-size
        # window.
        return dui2.WindowLayout.LARGE


class ThemeVariant(Enum):
    """A look test pages can show their content in.

    The page-themes test pages show each; the root page's 'Layout Test
    Options' pick one for its 'Layout Tests' pages.
    """

    DEFAULT = 'default'
    POPUP_LOOK = 'popup_look'
    BUTTON_COLOR = 'button_color'
    ROLE_COLORS = 'role_colors'
    TIGHT = 'tight'
    ROOMY = 'roomy'
    DARK = 'dark'
    TEXT_STYLES = 'text_styles'


@ioprepped
@dataclass
class Root(TestRoute, path='/'):
    """The root test page."""

    #: Draw bounds and other debug bits.
    debug: Annotated[bool, IOAttrs('debug', store_default=False)] = False

    #: Have the response include some client-effects.
    test_effects: Annotated[
        bool, IOAttrs('test_effects', store_default=False)
    ] = False

    #: Have the response include a local-action.
    test_action: Annotated[
        bool, IOAttrs('test_action', store_default=False)
    ] = False


@ioprepped
@dataclass
class RootState(DocUIState, state_id='docuitest.root'):
    """State for the root test page."""

    #: The window layout picked in its 'Layout Test Options' (for rows
    #: below to open their pages at), and at viewer layouts which side
    #: the viewer pane sits on (None for no pane).
    layout: Annotated[
        dui2.WindowLayout,
        IOAttrs('layout', enum_fallback=dui2.WindowLayout.WIDE_TALL),
    ] = dui2.WindowLayout.WIDE_TALL
    viewer_side: Annotated[
        dui2.ViewerSide | None, IOAttrs('vside', store_default=False)
    ] = None

    #: The theme picked in its 'Layout Test Options' (for rows below to
    #: show their pages in).
    theme: Annotated[
        ThemeVariant,
        IOAttrs(
            'theme', store_default=False, enum_fallback=ThemeVariant.DEFAULT
        ),
    ] = ThemeVariant.DEFAULT


@ioprepped
@dataclass
class Test2(TestRoute, path='/test2'):
    """A second simple page."""


@ioprepped
@dataclass
class Slow(TestRoute, path='/slow'):
    """A page that takes a while to load."""


@ioprepped
@dataclass
class TimedActions(TestRoute, path='/timedactions'):
    """A page that counts down via timed-actions and then closes."""

    val: Annotated[int, IOAttrs('val', store_default=False)] = 5


@ioprepped
@dataclass
class DisplayItems(TestRoute, path='/displayitems'):
    """Display-item tests."""

    debug: Annotated[bool, IOAttrs('debug', store_default=False)] = False


@ioprepped
@dataclass
class TextImages(TestRoute, path='/textimages'):
    """Text-with-images tests."""

    debug: Annotated[bool, IOAttrs('debug', store_default=False)] = False


@ioprepped
@dataclass
class LiveTimes(TestRoute, path='/livetimes'):
    """Time-varying text (countdowns, elapsed times) that ticks itself."""


@ioprepped
@dataclass
class TextWrapping(TestRoute, path='/textwrapping'):
    """Titles, subtitles and footnotes word-wrapped to their columns."""

    debug: Annotated[bool, IOAttrs('debug', store_default=False)] = False


@ioprepped
@dataclass
class Animation(TestRoute, path='/animation'):
    """Decorations animated by keyframe client-effects."""


@ioprepped
@dataclass
class Depictions(TestRoute, path='/depictions'):
    """Depiction tests."""

    debug: Annotated[bool, IOAttrs('debug', store_default=False)] = False


@ioprepped
@dataclass
class Viewers(TestRoute, path='/viewers'):
    """Live viewer tests: good cases and bad data, one shown at a time.

    The page's own controls switch cases, and the pane's style and
    side (page state), in place.
    """

    #: Which case the viewer pane shows (a test-page case name; unknown
    #: names show the first).
    case: Annotated[str, IOAttrs('case', store_default=False)] = ''

    @override
    @classmethod
    def get_window_layout(cls) -> dui2.WindowLayout:
        return dui2.WindowLayout.VIEWER


@ioprepped
@dataclass
class Names(TestRoute, path='/names'):
    """Name depiction tests (basic and capsule forms)."""

    debug: Annotated[bool, IOAttrs('debug', store_default=False)] = False


@ioprepped
@dataclass
class NinePatch(TestRoute, path='/ninepatch'):
    """9-patch image tests (stretched and tile-fit, tinted)."""

    debug: Annotated[bool, IOAttrs('debug', store_default=False)] = False


@ioprepped
@dataclass
class Glyphs(TestRoute, path='/glyphs'):
    """Custom glyphs against their measured bounds and anchor points."""


@ioprepped
@dataclass
class GlyphsState(DocUIState, state_id='docuitest.glyphs'):
    """What the glyphs test page draws over its glyphs."""

    crosshairs: Annotated[bool, IOAttrs('crosshairs')] = True
    bounds: Annotated[bool, IOAttrs('bounds')] = True


@ioprepped
@dataclass
class EmptyPage(TestRoute, path='/emptypage'):
    """A page with nothing on it."""


@ioprepped
@dataclass
class BoundsTests(TestRoute, path='/boundstests'):
    """Button-style bounds tests."""


@ioprepped
@dataclass
class Widgets(TestRoute, path='/widgets'):
    """Control rows and page state."""

    debug: Annotated[bool, IOAttrs('debug', store_default=False)] = False

    #: See :attr:`WindowLayouts.viewer_side`.
    viewer_side: Annotated[
        dui2.ViewerSide | None, IOAttrs('vside', store_default=False)
    ] = None

    #: See :attr:`WindowLayouts.theme`.
    theme: Annotated[
        ThemeVariant,
        IOAttrs(
            'theme', store_default=False, enum_fallback=ThemeVariant.DEFAULT
        ),
    ] = ThemeVariant.DEFAULT


class ControlRowKind(Enum):
    """Kinds of control row (for :class:`NavTest`)."""

    CHECKBOX = 'checkbox'
    TEXT_INPUT = 'text'
    CHOICE = 'choice'
    SLIDER = 'slider'
    NUMBER = 'number'
    COLOR = 'color'
    BUTTON = 'button'


@ioprepped
@dataclass
class NavTest(TestRoute, path='/navtest'):
    """A button row, then one control row of some kind as the last row.

    For checking directional navigation on control rows: down from the
    last row should reach the toolbars, left should reach the back
    button, and right from a row's rightmost control should do nothing.
    """

    kind: Annotated[ControlRowKind, IOAttrs('kind')] = ControlRowKind.CHECKBOX


@ioprepped
@dataclass
class Drill(TestRoute, path='/drill'):
    """The top of a drill-down; shows what was found at the bottom.

    Exploring opens levels in windows of their own, several deep;
    picking something at the bottom closes all of them at once and
    hands the pick back here (see
    :meth:`~bacommon.docui.routes.DocUIRoute.close_to`).
    """


@ioprepped
@dataclass
class DrillLevel(TestRoute, path='/drill/level'):
    """One level of the drill-down, each in a window of its own."""

    #: How deep this is (1 is the first level below the top).
    depth: Annotated[int, IOAttrs('depth')] = 1

    #: Doors taken to get here, in order.
    trail: Annotated[str, IOAttrs('trail')] = ''


@ioprepped
@dataclass
class DrillState(DocUIState, state_id='docuitest.drill'):
    """State for the drill-down's top page."""

    #: What was picked at the bottom, handed back up (empty for
    #: nothing yet).
    found: Annotated[str, IOAttrs('found')] = ''


@ioprepped
@dataclass
class PopupsState(DocUIState, state_id='docuitest.popups'):
    """State for the popups test page, which its popups act on."""

    #: A color picked in a popup (empty for none yet).
    color: Annotated[str, IOAttrs('color')] = ''

    #: Bumped by popups replacing the page.
    count: Annotated[int, IOAttrs('count')] = 0

    #: Set by the button opening a popup (handed along to it).
    opened_with: Annotated[str, IOAttrs('opened')] = ''

    #: Scroll edge style for the popups this page opens.
    edge_style: Annotated[
        dui2.ScrollEdgeStyle,
        IOAttrs('edge', enum_fallback=dui2.ScrollEdgeStyle.FADE),
    ] = dui2.ScrollEdgeStyle.FADE


@ioprepped
@dataclass
class Popups(TestRoute, path='/popups'):
    """Popup windows: opening them and what they can do to this page."""


@ioprepped
@dataclass
class PopupsMain(TestRoute, PopupRoute[PopupsState], path='/popups/main'):
    """The main test popup: acts on its parent every way there is."""

    @override
    @classmethod
    def get_popup_size(cls) -> tuple[float, float]:
        # Lots to show.
        return (600.0, 400.0)


@ioprepped
@dataclass
class PopupsOther(TestRoute, PopupRoute[PopupsState], path='/popups/other'):
    """A second popup, swapped in for the first (and back)."""


@ioprepped
@dataclass
class PopupsMainState(DocUIState, state_id='docuitest.popupsmain'):
    """The main test popup's own state (apart from its parent's)."""

    #: Bumped by the popup replacing its own page.
    bumps: Annotated[int, IOAttrs('bumps')] = 0


@ioprepped
@dataclass
class ThemesState(DocUIState, state_id='docuitest.themes'):
    """State for the page-themes test pages (and their popups)."""

    #: Backs the sample checkbox.
    checked: Annotated[bool, IOAttrs('checked')] = False


@ioprepped
@dataclass
class Themes(TestRoute, path='/themes'):
    """Page themes: the same content shown with various look values."""

    variant: Annotated[
        ThemeVariant,
        IOAttrs('variant', enum_fallback=ThemeVariant.DEFAULT),
    ] = ThemeVariant.DEFAULT

    @override
    @classmethod
    def get_window_layout(cls) -> dui2.WindowLayout:
        # A column, so insets and spacing are easy to compare.
        return dui2.WindowLayout.WIDE_TALL


@ioprepped
@dataclass
class ThemesPopup(TestRoute, PopupRoute[ThemesState], path='/themes/popup'):
    """The page-themes sample content in a popup."""

    variant: Annotated[
        ThemeVariant,
        IOAttrs('variant', enum_fallback=ThemeVariant.DEFAULT),
    ] = ThemeVariant.DEFAULT

    @override
    @classmethod
    def get_popup_size(cls) -> tuple[float, float]:
        return (600.0, 400.0)


@ioprepped
@dataclass
class Sections(TestRoute, path='/sections'):
    """Sections: headings, notes, backings and spacing between them."""

    debug: Annotated[bool, IOAttrs('debug', store_default=False)] = False

    #: See :attr:`WindowLayouts.viewer_side`.
    viewer_side: Annotated[
        dui2.ViewerSide | None, IOAttrs('vside', store_default=False)
    ] = None

    #: See :attr:`WindowLayouts.theme`.
    theme: Annotated[
        ThemeVariant,
        IOAttrs(
            'theme', store_default=False, enum_fallback=ThemeVariant.DEFAULT
        ),
    ] = ThemeVariant.DEFAULT

    @override
    @classmethod
    def get_window_layout(cls) -> dui2.WindowLayout:
        # A column, like the settings pages sections mostly live in.
        return dui2.WindowLayout.SMALL_TALLER


@ioprepped
@dataclass
class ButtonGrids(TestRoute, path='/buttongrids'):
    """Grid button rows: columns, cells, alignment and navigation.

    Browse to it at several layouts; grids reflow to fit each width.
    """

    debug: Annotated[bool, IOAttrs('debug', store_default=False)] = False

    #: See :attr:`WindowLayouts.viewer_side`.
    viewer_side: Annotated[
        dui2.ViewerSide | None, IOAttrs('vside', store_default=False)
    ] = None

    #: See :attr:`WindowLayouts.theme`.
    theme: Annotated[
        ThemeVariant,
        IOAttrs(
            'theme', store_default=False, enum_fallback=ThemeVariant.DEFAULT
        ),
    ] = ThemeVariant.DEFAULT


@ioprepped
@dataclass
class WindowLayouts(TestRoute, path='/windowlayouts'):
    """Assorted rows for judging window layouts (browse to it at each).

    Control rows, titles and button rows at every alignment, and long
    rows, which in a narrow column scroll within it.
    """

    debug: Annotated[bool, IOAttrs('debug', store_default=False)] = False
    #: The layout we're being browsed to at, for the page to name (the
    #: browse sets the actual layout; this is just for show).
    layout: Annotated[
        dui2.WindowLayout | None, IOAttrs('layout', store_default=False)
    ] = None

    #: Which side the page's viewer pane (a turning punch powerup box)
    #: sits on at viewer layouts, or None for a page with no viewer
    #: (its rows then span the window). Ignored at other layouts.
    viewer_side: Annotated[
        dui2.ViewerSide | None, IOAttrs('vside', store_default=False)
    ] = None

    #: The theme to show the page in (its frame colors come with the
    #: link that opens it).
    theme: Annotated[
        ThemeVariant,
        IOAttrs(
            'theme', store_default=False, enum_fallback=ThemeVariant.DEFAULT
        ),
    ] = ThemeVariant.DEFAULT


@ioprepped
@dataclass
class LayoutFit(TestRoute, path='/layoutfit'):
    """A row exactly as big as a layout promises (browse at that layout).

    ``layout`` says which layout it's being shown in. The row fills the
    content rect the layout promises (see
    :data:`bacommon.docui.v2.SMALL_CONTENT_WIDTH` and friends), less the
    page's insets, and should never scroll; with ``over`` /
    ``wide_over`` set it's a hair taller / wider, which should scroll
    where the promise is exact (and may not where it's only a minimum).
    Viewer layouts show a blank viewer pane, as their promises are for
    a page beside one.
    """

    over: Annotated[bool, IOAttrs('over', store_default=False)] = False
    wide_over: Annotated[bool, IOAttrs('wo', store_default=False)] = False
    layout: Annotated[
        dui2.WindowLayout,
        IOAttrs(
            'lo',
            store_default=False,
            enum_fallback=dui2.WindowLayout.WIDE_TALL,
        ),
    ] = dui2.WindowLayout.WIDE_TALL

    #: See :attr:`WindowLayouts.theme`. (The page keeps its own
    #: vertical inset, which its row's size is figured from.)
    theme: Annotated[
        ThemeVariant,
        IOAttrs(
            'theme', store_default=False, enum_fallback=ThemeVariant.DEFAULT
        ),
    ] = ThemeVariant.DEFAULT


class Flavor(Enum):
    """Something to pick from on the widgets test page."""

    VANILLA = 'v'
    CHOCOLATE = 'c'
    STRAWBERRY = 's'
    MINT = 'm'


class Size(Enum):
    """Something else to pick from on the widgets test page."""

    S = 's'
    M = 'm'
    L = 'l'
    XL = 'x'


@ioprepped
@dataclass
class WidgetTestState(DocUIState, state_id='docuitest.widgets'):
    """State for the widgets test page."""

    #: A checkbox with no on-change action.
    plain: Annotated[bool, IOAttrs('plain')] = False

    #: A checkbox that re-requests the page when changed.
    live: Annotated[bool, IOAttrs('live')] = False

    #: Disabled checkboxes (selectable; not toggleable), one checked and
    #: one not.
    checked_disabled: Annotated[bool, IOAttrs('checked_disabled')] = True
    unchecked_disabled: Annotated[bool, IOAttrs('unchecked_disabled')] = False

    #: Nothing shows or edits this directly; it simply rides along
    #: (and gets bumped by a button).
    presses: Annotated[int, IOAttrs('presses')] = 0

    #: Text inputs with labels of assorted lengths.
    text_short: Annotated[str, IOAttrs('text_short')] = ''
    text_medium: Annotated[str, IOAttrs('text_medium')] = 'Some text'
    text_long: Annotated[str, IOAttrs('text_long')] = ''

    #: A text input that re-requests the page when an edit is committed.
    text_live: Annotated[str, IOAttrs('text_live')] = ''

    #: A disabled text input (selectable; not editable).
    text_disabled: Annotated[str, IOAttrs('text_disabled')] = 'Not editable'

    #: Choices, plain and live.
    flavor: Annotated[Flavor, IOAttrs('flavor')] = Flavor.VANILLA
    flavor_live: Annotated[Flavor, IOAttrs('flavor_live')] = Flavor.VANILLA

    #: Short choice labels (a compact button) and an absurdly long one.
    size: Annotated[Size, IOAttrs('size')] = Size.M
    size_long: Annotated[Size, IOAttrs('size_long')] = Size.M

    #: An optional choice -- a 'nothing' option ahead of the flavors.
    topping: Annotated[Flavor | None, IOAttrs('topping')] = None

    #: Choices over an arbitrary string set (the page defines the
    #: options, not an enum); plain and optional.
    difficulty: Annotated[str, IOAttrs('difficulty')] = 'normal'
    region: Annotated[str | None, IOAttrs('region')] = None

    #: Disabled choice rows (selectable; menus won't open), one of each
    #: form: enum, optional enum, str, optional str.
    flavor_disabled: Annotated[Flavor, IOAttrs('flavor_disabled')] = (
        Flavor.CHOCOLATE
    )
    topping_disabled: Annotated[Flavor | None, IOAttrs('topping_disabled')] = (
        None
    )
    difficulty_disabled: Annotated[str, IOAttrs('difficulty_disabled')] = 'hard'
    region_disabled: Annotated[str | None, IOAttrs('region_disabled')] = 'eu'

    #: A slider value shaped like the sound-settings ones -- 0-1 by 0.05.
    volume: Annotated[float, IOAttrs('volume')] = 0.5

    #: A disabled slider (selectable; not adjustable).
    volume_disabled: Annotated[float, IOAttrs('volume_disabled')] = 0.3

    #: A number-row value shaped like a series length -- 1-21 by 2.
    series_length: Annotated[float, IOAttrs('series_length')] = 7.0

    #: A disabled number row (selectable; not adjustable).
    series_length_disabled: Annotated[
        float, IOAttrs('series_length_disabled')
    ] = 5.0

    #: An rgb color, edited via the color-picker popup.
    tint: Annotated[tuple[float, float, float], IOAttrs('tint')] = (
        0.5,
        0.25,
        1.0,
    )

    #: A disabled color row (selectable; picker won't open).
    tint_disabled: Annotated[
        tuple[float, float, float], IOAttrs('tint_disabled')
    ] = (1.0, 0.6, 0.1)

    #: Checkboxes on rows demonstrating control-row spacing and header /
    #: footer bands (they drive nothing).
    spacing_top_demo: Annotated[bool, IOAttrs('spacing_top_demo')] = False
    spacing_bottom_demo: Annotated[bool, IOAttrs('spacing_bottom_demo')] = False
    bands_demo: Annotated[bool, IOAttrs('bands_demo')] = False


@ioprepped
@dataclass
class WebTestGet(TestRoute, path='/webtest/get'):
    """A page fetched from a web server via GET."""


@ioprepped
@dataclass
class WebTestPost(
    TestRoute, path='/webtest/post', method=dui2.RequestMethod.POST
):
    """A page fetched from a web server via POST."""


@ioprepped
@dataclass
class CloudMsgTestGet(TestRoute, path='/cloudmsgtest/get'):
    """A page fetched through our cloud connection via GET."""


@ioprepped
@dataclass
class CloudMsgTestPost(
    TestRoute, path='/cloudmsgtest/post', method=dui2.RequestMethod.POST
):
    """A page fetched through our cloud connection via POST."""


# All routes in the family. Handlers can match against this with
# assert_never to be sure they cover everything.
AnyTestRoute = (
    Root
    | Test2
    | Slow
    | TimedActions
    | DisplayItems
    | TextImages
    | LiveTimes
    | TextWrapping
    | Animation
    | Depictions
    | Viewers
    | Names
    | NinePatch
    | Glyphs
    | EmptyPage
    | BoundsTests
    | Widgets
    | NavTest
    | Drill
    | DrillLevel
    | Popups
    | PopupsMain
    | PopupsOther
    | Themes
    | ThemesPopup
    | Sections
    | ButtonGrids
    | WindowLayouts
    | LayoutFit
    | WebTestGet
    | WebTestPost
    | CloudMsgTestGet
    | CloudMsgTestPost
)


class TestLocalAction(DocUILocalActionBase):
    """Family class for doc-ui test local-actions."""

    @override
    @classmethod
    def get_action_types(cls) -> tuple[type[DocUILocalActionBase], ...]:
        return family_members(AnyTestLocalAction)


@ioprepped
@dataclass
class TestAction(TestLocalAction, name='testaction'):
    """Show a message proving we got here."""

    testparam: Annotated[int, IOAttrs('testparam')]


# All local-actions in the family (just the one for now).
@ioprepped
@dataclass
class ShowVolume(TestLocalAction, name='showvolume'):
    """Show the volume slider's live value (fired while dragging)."""


AnyTestLocalAction = TestAction | ShowVolume
