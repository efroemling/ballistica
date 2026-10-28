# Released under the MIT License. See LICENSE for details.
#
"""Type-safe doc-ui popup windows and the parents they act on."""

from dataclasses import dataclass
from typing import TYPE_CHECKING, override, get_args, get_origin

import bacommon.docui.v2 as dui2
from bacommon.docui.walk import page_actions
from bacommon.docui.routes._base import DocUIRoute
from bacommon.docui.routes._state import (
    DocUIState,
    STATE_TYPE_KEY,
    merge_assigns,
    validate_page_state,
)

if TYPE_CHECKING:
    from typing import Any, Sequence

    import bacommon.docui.v2
    from bacommon.docui.routes._state import DocUIStateAssign


# Parent state types of popup routes, by the class declaring them (see
# PopupRoute.__init_subclass__). Kept out here rather than as a class
# attribute because dataclassio would try to prep an annotated one as
# part of our dataclass children (and mypy wants it annotated).
_g_parent_state_types: dict[type, type[DocUIState]] = {}


# (A mixin beside a family class, which supplies get_route_types().)
# pylint: disable-next=abstract-method
class PopupRoute[S: DocUIState](DocUIRoute):
    """A route whose page is shown in a popup over a parent page.

    Mixed in next to a domain's family class, naming the state type of
    the page(s) the popup opens over:
    ``class SortMenu(StoreRoute, PopupRoute[ListingState], path=...)``.
    That type is what the popup may act on: its
    :meth:`parent` builds actions applying to the parent (setting keys
    of ``S``), and :meth:`get_parent_state` reads the parent's current
    state. Pages opening the popup must hold state of type ``S``; that
    and the rules for what a popup page may contain are checked when
    pages are validated (see :func:`validate_route_page`).

    Open one with :meth:`popup`.
    """

    @override
    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        # Pick up S from a 'PopupRoute[Foo]' on our own class line;
        # subclasses of that class simply inherit it.
        for base in cls.__dict__.get('__orig_bases__', ()):
            if get_origin(base) is PopupRoute:
                (arg,) = get_args(base)
                if isinstance(arg, type) and issubclass(arg, DocUIState):
                    _g_parent_state_types[cls] = arg

    @classmethod
    def get_parent_state_type(cls) -> type[S]:
        """Return the state type of the page this popup opens over."""
        statetype = next(
            (
                _g_parent_state_types[c]
                for c in cls.__mro__
                if c in _g_parent_state_types
            ),
            None,
        )
        if statetype is None:
            raise TypeError(
                f'{cls.__name__} declares no parent state type'
                f' (PopupRoute[SomeState] on its class line).'
            )
        # (Set from our own type arg; see __init_subclass__.)
        return statetype  # type: ignore[return-value]

    @classmethod
    def parent(cls) -> PopupParent[S]:
        """Return a handle for building actions acting on our parent."""
        return PopupParent(cls.get_parent_state_type())

    @classmethod
    def get_popup_size(cls) -> tuple[float, float]:
        """Content-area size (width, height) our popups open at.

        In window units (see :attr:`bacommon.docui.v2.Popup.size`), at
        least :data:`~bacommon.docui.v2.POPUP_MIN_SIZE`; clients shrink
        whatever doesn't fit their screen. Override to suit the page;
        :meth:`~bacommon.docui.routes.PopupRoute.popup` can also be told
        otherwise per link.
        """
        return (500.0, 300.0)

    def popup(
        self,
        *,
        default_sound: bool = True,
        sets: Sequence[DocUIStateAssign[S]] | None = None,
        size: tuple[float, float] | None = None,
        show_title: bool = False,
        show_close_button: bool = False,
        dim_background: bool = True,
        scroll_edge_style: bacommon.docui.v2.ScrollEdgeStyle = (
            dui2.ScrollEdgeStyle.FADE
        ),
        background_color: tuple[float, float, float] | None = None,
        cancel_button_color: tuple[float, float, float] | None = None,
    ) -> bacommon.docui.v2.Popup:
        """Return an action opening this route's page in a popup.

        The pressing page (whose state must be of our parent state
        type) is the popup's parent; any ``sets`` are applied to its
        state first, and that state goes along with the request (and
        every later one fired from the popup). The popup's content
        area is ``size``, or :meth:`get_popup_size` if not given; the
        rest is as for :class:`bacommon.docui.v2.Popup`.

        Only clients from :data:`bacommon.docui.v2.POPUP_BUILD` on can
        show popups; gate links to them on
        :func:`bacommon.docui.v2.supports_popups`.
        """
        if size is None:
            size = self.get_popup_size()
        lo = dui2.POPUP_MIN_SIZE
        if not (lo[0] <= size[0] and lo[1] <= size[1]):
            raise ValueError(
                f'Popup size {size} is smaller than {lo}'
                f' ({type(self).__name__}).'
            )
        return dui2.Popup(
            self.request(),
            default_sound=default_sound,
            sets=merge_assigns(sets),
            parent_state_id=self.get_parent_state_type().get_state_id(),
            size=size,
            show_title=show_title,
            show_close_button=show_close_button,
            dim_background=dim_background,
            scroll_edge_style=scroll_edge_style,
            background_color=background_color,
            cancel_button_color=cancel_button_color,
        )

    def get_parent_state(self) -> S | None:
        """Return the parent page's state as it arrived with our request.

        As with :meth:`~bacommon.docui.routes.DocUIRoute.get_state`,
        this is always optional input: None when absent, of another
        type, or undecodable.
        """
        src = self.get_source_request()
        return self.get_parent_state_type().decode(
            None if src is None else src.parent_state
        )


