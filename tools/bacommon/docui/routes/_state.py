# Released under the MIT License. See LICENSE for details.
#
"""Type-safe page state for doc-ui."""

from enum import Enum
from dataclasses import dataclass, fields
from types import NoneType, UnionType
from typing import (
    TYPE_CHECKING,
    Annotated,
    Union,
    cast,
    overload,
    override,
    get_origin,
    get_args,
)

from efro.util import strip_exception_tracebacks
from efro.dataclassio import (
    dataclass_to_dict,
    dataclass_from_dict,
    DataclassFieldLookup,
)

import bacommon.docui.v2 as dui2
from bacommon.docui.walk import flatten_action

if TYPE_CHECKING:
    from typing import Any, Self, Callable, Collection, Sequence
    from dataclasses import Field

    import bacommon.docui.v2
    from bacommon.langstr import LangStrSpec

#: Key holding a state's type id within its (flat) wire dict. Keys
#: starting with an underscore are reserved for such things.
STATE_TYPE_KEY = '_t'

# All state types by id. State ids travel with requests to whatever
# page they wind up at, so unlike route paths they must be unique
# across *all* domains; registering here is what enforces that.
_g_state_types: dict[str, type[DocUIState]] = {}


@dataclass
class DocUIStateAssign:
    """A value to be assigned into a page's state.

    Create these via :meth:`DocUIState.assign`.
    """

    state_type: type[DocUIState]
    key: str
    value: Any


def merge_assigns(assigns: Sequence[DocUIStateAssign] | None) -> dict | None:
    """Return the wire form for a set of assigns (or None for none)."""
    if not assigns:
        return None
    return {a.key: a.value for a in assigns}


def _encode_value(value: Any) -> Any:
    """Json form for a single state value."""
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, (tuple, list)):
        return [_encode_value(v) for v in value]
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    raise TypeError(f'Unsupported state value type: {type(value)}.')


