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
class Sections(TestRoute, path='/sections'):
    """Sections: headings, notes, backings and spacing between them."""

    debug: Annotated[bool, IOAttrs('debug', store_default=False)] = False

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

    #: Which side the page's viewer pane sits on at viewer layouts, or
    #: None for a page with no viewer (its rows then span the window).
    #: Ignored at other layouts.
    viewer_side: Annotated[
        dui2.ViewerSide | None, IOAttrs('vside', store_default=False)
    ] = None


@ioprepped
@dataclass
class WideFit(TestRoute, path='/widefit'):
    """A row exactly as big as wide pages get (browse at each layout).

    It should fill the page's height and width with no scrolling, at
    every ui-scale; with ``over`` / ``wide_over`` set it's a hair
    taller / wider, which should scroll (at small ui-scale, only on the
    smallest screens: windows there fill the screen, so the page sizes
    are minimums). ``layout`` says which wide
    layout it's being shown in (browse at that one): wide and wider
    pages are the same height everywhere, wide-tall ones depend on the
    ui-scale and wide-taller ones on the screen too; wider's width
    follows the screen, so there's no width to overflow there.
    """

    over: Annotated[bool, IOAttrs('over', store_default=False)] = False
    wide_over: Annotated[bool, IOAttrs('wo', store_default=False)] = False
    layout: Annotated[
        dui2.WindowLayout,
        IOAttrs(
            'lo', store_default=False, enum_fallback=dui2.WindowLayout.WIDE
        ),
    ] = dui2.WindowLayout.WIDE


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
    | EmptyPage
    | BoundsTests
    | Widgets
    | NavTest
    | Sections
    | ButtonGrids
    | WindowLayouts
    | WideFit
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
