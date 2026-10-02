# Released under the MIT License. See LICENSE for details.
#
"""Base classes for type-safe doc-ui routes and local-actions."""

from enum import Enum
from typing import TYPE_CHECKING, override, get_args

from efro.dataclassio import dataclass_to_dict, dataclass_from_dict

import bacommon.docui.v2 as dui2

if TYPE_CHECKING:
    from typing import Any, Self, Sequence

    from bacommon.docui.routes._state import DocUIState, DocUIStateAssign

    import bacommon.docui.v2


class DocUIRouteError(Exception):
    """A request or local-action could not be mapped to a typed form."""


def family_members(alias: Any) -> tuple[Any, ...]:
    """Return the classes making up a family's union alias.

    Handles the degenerate single-member case, where the 'union' is
    simply the one class.
    """
    # Any because union aliases have no useful static type; callers
    # narrow to their own family's type.
    members = get_args(alias)
    return members if members else (alias,)


class DocUIRoute:
    """A page in a doc-ui domain, with its args as dataclass fields.

    Doc-ui (v2) requests are a path string plus a dict of args on the
    wire. A route is a type-safe stand-in for one: each page a domain
    offers is an ``@ioprepped`` dataclass inheriting from that domain's
    *family* class (itself a direct child of this class). The dataclass'
    fields are the page's args; its path and request-method are given
    as keywords on its class line
    (``class Foo(FooFamily, path='/foo', method=POST)``).

    Page code never touches the path or args dict directly: authoring
    goes through the :meth:`browse` and :meth:`replace` verbs and
    handling goes through :meth:`from_request` (generally called on
    one's behalf by a controller or request-handler base class).

    Paths within a family are a closed set; anything variable belongs
    in args (no ``/item/<id>`` style paths). Routes are keyed on path
    *and* method, so a page and the POST that submits it can share a
    path.
    """

    # Set via class-line keywords; see __init_subclass__. (Left
    # un-annotated so dataclassio doesn't try to evaluate them as part
    # of our dataclass children.) An empty path means 'not concrete'.
    _path = ''
    _method = dui2.RequestMethod.GET

    # The request we were built from (when we were); its state and
    # trigger are not part of our identity but are still ours to report
    # (see get_state(), get_trigger(), get_source_request()). We are not
    # a dataclass, so this annotation never becomes a field of our
    # dataclass children; it does get *evaluated* when they are prepped
    # (get_type_hints walks the MRO), so it must resolve in this
    # module's globals -- hence dui2, not bacommon.docui.v2. (Not
    # guarded by TYPE_CHECKING: sphinx runs such blocks live.)
    _source_request: dui2.Request | None = None

    @override
    def __init_subclass__(
        cls,
        *,
        path: str | None = None,
        method: bacommon.docui.v2.RequestMethod = dui2.RequestMethod.GET,
        **kwargs: Any,
    ) -> None:
        # Python calls this for each subclass as it is defined, handing
        # us any keywords from its class line; this is what lets a
        # concrete route declare itself as
        # 'class Foo(FooFamily, path='/foo', method=POST)'. Family
        # classes simply pass nothing.
        super().__init_subclass__(**kwargs)
        if path is not None:
            cls._path = path
            cls._method = method

    @classmethod
    def get_path(cls) -> str:
        """Return the request path for this route."""
        if not cls._path:
            raise TypeError(f'{cls.__name__} is not a concrete route.')
        return cls._path

    @classmethod
    def get_method(cls) -> bacommon.docui.v2.RequestMethod:
        """Return the request method for this route."""
        return cls._method

    @classmethod
    def get_route_types(cls) -> tuple[type[DocUIRoute], ...]:
        """Return all concrete routes in this family.

        Must be overridden by each family class. A family generally
        defines a union alias of its routes (which also gives handlers
        ``assert_never`` exhaustiveness) and returns
        :func:`~bacommon.docui.routes.family_members` of it here.
        """
        raise NotImplementedError()

    def request(self) -> bacommon.docui.v2.Request:
        """Return the wire request for this route."""
        return dui2.Request(
            self.get_path(),
            method=self.get_method(),
            args=dataclass_to_dict(self),
        )

    @classmethod
    def get_window_layout(cls) -> bacommon.docui.v2.WindowLayout:
        """The layout windows browsing to this route open with.

        :meth:`~bacommon.docui.routes.DocUIRoute.browse` uses this
        unless told otherwise, so a route whose page is best shown at
        some layout declares it once rather than at every link.

        Defaults to :attr:`~bacommon.docui.v2.WindowLayout.WIDE`, which
        is the same size at every ui-scale, so a one-off page (a
        confirmation, a dialog) never ends up as a big mostly-empty
        window. :attr:`~bacommon.docui.v2.WindowLayout.LARGE`, which
        grows to fill more of the screen at medium/large ui-scale, is
        for pages built to use that room (store listings and the
        like), and they ask for it explicitly.
        """
        return dui2.WindowLayout.WIDE

    def browse(
        self,
        *,
        default_sound: bool = True,
        sets: Sequence[DocUIStateAssign] | None = None,
        state: DocUIState | None = None,
        layout: bacommon.docui.v2.WindowLayout | None = None,
    ) -> bacommon.docui.v2.Browse:
        """Return an action browsing to this route in a new window.

        The pressing page's state goes along with the request, with any
        ``sets`` applied to it. Pass ``state`` to send some other state
        entirely; generally what a different page expects. The window
        opens at ``layout``, or at :meth:`get_window_layout` if not
        given.
        """
        from bacommon.docui.routes._state import merge_assigns

        return dui2.Browse(
            self.request(),
            default_sound=default_sound,
            sets=merge_assigns(sets),
            state=None if state is None else state.encode(),
            layout=self.get_window_layout() if layout is None else layout,
        )

    def replace(
        self,
        *,
        default_sound: bool = True,
        sets: Sequence[DocUIStateAssign] | None = None,
        state: DocUIState | None = None,
    ) -> bacommon.docui.v2.Replace:
        """Return an action replacing the current page with this route.

        See :meth:`browse` for ``sets`` and ``state``.
        """
        from bacommon.docui.routes._state import merge_assigns

        return dui2.Replace(
            self.request(),
            default_sound=default_sound,
            sets=merge_assigns(sets),
            state=None if state is None else state.encode(),
        )

    def get_state[S: DocUIState](self, state_type: type[S]) -> S | None:
        """Return page state that arrived with the request for us.

        Only routes built from requests have any, and only when the
        page the request was fired from had state of this type;
        anything else gives None. State is always optional input, so
        callers need a story for that.
        """
        src = self._source_request
        return state_type.decode(None if src is None else src.state)

    def get_trigger(self) -> str | None:
        """State key of the input whose change fired our request, if any."""
        src = self._source_request
        return None if src is None else src.trigger

    def get_source_request(self) -> bacommon.docui.v2.Request | None:
        """Return the request we were built from, if we were.

        Unlike :meth:`request`, which only ever describes the route
        itself, this carries whatever else rode along with the request
        (page state, trigger). Something forwarding an incoming route
        elsewhere as-is wants those to go along too.
        """
        return self._source_request

    @classmethod
    def from_request(cls, request: bacommon.docui.v2.Request) -> Self:
        """Return the route in this family that a request maps to.

        Should be called on a family class. Raises
        :class:`DocUIRouteError` if the request does not map to a route
        in the family.
        """
        # A path can host a route per method (a page plus the POST that
        # submits it, say), so look for a match on both.
        path_matched = False
        for routetype in cls.get_route_types():
            if routetype.get_path() != request.path:
                continue
            path_matched = True
            if routetype.get_method() is not request.method:
                continue
            try:
                route = dataclass_from_dict(routetype, request.args)
            except Exception as exc:
                raise DocUIRouteError(
                    f'Invalid request args for path {request.path!r}.'
                ) from exc
            assert isinstance(route, cls)
            # (Ours to set; this is a fellow member of our family.)
            # pylint: disable=protected-access
            route._source_request = request
            return route
        if path_matched:
            raise DocUIRouteError(
                f'Invalid request method for path {request.path!r}.'
            )
        raise DocUIRouteError(f'Invalid request path {request.path!r}.')