class DocUIState:
    """Values belonging to a doc-ui page, as dataclass fields.

    Where route args say *which page* something is, state is what the
    user is in the middle of on it: the values its input rows show and
    edit plus anything else it wants handed back (a draft being
    composed, say). A page declares its state once and the client
    sends the current values along with every request fired from that
    page, so individual links need only say what they *change*.

    Subclasses are ``@ioprepped`` dataclasses declaring a globally
    unique id on their class line
    (``class Foo(DocUIState, state_id='mydomain.foo')``). The id rides
    along with the values so that state arriving at a page expecting
    some other type reads as no state at all instead of being
    mis-decoded. Field storage names must not start with an
    underscore.

    State is always optional input; a page must be able to make do
    without any (see :meth:`DocUIRoute.get_state
    <bacommon.docui.routes.DocUIRoute.get_state>`).
    """

    # Set via class-line keyword; see __init_subclass__. (Left
    # un-annotated so dataclassio doesn't try to evaluate it as part
    # of our dataclass children.)
    _state_id = ''

    @override
    def __init_subclass__(
        cls, *, state_id: str | None = None, **kwargs: Any
    ) -> None:
        super().__init_subclass__(**kwargs)
        if state_id is not None:
            existing = _g_state_types.get(state_id)
            # (Dataclass decorators can recreate a class, so allow
            # re-registering something with the same qualified name.)
            if existing is not None and (
                existing.__module__,
                existing.__qualname__,
            ) != (cls.__module__, cls.__qualname__):
                raise RuntimeError(
                    f'Doc-ui state id {state_id!r} is used by both'
                    f' {existing.__qualname__} and {cls.__qualname__}.'
                )
            cls._state_id = state_id
            _g_state_types[state_id] = cls

    @classmethod
    def get_state_id(cls) -> str:
        """Return the wire id for this state type."""
        if not cls._state_id:
            raise TypeError(f'{cls.__name__} declares no state_id.')
        return cls._state_id

    def encode(self) -> dict:
        """Return the wire form of this state (for ``Page.state`` etc.)."""
        out = dataclass_to_dict(self)
        assert isinstance(out, dict)
        for key in out:
            if key.startswith('_'):
                raise ValueError(
                    f'{type(self).__name__} has a field stored as {key!r};'
                    f' names starting with underscores are reserved.'
                )
        out[STATE_TYPE_KEY] = self.get_state_id()
        return out

    @classmethod
    def decode(cls, data: dict | None) -> Self | None:
        """Return state of this type from its wire form, if that it be.

        Returns None for no data, data for some other state type, or
        data that fails to decode. State comes from clients and is
        always optional, so none of those are errors.
        """
        if data is None or data.get(STATE_TYPE_KEY) != cls.get_state_id():
            return None
        try:
            return dataclass_from_dict(
                cls, {k: v for k, v in data.items() if not k.startswith('_')}
            )
        except Exception as exc:
            strip_exception_tracebacks(exc)
            return None

    @classmethod
    def _fields_by_key(cls) -> dict[str, Field]:
        """Return our dataclass fields keyed by their wire keys."""
        # Fine to be fast-and-loose with types here; cls is a dataclass
        # by the time anyone is calling this.
        return {
            cls.key(lambda s, n=f.name: getattr(s, n)): f  # type: ignore[misc]
            for f in fields(cls)  # type: ignore[arg-type]
        }

    @classmethod
    def get_keys(cls) -> set[str]:
        """Return the wire keys of all of our fields."""
        return set(cls._fields_by_key())

    @classmethod
    def key(cls, field: Callable[[Self], Any]) -> str:
        """Return the wire key for a field, given a lambda fetching it.

        ``MyState.key(lambda s: s.some_field)``
        """
        return DataclassFieldLookup(cls).path(field)

    @classmethod
    @overload
    @classmethod
    def assign[V](
        cls, field: Callable[[Self], V], value: V
    ) -> DocUIStateAssign: ...

    @overload
    @classmethod
    def assign[V](
        cls, field: Callable[[Self], V | None], value: V
    ) -> DocUIStateAssign: ...

    @classmethod
    def assign[V](
        cls, field: Callable[[Self], V | None], value: V
    ) -> DocUIStateAssign:
        """Return an assignment of a value to one of our fields.

        For passing as ``sets`` when creating actions:
        ``route.replace(sets=[MyState.assign(lambda s: s.color, c)])``.
        The value is type-checked against the field. (The second
        overload is what lets a plain ``E`` be assigned to an
        ``E | None`` field: mypy settles the type variable from the
        value before it looks at the lambda.)
        """
        key = cls.key(field)
        # Mypy lets None through for a non-optional field (it widens
        # the type variable to fit both args), so catch that here.
        if value is None and not _field_is_optional(cls, key):
            raise TypeError(f'State field {key!r} is not optional.')
        return DocUIStateAssign(cls, key, _encode_value(value))

    @classmethod
    def assign_locally(
        cls, *assigns: DocUIStateAssign, default_sound: bool = True
    ) -> bacommon.docui.v2.Local:
        """Return an action assigning values with no request involved.

        The values simply go out with whatever the page sends next.
        """
        del cls  # Just here for symmetry with assign().
        return dui2.Local(
            sets=merge_assigns(assigns), default_sound=default_sound
        )

    @classmethod
    def assign_on_return(
        cls, *assigns: DocUIStateAssign, default_sound: bool = True
    ) -> bacommon.docui.v2.Local:
        """Return an action closing the window, handing values back.

        For a picker opened in a window of its own: the window closes
        and the values are assigned into the state of the page returned
        to (which must hold our state type; the client checks), which
        then refreshes with them.
        """
        for assign in assigns:
            if assign.state_type is not cls:
                raise TypeError(
                    f'Assign for {assign.state_type.__name__} passed to'
                    f' {cls.__name__}.assign_on_return().'
                )
        values = merge_assigns(assigns) or {}
        values[STATE_TYPE_KEY] = cls.get_state_id()
        return dui2.Local(
            close_window=True,
            return_sets=values,
            default_sound=default_sound,
        )

    @classmethod
    def checkbox_row(
        cls,
        field: Callable[[Self], bool],
        *,
        label: LangStrSpec | None = None,
        title: LangStrSpec | None = None,
        subtitle: LangStrSpec | None = None,
        title_align: bacommon.docui.v2.HAlign | None = None,
        footnote: LangStrSpec | None = None,
        on_change: bacommon.docui.v2.Action | None = None,
        disabled: bool = False,
        debug: bool = False,
    ) -> bacommon.docui.v2.CheckboxRow:
        """Return a checkbox row editing one of our (bool) fields.

        ``disabled`` shows it dimmed and not toggleable (still
        selectable).
        """
        _check_on_change(on_change)
        return dui2.CheckboxRow(
            name=cls.key(field),
            label=label,
            title=title,
            subtitle=subtitle,
            title_align=title_align,
            footnote=footnote,
            on_change=on_change,
            disabled=disabled,
            debug=debug,
        )

    @classmethod
    @overload
    @classmethod
    def choice_row[E: Enum](
        cls,
        field: Callable[[Self], E],
        *,
        choice_label: Callable[[E], LangStrSpec],
        choices: Sequence[E] | None = None,
        disabled_choices: Collection[E] = (),
        label: LangStrSpec | None = None,
        title: LangStrSpec | None = None,
        subtitle: LangStrSpec | None = None,
        title_align: bacommon.docui.v2.HAlign | None = None,
        footnote: LangStrSpec | None = None,
        on_change: bacommon.docui.v2.Action | None = None,
        disabled: bool = False,
        debug: bool = False,
    ) -> bacommon.docui.v2.ChoiceRow: ...

    @overload
    @classmethod
    def choice_row[E: Enum](
        cls,
        field: Callable[[Self], E | None],
        *,
        choice_label: Callable[[E], LangStrSpec],
        none_label: LangStrSpec,
        choices: Sequence[E] | None = None,
        disabled_choices: Collection[E] = (),
        label: LangStrSpec | None = None,
        title: LangStrSpec | None = None,
        subtitle: LangStrSpec | None = None,
        title_align: bacommon.docui.v2.HAlign | None = None,
        footnote: LangStrSpec | None = None,
        on_change: bacommon.docui.v2.Action | None = None,
        disabled: bool = False,
        debug: bool = False,
    ) -> bacommon.docui.v2.ChoiceRow: ...

    @overload
    @classmethod
    def choice_row(
        cls,
        field: Callable[[Self], str],
        *,
        choices: Sequence[tuple[str, LangStrSpec]],
        disabled_choices: Collection[str] = (),
        label: LangStrSpec | None = None,
        title: LangStrSpec | None = None,
        subtitle: LangStrSpec | None = None,
        title_align: bacommon.docui.v2.HAlign | None = None,
        footnote: LangStrSpec | None = None,
        on_change: bacommon.docui.v2.Action | None = None,
        disabled: bool = False,
        debug: bool = False,
    ) -> bacommon.docui.v2.ChoiceRow: ...

    @overload
    @classmethod
    def choice_row(
        cls,
        field: Callable[[Self], str | None],
        *,
        choices: Sequence[tuple[str, LangStrSpec]],
        none_label: LangStrSpec,
        disabled_choices: Collection[str] = (),
        label: LangStrSpec | None = None,
        title: LangStrSpec | None = None,
        subtitle: LangStrSpec | None = None,
        title_align: bacommon.docui.v2.HAlign | None = None,
        footnote: LangStrSpec | None = None,
        on_change: bacommon.docui.v2.Action | None = None,
        disabled: bool = False,
        debug: bool = False,
    ) -> bacommon.docui.v2.ChoiceRow: ...

    @classmethod
    def choice_row[E: Enum](
        cls,
        field: Callable[[Self], E | str | None],
        *,
        choice_label: Callable[[E], LangStrSpec] | None = None,
        none_label: LangStrSpec | None = None,
        choices: Sequence[E] | Sequence[tuple[str, LangStrSpec]] | None = None,
        disabled_choices: Collection[E] | Collection[str] = (),
        label: LangStrSpec | None = None,
        title: LangStrSpec | None = None,
        subtitle: LangStrSpec | None = None,
        title_align: bacommon.docui.v2.HAlign | None = None,
        footnote: LangStrSpec | None = None,
        on_change: bacommon.docui.v2.Action | None = None,
        disabled: bool = False,
        debug: bool = False,
    ) -> bacommon.docui.v2.ChoiceRow:
        """Return a choice row editing one of our enum or str fields.

        For an enum field, ``choice_label`` gives each option's display
        text; write it as a ``match`` ending in ``assert_never`` so a
        new enum member can't go unlabeled. ``choices`` narrows/reorders
        the options shown (default: every member, in definition order).

        For a str field there is no closed set to be exhaustive over,
        so ``choices`` instead *defines* the options as ``(value,
        label)`` pairs, in display order; ``choice_label`` does not
        apply. The state's current value should be among them (a value
        that isn't shows as the first option).

        ``disabled_choices`` lists options to show greyed out and
        unpickable (enum members, or str values, matching how
        ``choices`` are given) -- each must be one of the options.
        ``disabled`` instead disables the whole row: shown dimmed with
        its menu unopenable (still selectable).

        A field typed ``E | None`` / ``str | None`` gets a 'nothing'
        option too, listed first, whose display text is ``none_label``
        -- required for such fields and not allowed for others. The
        type checker enforces the required halves of all this via the
        overloads; what it can't express (a stray ``none_label`` or
        ``choice_label``) is checked here at runtime along with the rest.
        """
        _check_on_change(on_change)
        key = cls.key(field)
        fieldtype, optional = _field_type(cls, key)
        if optional and none_label is None:
            raise TypeError(
                f'State field {key!r} is optional;'
                ' choice_row() needs a none_label for it.'
            )
        if not optional and none_label is not None:
            raise TypeError(
                f'State field {key!r} is not optional;'
                ' choice_row() takes no none_label for it.'
            )
        wirechoices: list[dui2.Choice] = []
        if none_label is not None:
            wirechoices.append(dui2.Choice(value=None, label=none_label))
        if fieldtype is str:
            if choice_label is not None or choices is None:
                raise TypeError(
                    f'State field {key!r} is a str; choice_row() takes'
                    ' (value, label) choices for it and no choice_label.'
                )
            pairs = cast('Sequence[tuple[str, LangStrSpec]]', choices)
            wirechoices += [
                dui2.Choice(value=value, label=lbl) for value, lbl in pairs
            ]
        elif isinstance(fieldtype, type) and issubclass(fieldtype, Enum):
            if choice_label is None:
                raise TypeError(
                    f'State field {key!r} is an enum; choice_row() needs'
                    ' a choice_label for it.'
                )
            # (mypy can't tie the looked-up enum type back to E, hence
            # the casts; the lookup verified the field is an enum.)
            members = (
                cast('Sequence[E]', choices)
                if choices is not None
                else cast('list[E]', list(fieldtype))
            )
            wirechoices += [
                dui2.Choice(value=str(m.value), label=choice_label(m))
                for m in members
            ]
        else:
            raise TypeError(f'State field {key!r} is not an enum or str.')
        values = [c.value for c in wirechoices]
        if len(set(values)) != len(values):
            raise ValueError(f'Duplicate choice values for {key!r}.')

        # Grey out what's disabled (enum members or str values, as the
        # choices themselves are given).
        disabled_values = {
            str(d.value) if isinstance(d, Enum) else d for d in disabled_choices
        }
        if not disabled_values <= set(values):
            raise ValueError(
                f'Disabled choices {sorted(disabled_values - set(values))}'
                f' are not among the choices for {key!r}.'
            )
        for choice in wirechoices:
            if choice.value in disabled_values:
                choice.disabled = True
        return dui2.ChoiceRow(
            name=cls.key(field),
            choices=wirechoices,
            label=label,
            title=title,
            subtitle=subtitle,
            title_align=title_align,
            footnote=footnote,
            on_change=on_change,
            disabled=disabled,
            debug=debug,
        )

    @classmethod
    def color_row(
        cls,
        field: Callable[[Self], tuple[float, float, float]],
        *,
        label: LangStrSpec | None = None,
        title: LangStrSpec | None = None,
        subtitle: LangStrSpec | None = None,
        title_align: bacommon.docui.v2.HAlign | None = None,
        footnote: LangStrSpec | None = None,
        on_change: bacommon.docui.v2.Action | None = None,
        disabled: bool = False,
        debug: bool = False,
    ) -> bacommon.docui.v2.ColorRow:
        """Return a color row editing one of our rgb fields.

        The field must be typed ``tuple[float, float, float]`` (0-1
        components). ``on_change`` fires when the picker closes with a
        changed color, not per intermediate change. ``disabled`` shows
        it dimmed with its picker unopenable (still selectable).
        """
        _check_on_change(on_change)
        key = cls.key(field)
        fieldtype, optional = _field_type(cls, key)
        if optional or not (
            get_origin(fieldtype) is tuple
            and get_args(fieldtype) == (float, float, float)
        ):
            raise TypeError(
                f'State field {key!r} is not a tuple[float, float, float].'
            )
        return dui2.ColorRow(
            name=key,
            label=label,
            title=title,
            subtitle=subtitle,
            title_align=title_align,
            footnote=footnote,
            on_change=on_change,
            disabled=disabled,
            debug=debug,
        )

    @classmethod
    def number_row(
        cls,
        field: Callable[[Self], float],
        *,
        min_value: float,
        max_value: float,
        increment: float,
        as_percent: bool = False,
        decimals: int = 0,
        label: LangStrSpec | None = None,
        title: LangStrSpec | None = None,
        subtitle: LangStrSpec | None = None,
        title_align: bacommon.docui.v2.HAlign | None = None,
        footnote: LangStrSpec | None = None,
        on_change: bacommon.docui.v2.Action | None = None,
        disabled: bool = False,
        debug: bool = False,
    ) -> bacommon.docui.v2.NumberRow:
        """Return a '-'/'+' number row editing one of our float fields.

        ``on_change`` fires on each press that changes the value.
        ``disabled`` shows it dimmed and not adjustable (still
        selectable). See :class:`bacommon.docui.v2.NumberRow`.
        """
        _check_on_change(on_change)
        key = cls.key(field)
        fieldtype, optional = _field_type(cls, key)
        if optional or fieldtype is not float:
            raise TypeError(f'State field {key!r} is not a float.')
        if not min_value < max_value or increment <= 0.0:
            raise ValueError(f'Invalid number range for {key!r}.')
        return dui2.NumberRow(
            name=key,
            min_value=min_value,
            max_value=max_value,
            increment=increment,
            as_percent=as_percent,
            decimals=decimals,
            label=label,
            title=title,
            subtitle=subtitle,
            title_align=title_align,
            footnote=footnote,
            on_change=on_change,
            disabled=disabled,
            debug=debug,
        )

    @classmethod
    def slider_row(
        cls,
        field: Callable[[Self], float],
        *,
        min_value: float,
        max_value: float,
        increment: float,
        as_percent: bool = False,
        decimals: int = 2,
        label: LangStrSpec | None = None,
        title: LangStrSpec | None = None,
        subtitle: LangStrSpec | None = None,
        title_align: bacommon.docui.v2.HAlign | None = None,
        footnote: LangStrSpec | None = None,
        on_change: bacommon.docui.v2.Action | None = None,
        on_drag: bacommon.docui.v2.Local | None = None,
        drag_interval: float = 0.25,
        drag_delay: float = 0.0,
        disabled: bool = False,
        debug: bool = False,
    ) -> bacommon.docui.v2.SliderRow:
        """Return a slider row editing one of our float fields.

        ``on_change`` fires for a settled value (release, or a run of
        key/controller steps going quiet); ``on_drag`` -- a local
        action, built via ``MyAction().local()`` -- fires during a drag
        (key/controller steps included) at the throttled
        cadence ``drag_interval`` / ``drag_delay`` describe, reading
        the live value from the page's state. ``disabled`` shows it
        dimmed and not adjustable (still selectable). See
        :class:`bacommon.docui.v2.SliderRow`.
        """
        _check_on_change(on_change)
        key = cls.key(field)
        fieldtype, optional = _field_type(cls, key)
        if optional or fieldtype is not float:
            raise TypeError(f'State field {key!r} is not a float.')
        if not min_value < max_value or increment <= 0.0:
            raise ValueError(f'Invalid slider range for {key!r}.')
        return dui2.SliderRow(
            name=key,
            min_value=min_value,
            max_value=max_value,
            increment=increment,
            as_percent=as_percent,
            decimals=decimals,
            label=label,
            title=title,
            subtitle=subtitle,
            title_align=title_align,
            footnote=footnote,
            on_change=on_change,
            on_drag=on_drag,
            drag_interval=drag_interval,
            drag_delay=drag_delay,
            disabled=disabled,
            debug=debug,
        )

    @classmethod
    def text_input_row(
        cls,
        field: Callable[[Self], str],
        *,
        label: LangStrSpec | None = None,
        title: LangStrSpec | None = None,
        subtitle: LangStrSpec | None = None,
        title_align: bacommon.docui.v2.HAlign | None = None,
        footnote: LangStrSpec | None = None,
        description: LangStrSpec | None = None,
        max_chars: int = 64,
        on_change: bacommon.docui.v2.Action | None = None,
        on_submit: bacommon.docui.v2.Action | None = None,
        disabled: bool = False,
        debug: bool = False,
    ) -> bacommon.docui.v2.TextInputRow:
        """Return a text-input row editing one of our (str) fields.

        ``disabled`` shows it dimmed and not editable (still
        selectable).
        """
        _check_on_change(on_change)
        return dui2.TextInputRow(
            name=cls.key(field),
            label=label,
            title=title,
            subtitle=subtitle,
            title_align=title_align,
            footnote=footnote,
            description=description,
            max_chars=max_chars,
            on_change=on_change,
            on_submit=on_submit,
            disabled=disabled,
            debug=debug,
        )


