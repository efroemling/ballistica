# Released under the MIT License. See LICENSE for details.
#
"""Types used in prepping a doc-ui page for display.

Prepping involves doing as much math and layout work as possible in a
pre-pass (generally run in a background thread) so that the actual calls
made to instantiate the ui are as fast and minimal as possible.
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from typing import Callable

    import bacommon.docui.v2
    import bacommon.clienteffect
    from bacommon.langstr import LangStrSpec
    import bauiv1

    from bauiv1lib.docui._window import DocUIWindow


#: A usage-site line-wrap override for a native language-string
#: (min-lines, max-lines, max-chars-per-line; see
#: :class:`babase.LangStr`).
type WrapOverride = tuple[int, int | None, int | None]

#: The override turning a string's own wrap hints off, for text we
#: wrap ourselves: exactly one "line", which the splitter returns as
#: the whole text (explicit newlines included; only edge whitespace is
#: trimmed). Pinning max-lines to 1 also keeps the splitter's
#: line-count search trivial; leaving it unlimited would search every
#: count up to the number of break opportunities.
NO_WRAP: WrapOverride = (1, 1, None)


class NativeLangStrFn(Protocol):
    """Makes native handles for a payload's language-strings.

    Bound against the payload's package list. Pass ``wrap`` to
    override the string's own wrap hints -- :data:`NO_WRAP` for text
    prep wraps itself (row and section titles, subtitles and
    footnotes; popup text).
    """

    def __call__(
        self, lstr: LangStrSpec | int, /, *, wrap: WrapOverride | None = None
    ) -> bauiv1.LangStr: ...


class AnimTargetKind(Enum):
    """What sort of widget an animation target is.

    Decides which widget attrs an animation state maps onto.
    """

    #: An image widget (images, depictions): position is its
    #: bottom-left corner; scaling grows its size about its center.
    IMAGE = 'image'

    #: A text widget: position is its anchor; scaling scales the text.
    TEXT = 'text'

    #: A button widget: position is its bottom-left corner, size its
    #: unscaled size; scaling grows it about its center.
    BUTTON = 'button'


@dataclass
class AnimTargetPrep:
    """How to animate a decoration that carries an ``anim_id``.

    The widget's base (as-laid-out) geometry, which animation states
    are relative to.
    """

    anim_id: str
    kind: AnimTargetKind
    position: tuple[float, float]

    #: Image or (unscaled) button size; unused for text.
    size: tuple[float, float] = (0.0, 0.0)

    #: Text or button scale; unused for images.
    scale: float = 1.0

    #: Base opacity (an image's, or a text color's alpha).
    opacity: float = 1.0

    #: A text's base rgb (None for the widget default).
    color: tuple[float, float, float] | None = None


@dataclass
class DecorationPrep:
    """Prep for a decoration in a doc-ui."""

    #: Creates the widget, returning it (or None for a call that
    #: creates several).
    call: Callable[..., bauiv1.Widget | None]
    textures: dict[str, str]
    meshes: dict[str, str]
    highlight: bool

    #: Set for decorations that can be animated by client-effects.
    anim: AnimTargetPrep | None = None


@dataclass
class MenuPrep:
    """Prep for the menu a doc-ui button with a menu action pops up.

    One entry per menu item in each list, in display order.
    """

    #: Native handles for the items' labels.
    labels: list[bauiv1.LangStr]
    #: Which items show greyed out and can't be picked.
    disabled: list[bool]
    actions: list[bacommon.docui.v2.Action | None]
    #: Set for items whose action pops up text.
    popup_texts: list[PopupTextPrep | None]


@dataclass
class PopupTextPrep:
    """Prep for the text popup a doc-ui popup-text action shows.

    The text is wrapped and measured here, in prep (wrapping is for
    background threads only), so the popup can size itself to it.
    """

    #: Native handle for the (wrapped) text.
    text: bauiv1.LangStr
    #: The space the text gets, in the popup's own units: its measured
    #: size, except that height is capped (the text squishes to fit).
    width: float
    height: float


@dataclass
class ButtonPrep:
    """Prep for a button in a doc-ui."""

    buttoncall: Callable[..., bauiv1.Widget]
    buttoneditcall: Callable | None
    decorations: list[DecorationPrep]
    textures: dict[str, str]
    widgetid: str
    action: bacommon.docui.v2.Action | None
    #: What ``action`` pops up, when it is a menu or popup text.
    popup: MenuPrep | PopupTextPrep | None = None

    #: Set for buttons that can be animated by client-effects.
    anim: AnimTargetPrep | None = None


@dataclass
class ButtonControlPrep:
    """Prep for the label + button in a doc-ui button control row."""

    labelcall: Callable[..., bauiv1.Widget] | None
    button: ButtonPrep


@dataclass
class CheckboxPrep:
    """Prep for the checkbox in a doc-ui checkbox row."""

    call: Callable[..., bauiv1.Widget]
    #: Key of our value in the page's state.
    key: str
    on_change: bacommon.docui.v2.Action | None
    widgetid: str
    #: Center of the box itself (we span the whole row).
    box_center: tuple[float, float]


@dataclass
class TextInputPrep:
    """Prep for the label + text box in a doc-ui text-input row."""

    labelcall: Callable[..., bauiv1.Widget] | None
    boxcall: Callable[..., bauiv1.Widget]
    #: Key of our value in the page's state.
    key: str
    on_change: bacommon.docui.v2.Action | None
    on_submit: bacommon.docui.v2.Action | None
    widgetid: str
    #: Center of the box itself (we span the whole row).
    box_center: tuple[float, float]


@dataclass
class ChoicePrep:
    """Prep for the label + popup-menu in a doc-ui choice row."""

    labelcall: Callable[..., bauiv1.Widget] | None
    #: Kwargs for bauiv1lib.popup.PopupMenu (minus parent and calls).
    menu_kwargs: dict
    #: Native handles for the choices' labels (menu_kwargs refers to
    #: these; kept here to make the lifetime obvious).
    choice_labels: list[bauiv1.LangStr]
    #: Choice values, in display order (None being an optional's
    #: 'nothing' choice).
    choice_values: list[str | None]
    #: Which choices show greyed out and can't be picked (parallel to
    #: choice_values).
    choice_disabled: list[bool]
    #: Key of our value in the page's state.
    key: str
    on_change: bacommon.docui.v2.Action | None
    widgetid: str
    #: Center of the button itself (we span the whole row).
    button_center: tuple[float, float]
    #: The whole row is disabled (its menu button can't open).
    disabled: bool = False


@dataclass
class ColorPrep:
    """Prep for the label + swatch button in a doc-ui color row."""

    labelcall: Callable[..., bauiv1.Widget] | None
    #: The swatch button (minus parent, color, and calls).
    buttoncall: Callable[..., bauiv1.Widget]
    #: Key of our value in the page's state.
    key: str
    on_change: bacommon.docui.v2.Action | None
    widgetid: str
    #: Center of the swatch itself (we span the whole row); also where
    #: the picker pops up from.
    button_center: tuple[float, float]


@dataclass
class SliderPrep:
    """Prep for the label + value text + slider in a doc-ui slider row."""

    labelcall: Callable[..., bauiv1.Widget] | None
    #: The value readout (minus parent and text).
    valuecall: Callable[..., bauiv1.Widget]
    #: The slider (minus parent, value, and calls).
    slidercall: Callable[..., bauiv1.Widget]
    #: Key of our value in the page's state.
    key: str
    on_change: bacommon.docui.v2.Action | None
    on_drag: bacommon.docui.v2.Local | None
    drag_interval: float
    drag_delay: float
    as_percent: bool
    decimals: int
    min_value: float
    max_value: float
    increment: float
    widgetid: str
    #: Center of the slider itself (we span the whole row).
    slider_center: tuple[float, float]


@dataclass
class NumberPrep:
    """Prep for the label + value text + '-'/'+' buttons in a number row."""

    labelcall: Callable[..., bauiv1.Widget] | None
    #: The value readout (minus parent and text).
    valuecall: Callable[..., bauiv1.Widget]
    #: The '-' and '+' buttons (minus parent and calls).
    minuscall: Callable[..., bauiv1.Widget]
    pluscall: Callable[..., bauiv1.Widget]
    #: Key of our value in the page's state.
    key: str
    on_change: bacommon.docui.v2.Action | None
    as_percent: bool
    decimals: int
    min_value: float
    max_value: float
    increment: float
    #: Ids of the '-' and '+' buttons (the row's selectable widgets).
    minus_widgetid: str
    plus_widgetid: str
    #: The whole row is disabled (both buttons, whatever the value).
    disabled: bool = False


@dataclass
class RowPrep:
    """Prep for a row in a doc-ui.

    A row of buttons gets the h-scroll bits and buttons; a control row
    gets its particular control instead; a section marker gets only
    text and decorations (nothing selectable).
    """

    width: float
    height: float
    titlecalls: list[Callable[..., bauiv1.Widget]]
    hscrollcall: Callable[..., bauiv1.Widget] | None
    hscrolleditcall: Callable | None
    hsubcall: Callable[..., bauiv1.Widget] | None
    buttons: list[ButtonPrep]
    simple_culling_h: float
    decorations: list[DecorationPrep]
    #: How far above/below the row's selectable part to keep in view
    #: when it is selected: its titles and footnote, plus any section
    #: heading above / note below that attached itself to this row.
    show_buffer_top: float = 0.0
    show_buffer_bottom: float = 0.0
    #: A section marker: draws its text and decorations, but holds
    #: nothing selectable and takes no part in navigation.
    is_section: bool = False
    #: The row's full vertical extent in the page (top/bottom: header
    #: band to footer band, as its debug bounds show), once prepped.
    #: Sections back their rows by these.
    bounds_top: float = 0.0
    bounds_bottom: float = 0.0
    checkbox: CheckboxPrep | None = None
    textinput: TextInputPrep | None = None
    choice: ChoicePrep | None = None
    color: ColorPrep | None = None
    slider: SliderPrep | None = None
    number: NumberPrep | None = None
    buttoncontrol: ButtonControlPrep | None = None
    #: A static (non-scrolling) button row's buttons, left to right
    #: (laid out like a control row; see :func:`is_control_row`).
    staticbuttons: list[ButtonPrep] | None = None

    def is_control_row(self) -> bool:
        """Are we laid out like a control row (vs a row of buttons)?

        True for static button rows too: they share control rows'
        column placement, just without a label.
        """
        return (
            self.checkbox is not None
            or self.textinput is not None
            or self.choice is not None
            or self.color is not None
            or self.slider is not None
            or self.number is not None
            or self.buttoncontrol is not None
            or self.staticbuttons is not None
        )


@dataclass
class PagePrep:
    """Prep for a page in a doc-ui."""

    rootcall: Callable[..., bauiv1.Widget] | None
    rows: list[RowPrep]
    width: float
    height: float
    simple_culling_v: float
    center_vertically: bool
    show_scrollbar: bool
    #: Native language-string title handle.
    title: bauiv1.LangStr
    root_post_calls: list[Callable[[bauiv1.Widget], None]]
    #: Whether this page was prepped to appear with no transitions (a
    #: refresh in place, a back-nav to a page we already have). Carried
    #: here so instantiation can match -- a page that snaps in should
    #: snap its scroll position too rather than gliding to the restored
    #: selection.
    immediate: bool
    #: Effects to run when this page is first displayed, de-indexed
    #: ready to run. They ride here rather than being read back off the
    #: response because the response is cached un-de-indexed; prep is
    #: what produces the runnable form. Attached by the caller rather
    #: than built by :func:`~bauiv1lib.docui.prep.prep_page`, which
    #: preps a *page* -- effects belong to the response around it.
    #: Button-press effects need no equivalent: they hang off
    #: ButtonPrep.action, which already points into the de-indexed copy.
    client_effects: list[bacommon.clienteffect.Effect] = field(
        default_factory=list
    )
