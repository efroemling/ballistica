# Released under the MIT License. See LICENSE for details.
#
"""Serving host-ui doc-ui pages (see :class:`HostUIHandler`)."""

import time
import inspect
import logging
from contextvars import ContextVar
from typing import TYPE_CHECKING, cast

from efro.error import CleanError
from efro.util import strip_exception_tracebacks
import bacommon.docui.v2 as dui2
from bacommon.langstr import LangStrSpecValue
from bacommon.docui.routes import DocUIRouteError
import bacommon.docui.routes.classichost as hroutes

import babase

if TYPE_CHECKING:
    from typing import Awaitable, Callable

    import bacommon.docui.v2

logger = logging.getLogger('ba.net')

#: Logic-thread time past which a page handler gets a warning (seconds).
#: A frame at 60fps is ~16ms, and a page that takes this long holds up
#: everything else the game does in the meantime.
SLOW_HANDLER_SECONDS = 0.01

# Time spent in run_in_bg() by the handler running in the current task.
_g_bg_time: ContextVar[list[float] | None] = ContextVar(
    '_g_bg_time', default=None
)

# Paths we've warned about being slow (once each per run).
_g_slow_warned_paths: set[str] = set()


class HostUIHandler:
    """Serves the doc-ui pages a host's buttons open.

    **Adding your own pages** takes three pieces: routes naming the
    pages, a handler serving them, and buttons opening them. A complete
    plugin-sized example::

        from dataclasses import dataclass

        from efro.dataclassio import ioprepped
        from bacommon.docui.routes import DocUIRoute, family_members
        import bacommon.docui.v2 as dui2
        from bacommon.langstr import LangStrSpecValue
        import babase
        import baclassic

        # 1. Routes: one family class, one dataclass per page (fields
        # are the page's args).
        class MyRoute(DocUIRoute):
            @classmethod
            def get_route_types(cls) -> tuple[type[DocUIRoute], ...]:
                return family_members(AnyMyRoute)

        @ioprepped
        @dataclass
        class Rules(MyRoute, path='/myplugin/rules'):
            pass

        AnyMyRoute = Rules

        # 2. A handler serving them (everything else goes to super()).
        class MyHandler(baclassic.HostUIHandler):
            def fulfill_request(self, request, client_id):
                try:
                    route = MyRoute.from_request(request)
                except Exception:
                    return super().fulfill_request(request, client_id)
                assert isinstance(route, Rules)
                lit = LangStrSpecValue.literal
                return dui2.Response(
                    page=dui2.Page(
                        title=lit('Rules'),
                        rows=[
                            dui2.ButtonRow(
                                title=lit('Be nice.'),
                                buttons=[
                                    dui2.Button(
                                        label=lit('Ok'),
                                        action=dui2.Local(close_window=True),
                                    )
                                ],
                            )
                        ],
                    )
                )

        # 3. Plug in: the handler, plus a button opening the page
        # (alongside the default ones).
        host_ui = babase.app.classic.host_ui
        host_ui.handler = MyHandler()
        host_ui.set_buttons(
            host_ui.get_buttons()
            + [baclassic.HostUIButton(label='Rules', route=Rules())]
        )

    To change the default stats page rather than add one, see
    :class:`baclassic.HostUIStatsPage`. If something goes wrong building
    a page (an exception, or returning something that isn't a response),
    the error is logged here and the client gets its standard error
    page.

    **Keeping pages cheap.** :meth:`fulfill_request` runs in the logic
    thread, the one the game itself runs in, so time spent there is
    time the game stands still. A page built from a handful of values
    costs next to nothing, and that's the common case. A page that
    grows (big tables, sorting or filtering many records, file or
    network access) should do the heavy part elsewhere:

    1. Make :meth:`fulfill_request` ``async``.
    2. Gather what you need from the game first, on the logic thread
       (game objects such as players and activities may only be
       touched there), into plain values.
    3. Build the page from those values in a background thread with
       ``await self.run_in_bg(build_page, values)``. That function must
       not touch game objects or ui.

    Handlers that spend more than about 10 ms on the logic thread get a
    warning saying so. (Turning the page into wire
    data and compressing it already happens in the background.)
    """

    def fulfill_request(
        self, request: bacommon.docui.v2.Request, client_id: int
    ) -> bacommon.docui.v2.Response | Awaitable[bacommon.docui.v2.Response]:
        """Return the page for a request from a client.

        ``client_id`` is -1 for the host's own requests. Runs in the
        logic thread, so game state can be read freely; return an
        awaitable (or make this ``async``) to answer asynchronously.
        Remember that requests come from clients and are untrusted
        input.
        """
        # pylint: disable=cyclic-import
        from baclassic._hostuipages import fulfill_classic_host_route

        try:
            route = hroutes.ClassicHostRoute.from_request(request)
        except DocUIRouteError:
            logger.debug(
                'Host-ui request from client %d for unknown path %r.',
                client_id,
                request.path,
            )
            return status_response(dui2.ResponseStatus.UNKNOWN_ERROR)
        # The family class only promises *some* member of the family;
        # the union is exactly the set of members.
        return fulfill_classic_host_route(
            cast(hroutes.AnyClassicHostRoute, route), client_id
        )

    async def run_in_bg[T](self, call: Callable[[], T]) -> T:
        """Run a call in a background thread; return its result.

        For the heavy parts of building a page (see the class docs).
        ``call`` must not touch game objects or ui; hand it plain
        values gathered beforehand (``functools.partial`` or a lambda
        does that nicely). Time spent here doesn't count toward the
        slow-handler warning.
        """
        start = time.monotonic()
        try:
            return await babase.app.asyncio_loop.run_in_executor(
                babase.app.threadpool, call
            )
        finally:
            spent = _g_bg_time.get()
            if spent is not None:
                spent[0] += time.monotonic() - start