def _field_type(statetype: type[DocUIState], key: str) -> tuple[Any, bool]:
    """Return a state field's type with any ``| None`` peeled off.

    The bool says whether it was peeled (the field is optional). Our
    fields are ``Annotated[T, IOAttrs(...)]``; ioprepped has already
    evaluated them for us.
    """
    # pylint: disable=protected-access
    anntype = statetype._fields_by_key()[key].type
    if get_origin(anntype) is Annotated:
        anntype = get_args(anntype)[0]
    if get_origin(anntype) in (Union, UnionType):
        args = get_args(anntype)
        nonnone = [a for a in args if a is not NoneType]
        if len(args) == 2 and len(nonnone) == 1:
            return nonnone[0], True
    return anntype, False


def _field_is_optional(statetype: type[DocUIState], key: str) -> bool:
    """Whether a state field is typed ``T | None``."""
    return _field_type(statetype, key)[1]


def _check_on_change(on_change: bacommon.docui.v2.Action | None) -> None:
    if isinstance(on_change, (dui2.Browse, dui2.Menu, dui2.PopupText)):
        raise ValueError(
            'on_change actions cannot open windows, menus or popups.'
        )


def validate_page_state(page: bacommon.docui.v2.Page) -> None:
    """Make sure a page's use of its state hangs together.

    Checks that everything referring to the page's state by key
    (input rows, ``sets`` on actions) names a real field of the state
    type the page declares. Those are all produced by type-checked
    calls, but nothing static ties them to the *same* state type as
    the page's, so that part gets checked here. Pages whose state is
    of no type known to us (third party ones, say) are left alone.
    """
    keys_used: list[tuple[str, str]] = []

    def _action(action: dui2.Action | None, where: str) -> None:
        # (A menu's items' actions included.)
        for act in flatten_action(action):
            if isinstance(act, (dui2.Browse, dui2.Replace, dui2.Local)):
                for key in act.sets or {}:
                    keys_used.append((key, where))

    # (Rows inside sections count too.)
    for row in dui2.all_rows(page.rows):
        if isinstance(row, dui2.CheckboxRow):
            keys_used.append((row.name, 'a checkbox row'))
            _action(row.on_change, 'a checkbox row on_change')
        elif isinstance(row, dui2.TextInputRow):
            keys_used.append((row.name, 'a text-input row'))
            _action(row.on_change, 'a text-input row on_change')
        elif isinstance(row, dui2.ChoiceRow):
            keys_used.append((row.name, 'a choice row'))
            _action(row.on_change, 'a choice row on_change')
        elif isinstance(row, dui2.ColorRow):
            keys_used.append((row.name, 'a color row'))
            _action(row.on_change, 'a color row on_change')
        elif isinstance(row, dui2.SliderRow):
            keys_used.append((row.name, 'a slider row'))
            _action(row.on_change, 'a slider row on_change')
            _action(row.on_drag, 'a slider row on_drag')
        elif isinstance(row, dui2.NumberRow):
            keys_used.append((row.name, 'a number row'))
            _action(row.on_change, 'a number row on_change')
        elif isinstance(row, dui2.ButtonControlRow):
            _action(row.button.action, 'a button action')
        elif isinstance(row, dui2.ButtonRow):
            for button in row.buttons:
                _action(button.action, 'a button action')

    if page.state is None:
        if keys_used:
            raise ValueError(
                f'Page has no state but {keys_used[0][1]} refers to'
                f' state key {keys_used[0][0]!r}.'
            )
        return

    state_type = _g_state_types.get(page.state.get(STATE_TYPE_KEY, ''))
    if state_type is None:
        return
    valid = state_type.get_keys()
    for key, where in keys_used:
        if key not in valid:
            raise ValueError(
                f'Page state is a {state_type.__name__} but {where}'
                f' refers to key {key!r}, which is not part of it'
                f' (bound to a different state type?).'
            )