@dataclass(frozen=True)
class PopupParent[S: DocUIState]:
    """Builds a popup's actions that act on the page it is over.

    Get one from :meth:`PopupRoute.parent`. Every action here closes
    the popup; the parent then does what the action says, as though
    pressed there. A link that would read ``Foo().replace()`` on the
    parent page reads ``parent.replace(Foo())`` in the popup.
    """

    #: State type of the parent page.
    state_type: type[S]

    def dismiss(self, *, default_sound: bool = True) -> bacommon.docui.v2.Local:
        """Close the popup, leaving the parent alone."""
        return dui2.Local(close_window=True, default_sound=default_sound)

    def refresh(
        self, *assigns: DocUIStateAssign[S], default_sound: bool = True
    ) -> bacommon.docui.v2.Local:
        """Close the popup and refresh the parent.

        Any ``assigns`` are applied to the parent's state first.
        """
        values = merge_assigns(assigns) or {}
        values[STATE_TYPE_KEY] = self.state_type.get_state_id()
        return dui2.Local(
            close_window=True,
            refresh_parent=True,
            return_sets=values,
            default_sound=default_sound,
        )

    def replace(
        self,
        route: DocUIRoute,
        *,
        sets: Sequence[DocUIStateAssign[S]] | None = None,
        state: DocUIState | None = None,
        default_sound: bool = True,
    ) -> bacommon.docui.v2.Local:
        """Close the popup; the parent replaces its page with a route.

        ``sets`` and ``state`` are as for
        :meth:`~bacommon.docui.routes.DocUIRoute.replace`, with
        ``sets`` applying to the parent's state.
        """
        return self.run(
            route.replace(default_sound=False, sets=sets, state=state),
            default_sound=default_sound,
        )

    def browse(
        self,
        route: DocUIRoute,
        *,
        sets: Sequence[DocUIStateAssign[S]] | None = None,
        state: DocUIState | None = None,
        layout: bacommon.docui.v2.WindowLayout | None = None,
        default_sound: bool = True,
    ) -> bacommon.docui.v2.Local:
        """Close the popup; the parent browses to a route.

        As for :meth:`~bacommon.docui.routes.DocUIRoute.browse`, with
        ``sets`` applying to the parent's state.
        """
        return self.run(
            route.browse(
                default_sound=False, sets=sets, state=state, layout=layout
            ),
            default_sound=default_sound,
        )

    def close(self, *, default_sound: bool = True) -> bacommon.docui.v2.Local:
        """Close the popup and the parent's window too."""
        return self.run(
            dui2.Local(close_window=True, default_sound=False),
            default_sound=default_sound,
        )

    def close_to(
        self,
        route_type: type[DocUIRoute],
        *assigns: DocUIStateAssign[DocUIState],
        default_sound: bool = True,
    ) -> bacommon.docui.v2.Local:
        """Close the popup, then close the parent back to a route.

        As :meth:`~bacommon.docui.routes.DocUIRoute.close_to` would if
        pressed on the parent (``assigns`` go to the page closed back
        to, so may be of any one state type).
        """
        return self.run(
            route_type.close_to(*assigns, default_sound=False),
            default_sound=default_sound,
        )

    def run(
        self, action: bacommon.docui.v2.Action, *, default_sound: bool = True
    ) -> bacommon.docui.v2.Local:
        """Close the popup; the parent runs an arbitrary action.

        The escape hatch for anything the other methods don't cover (a
        local-action's :meth:`local()
        <bacommon.docui.routes.DocUILocalActionBase.local>`, say). The
        action must be a browse, replace or local (not one acting on
        a parent itself); its ``sets`` apply to the parent's state.
        """
        _check_parent_action(action)
        return dui2.Local(
            close_window=True,
            parent_action=action,
            parent_state_id=self.state_type.get_state_id(),
            default_sound=default_sound,
        )


