# Released under the MIT License. See LICENSE for details.
#
"""Native Python REPL that executes code on the logic thread.

Input (line editing, history, completion, multi-line blocks) is handled
on the stdin thread by Python's own interactive console machinery, but
each compiled statement is shipped to the logic thread to run, so
engine APIs work as they would anywhere else in the app. This is the
same split ``python -m asyncio`` uses, and like it we compile with
top-level ``await`` allowed; awaited coroutines run as tasks on the
logic thread's asyncio loop alongside everything else.
"""

import ast
import builtins
import sys
import code
import types
import inspect
import importlib
import threading
import concurrent.futures
from typing import TYPE_CHECKING, override

import _babase

if TYPE_CHECKING:
    from typing import Any, Generator
    import asyncio

    import babase


async def _run_in_context(
    coro: types.CoroutineType[Any, Any, Any], ctx: babase.ContextRef
) -> Any:
    """Run a coroutine with a ballistica context set for each step.

    Asyncio tasks on the logic thread resume with an empty ballistica
    context, so without this anything after the first ``await`` in a
    REPL statement would lose the foreground context.
    """
    return await _context_steps(coro, ctx)


@types.coroutine
def _context_steps(
    coro: types.CoroutineType[Any, Any, Any], ctx: babase.ContextRef
) -> Generator[Any, Any, Any]:
    step, arg = coro.send, None
    while True:
        with ctx:
            try:
                yielded = step(arg)
            except StopIteration as exc:
                return exc.value
        try:
            step, arg = coro.send, (yield yielded)
        except BaseException as exc:  # pylint: disable=broad-except
            step, arg = coro.throw, exc


def _pyrepl(submodule: str) -> Any:
    """Return a submodule of the stdlib's private (and unstubbed) pyrepl.

    It's what gives the stock Python 3.13+ REPL its line editing,
    colors and completion; we drive it the same way asyncio's REPL does.
    """
    return importlib.import_module(f'_pyrepl.{submodule}')


# Whether pyrepl came up; decided on the main thread (see
# prepare_in_main_thread()).
_g_can_use_pyrepl = False


class _LogicThreadConsoleMixin(code.InteractiveConsole):
    """Interactive-console bits that run code on the logic thread."""

    def __init__(self, locals: dict[str, Any]) -> None:
        super().__init__(locals, filename='<stdin>')
        self.compile.compiler.flags |= ast.PyCF_ALLOW_TOP_LEVEL_AWAIT
        # Keep running tasks alive; the loop only holds weak refs.
        self._tasks: set[asyncio.Task[Any]] = set()

    @override
    def runcode(self, code: types.CodeType) -> Any:
        # pylint: disable=redefined-outer-name
        future: concurrent.futures.Future[Any] = concurrent.futures.Future()

        # A stored exception's traceback holds _run's frame, so _run
        # must not keep the future alive through its closure or the two
        # form a cycle only cyclic gc can break (see
        # babase._general._LogicThreadSubmission). Hand it over in a
        # list that _run empties.
        holder = [future]

        def _run() -> None:
            assert _babase.in_logic_thread()
            fut = holder.pop()
            if not fut.set_running_or_notify_cancel():
                return
            _babase.user_ran_commands()
            try:
                result = types.FunctionType(code, self.locals)()
                if not inspect.iscoroutine(result):
                    fut.set_result(result)
                    return
                task = _babase.app.asyncio_loop.create_task(
                    _run_in_context(result, _babase.ContextRef())
                )
            except BaseException as exc:  # pylint: disable=broad-except
                fut.set_exception(exc)
                del fut
                return
            self._tasks.add(task)

            def _done(tsk: asyncio.Task[Any]) -> None:
                self._tasks.discard(tsk)
                if tsk.cancelled():
                    fut.set_exception(KeyboardInterrupt())
                elif (exc := tsk.exception()) is not None:
                    fut.set_exception(exc)
                else:
                    fut.set_result(tsk.result())

            task.add_done_callback(_done)

        # Like the legacy console, run in whatever context is visible.
        _babase.pushcall(
            _run, from_other_thread=True, other_thread_use_fg_context=True
        )

        try:
            # Poll so we don't hang forever if the app goes down before
            # the logic thread gets to our call.
            while True:
                try:
                    return future.result(timeout=0.25)
                except concurrent.futures.TimeoutError:
                    if _babase.app.shutting_down:
                        future.cancel()
                        return None
        except BaseException as exc:  # pylint: disable=broad-except
            # The exception's traceback holds this frame; don't let it
            # hold the future holding the exception too.
            del future
            if isinstance(exc, SystemExit):
                # exit()/quit(); per InteractiveConsole.runcode()
                # convention this ends the interactive loop (and run()
                # then quits the app).
                raise
            self._show_user_traceback(exc)
            return None

    def _show_user_traceback(self, exc: BaseException) -> None:
        # Drop our own plumbing frames (futures, task wrappers, etc.) so
        # the traceback starts at the user's code like the stock REPL.
        tb = exc.__traceback__
        while tb is not None and not tb.tb_frame.f_code.co_filename.startswith(
            '<'
        ):
            tb = tb.tb_next
        if tb is None:
            tb = exc.__traceback__
        self._showtraceback(type(exc), exc, tb, '')  # type: ignore