class PressSound(Enum):
    """What a button plays when pressed to run a local-action.

    See
    :meth:`~bacommon.docui.routes.DocUILocalActionBase.get_press_sound`.
    """

    #: The standard click, for actions that stay on the page.
    CLICK = 'click'

    #: The standard ui swish, for actions that go somewhere -- open a
    #: window or a popup, say -- like a browse does.
    SWISH = 'swish'

    #: Nothing (the action handles any sound itself).
    NONE = 'none'


class DocUILocalActionBase:
    """A local-action in a doc-ui domain, with args as dataclass fields.

    The local-action analogue of :class:`DocUIRoute`: each named action
    a domain's client-side controller exposes is an ``@ioprepped``
    dataclass inheriting from that domain's family class (a direct
    child of this class).
    """

    # See DocUIRoute._path.
    _name = ''

    @override
    def __init_subclass__(
        cls, *, name: str | None = None, **kwargs: Any
    ) -> None:
        # See DocUIRoute.__init_subclass__.
        super().__init_subclass__(**kwargs)
        if name is not None:
            cls._name = name

    @classmethod
    def get_name(cls) -> str:
        """Return the wire name for this local-action."""
        if not cls._name:
            raise TypeError(f'{cls.__name__} is not a concrete local-action.')
        return cls._name

    @classmethod
    def get_press_sound(cls) -> PressSound:
        """What a button plays when pressed to run this local-action.

        Actions that stay on the page click (the default); override to
        return :attr:`~bacommon.docui.routes.PressSound.SWISH` for ones
        that go somewhere (open a window or popup). A press whose action has
        ``default_sound`` off plays nothing either way.
        """
        return PressSound.CLICK

    @classmethod
    def press_sound_for_name(cls, name: str) -> PressSound:
        """The press sound for the local-action in this family named so.

        Should be called on a family class. Unknown names click.
        """
        for actiontype in cls.get_action_types():
            if actiontype.get_name() == name:
                return actiontype.get_press_sound()
        return PressSound.CLICK

    @classmethod
    def get_action_types(cls) -> tuple[type[DocUILocalActionBase], ...]:
        """Return all concrete local-actions in this family.

        Must be overridden by each family class; see
        :meth:`~bacommon.docui.routes.DocUIRoute.get_route_types`.
        """
        raise NotImplementedError()

    def local(
        self,
        *,
        close_window: bool = False,
        default_sound: bool = True,
        sets: Sequence[DocUIStateAssign] | None = None,
    ) -> bacommon.docui.v2.Local:
        """Return an action running this local-action immediately.

        Any ``sets`` are applied to the pressing page's state first.
        """
        from bacommon.docui.routes._state import merge_assigns

        return dui2.Local(
            sets=merge_assigns(sets),
            close_window=close_window,
            default_sound=default_sound,
            immediate_local_action=self.get_name(),
            immediate_local_action_args=dataclass_to_dict(self),
        )

    def attach(self, response: bacommon.docui.v2.Response) -> None:
        """Have a response run this local-action when first received."""
        response.local_action = self.get_name()
        response.local_action_args = dataclass_to_dict(self)

    @classmethod
    def from_name_and_args(cls, name: str, args: dict) -> Self:
        """Return the local-action in this family matching a name + args.

        Should be called on a family class. Raises
        :class:`DocUIRouteError` if there is no match.
        """
        for actiontype in cls.get_action_types():
            if actiontype.get_name() != name:
                continue
            try:
                action = dataclass_from_dict(actiontype, args)
            except Exception as exc:
                raise DocUIRouteError(
                    f'Invalid args for local-action {name!r}.'
                ) from exc
            assert isinstance(action, cls)
            return action
        raise DocUIRouteError(f'Invalid local-action {name!r}.')


class NoLocalActions(DocUILocalActionBase):
    """Stock local-action family for domains that have none.

    Pair with :class:`typing.Never` as the local-action type arg.
    """

    @override
    @classmethod
    def get_action_types(cls) -> tuple[type[DocUILocalActionBase], ...]:
        return ()