def run_handler(
    handler: HostUIHandler,
    request: bacommon.docui.v2.Request,
    client_id: int,
    on_done: Callable[[bacommon.docui.v2.Response], None],
) -> None:
    """Run a handler for a request; call on_done with its response.

    Errors become error responses. Must be called in the logic thread;
    ``on_done`` is too.

    :meta private:
    """
    start = time.monotonic()
    try:
        result = handler.fulfill_request(request, client_id)
    except Exception as exc:
        _log_handler_error(exc, client_id)
        on_done(status_response(dui2.ResponseStatus.UNKNOWN_ERROR))
        strip_exception_tracebacks(exc)
        return
    if inspect.isawaitable(result):
        babase.app.create_async_task(
            _await_handler(result, request.path, client_id, start, on_done)
        )
    else:
        _check_slow(request.path, time.monotonic() - start)
        on_done(_checked_response(result, request.path))


def status_response(
    status: bacommon.docui.v2.ResponseStatus,
) -> bacommon.docui.v2.Response:
    """A page-less response with just a status.

    :meta private:
    """
    return dui2.Response(
        page=dui2.Page(title=LangStrSpecValue.literal(''), rows=[]),
        status=status,
    )


async def _await_handler(
    result: Awaitable[dui2.Response],
    path: str,
    client_id: int,
    start: float,
    on_done: Callable[[dui2.Response], None],
) -> None:
    # Count what the handler spends in run_in_bg() so it can be left
    # out of its logic-thread time.
    bg_time = [0.0]
    _g_bg_time.set(bg_time)
    try:
        response = await result
    except Exception as exc:
        _log_handler_error(exc, client_id)
        on_done(status_response(dui2.ResponseStatus.UNKNOWN_ERROR))
        strip_exception_tracebacks(exc)
        return
    # (Approximate: other awaiting, say on the network, counts too.)
    _check_slow(path, time.monotonic() - start - bg_time[0])
    on_done(_checked_response(response, path))


def _checked_response(result: object, path: str) -> dui2.Response:
    """A handler's result if it's a response; an error response if not."""
    if isinstance(result, dui2.Response):
        return result
    logger.error(
        "Host-ui handler for '%s' returned %s, not a"
        ' bacommon.docui.v2.Response; sending an error page.',
        path,
        type(result).__name__,
    )
    return status_response(dui2.ResponseStatus.UNKNOWN_ERROR)


def _check_slow(path: str, seconds: float) -> None:
    """Nudge authors of slow handlers toward building pages off-thread."""
    if seconds <= SLOW_HANDLER_SECONDS or path in _g_slow_warned_paths:
        return
    _g_slow_warned_paths.add(path)
    logger.warning(
        "Host-ui page '%s' took %.0f ms on the logic thread, during which"
        ' the game stood still. Build big pages in the background: make'
        ' fulfill_request() async and do the heavy part with'
        " 'await self.run_in_bg(...)' (see baclassic.HostUIHandler).",
        path,
        seconds * 1000.0,
    )


def _log_handler_error(exc: Exception, client_id: int) -> None:
    if isinstance(exc, CleanError):
        logger.warning('Host-ui page for client %d failed: %s', client_id, exc)
    else:
        logger.exception('Error serving host-ui page to client %d.', client_id)