def _make_console(locals: dict[str, Any]) -> _LogicThreadConsoleMixin:
    # pylint: disable=redefined-builtin

    # The colored console assumes pyrepl's own multi-line handling, so
    # it only pairs with pyrepl; the basic console pairs with readline.
    base: type[code.InteractiveConsole]
    if _g_can_use_pyrepl:
        base = _pyrepl('console').InteractiveColoredConsole
    else:
        base = code.InteractiveConsole

    cls = type('LogicThreadConsole', (_LogicThreadConsoleMixin, base), {})
    console: _LogicThreadConsoleMixin = cls(locals)
    return console


def prepare_in_main_thread(main_globals: dict[str, Any]) -> None:
    """Do setup that must happen on the main thread.

    pyrepl builds its terminal reader at import time and installs a
    SIGCONT handler while doing so; Python only allows that from the
    main thread, so we import it here and the stdin thread reuses the
    cached reader later. pyrepl is pure Python (no readline/libedit) and
    does its own completion.

    Without pyrepl we set up readline completion for the basic console
    instead. macOS readline is usually libedit, which ignores GNU-style
    bindings.
    """
    # pylint: disable=global-statement
    global _g_can_use_pyrepl
    from babase._logging import balog

    assert threading.current_thread() is threading.main_thread()

    try:
        pyrepl_main = _pyrepl('main')
        _g_can_use_pyrepl = pyrepl_main.CAN_USE_PYREPL
        if not _g_can_use_pyrepl:
            balog.info(
                'Native repl using basic console (%s).',
                pyrepl_main.FAIL_REASON,
            )
    except Exception:
        balog.info('Native repl using basic console.', exc_info=True)

    if _g_can_use_pyrepl:
        _restore_terminal_at_exit()
        return

    try:
        import readline
        import rlcompleter

        readline.set_completer(rlcompleter.Completer(main_globals).complete)
        if 'libedit' in (readline.__doc__ or ''):
            readline.parse_and_bind('bind ^I rl_complete')
        else:
            readline.parse_and_bind('tab: complete')
    except Exception:
        balog.debug('Unable to set up readline.', exc_info=True)


def _restore_terminal_at_exit() -> None:
    """Put the terminal back the way we found it when the app exits.

    pyrepl keeps the terminal in raw mode while waiting for input, and
    unlike a regular Python REPL our app can exit out from under it at
    any point (window closed, SIGTERM, etc.).
    """
    from babase._logging import balog

    try:
        import termios
    except ImportError:
        return  # Not a unix-y platform.

    try:
        fd = sys.stdin.fileno()
        saved = termios.tcgetattr(fd)
    except Exception:
        balog.debug('Unable to save terminal state.', exc_info=True)
        return

    def _restore() -> None:
        try:
            termios.tcsetattr(fd, termios.TCSANOW, saved)
            # Turn off bracketed-paste mode which pyrepl may have left on.
            sys.stdout.write('\x1b[?2004l')
            sys.stdout.flush()
        except Exception:
            pass

    _babase.atexit(_restore)


def run() -> None:
    """Run the interactive loop; call from the stdin thread."""
    assert not _babase.in_logic_thread()

    # Regular Python gets these from site; we don't run that. They go in
    # builtins (not our locals) so pyrepl's bare 'exit' command still
    # works. code's Quitter (unlike site's) doesn't close stdin; it's
    # just missing from typeshed.
    for name in ('exit', 'quit'):
        if not hasattr(builtins, name):
            quitter = code.Quitter(name)  # type: ignore[attr-defined]
            setattr(builtins, name, quitter)

    console = _make_console(sys.modules['__main__'].__dict__)
    try:
        if _g_can_use_pyrepl:
            _pyrepl('simple_interact').run_multiline_interactive_console(
                console
            )
        else:
            console.interact(banner='', exitmsg='')
    except SystemExit:
        pass

    # They typed exit()/quit() or hit Ctrl-D; treat it like the regular
    # Python REPL and take the app down with us.
    _babase.pushcall(_babase.quit, from_other_thread=True)