def _check_parent_action(action: dui2.Action) -> None:
    if not isinstance(action, (dui2.Browse, dui2.Replace, dui2.Local)):
        raise ValueError(
            f'A popup parent action must be a browse, replace or local;'
            f' got {type(action).__name__}.'
        )
    if isinstance(action, dui2.Local) and (
        action.parent_action is not None or action.refresh_parent
    ):
        raise ValueError('A popup parent action cannot act on a parent.')


def _check_popup_parent(
    action: dui2.Popup, parent_id: str | None, what: str
) -> None:
    if action.parent_state_id is not None and (
        action.parent_state_id != parent_id
    ):
        raise ValueError(
            f'Page opens a popup expecting a parent with state'
            f' {action.parent_state_id!r}, but its parent would be'
            f' {what}, with state {parent_id!r}.'
        )


def validate_popup_page(
    page: bacommon.docui.v2.Page, parent_state_type: type[DocUIState]
) -> None:
    """Make sure a page shown in a popup keeps to the popup rules.

    No :class:`~bacommon.docui.v2.Browse` (the parent browses
    instead), parent actions of the allowed kinds only, and everything
    aimed at the parent (``sets`` of its actions, values handed back)
    belonging to the parent's state type.
    """
    parent_id = parent_state_type.get_state_id()
    parent_keys = parent_state_type.get_keys()
    for act in page_actions(page, parent_actions=False):
        if isinstance(act, dui2.Popup):
            # Replaces this popup over the same parent.
            _check_popup_parent(act, parent_id, 'a popup')
            for key in act.sets or {}:
                if key not in parent_keys:
                    raise ValueError(
                        f'Popup page opens a popup setting key {key!r},'
                        f' which is not part of'
                        f' {parent_state_type.__name__}.'
                    )
            continue
        if isinstance(act, dui2.Browse):
            raise ValueError(
                'Popup pages cannot browse; browse from the parent'
                ' (PopupParent.browse()).'
            )
        if not isinstance(act, dui2.Local):
            continue
        if act.return_sets and act.close_window:
            if act.return_sets.get(STATE_TYPE_KEY) != parent_id:
                raise ValueError(
                    f'Popup page hands values back to a parent of state'
                    f' {act.return_sets.get(STATE_TYPE_KEY)!r}, but its'
                    f' parent is {parent_id!r}.'
                )
        if act.parent_action is None:
            continue
        _check_parent_action(act.parent_action)
        if act.parent_state_id != parent_id:
            raise ValueError(
                f'Popup page parent action expects state'
                f' {act.parent_state_id!r}, but its parent is'
                f' {parent_id!r}.'
            )
        assert isinstance(
            act.parent_action, (dui2.Browse, dui2.Replace, dui2.Local)
        )
        for key in act.parent_action.sets or {}:
            if key not in parent_keys:
                raise ValueError(
                    f'Popup page parent action sets key {key!r}, which'
                    f' is not part of {parent_state_type.__name__}.'
                )


def validate_route_page(
    route: DocUIRoute, page: bacommon.docui.v2.Page
) -> None:
    """Run every validation that applies to a route's page.

    :func:`~bacommon.docui.routes.validate_page_state`, plus
    :func:`validate_popup_page` for a popup route. Typed controllers
    and request handlers call this on every page they produce, so a
    misbuilt page fails on its first render rather than in the field.
    """
    if isinstance(route, PopupRoute):
        validate_page_state(page, in_popup=True)
        validate_popup_page(page, route.get_parent_state_type())
        return
    validate_page_state(page)
    # Popups opened from here must expect a parent of our state type.
    page_id = None if page.state is None else page.state.get(STATE_TYPE_KEY)
    for act in page_actions(page, parent_actions=False):
        if isinstance(act, dui2.Popup):
            _check_popup_parent(act, page_id, 'the page')
