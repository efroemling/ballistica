# Released under the MIT License. See LICENSE for details.
#
"""Standard snippets that can be pulled into project pcommand scripts.

A snippet is a mini-program that directly takes input from stdin and does
some focused task. This module is a repository of common snippets that can
be imported into projects' pcommand script for easy reuse.
"""
from __future__ import annotations

# Note: import as little as possible here at the module level to keep
# launch times fast for small snippets.
import sys
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import io
    import threading
    from typing import Any

    from efro.terminal import ClrBase

# Absolute path of the project root.
PROJROOT = Path(__file__).resolve().parents[2]

# Set of arguments for the currently running command.
# Note that, unlike sys.argv, this will not include the script path or
# the name of the pcommand; only the arguments *to* the command.
_g_thread_local_storage: threading.local | None = None

# Discovered functions for the current project.
_g_funcs: dict | None = None

# Are we running as a server?
_g_batch_server_mode: bool = False


def pcommand_main(globs: dict[str, Any]) -> None:
    """Main entry point to pcommand scripts.

    We simply look for all public functions and call
    the one corresponding to the first passed arg.
    """
    import types

    from efro.terminal import Clr
    from efro.error import CleanError

    global _g_funcs  # pylint: disable=global-statement
    assert _g_funcs is None

    # Build our list of available funcs.
    _g_funcs = dict(
        (
            (name, obj)
            for name, obj in globs.items()
            if not name.startswith('_')
            and name != 'pcommand_main'
            and isinstance(obj, types.FunctionType)
        )
    )

    try:
        _run_pcommand(sys.argv)
    except KeyboardInterrupt as exc:
        print(f'{Clr.RED}{exc}{Clr.RST}')
        sys.exit(1)
    except CleanError as exc:
        exc.pretty_print()
        sys.exit(1)


def get_args() -> list[str]:
    """Return the args for the current pcommand."""
    # pylint: disable=unsubscriptable-object, not-an-iterable
    if not _g_batch_server_mode:
        return sys.argv[2:]

    # Ok, we're in batch mode. We should have stuffed some args into
    # thread-local storage.
    assert _g_thread_local_storage is not None
    argv: list[str] | None = getattr(_g_thread_local_storage, 'argv', None)
    if argv is None:
        raise RuntimeError('Thread local args not found where expected.')
    assert isinstance(argv, list)
    assert all(isinstance(i, str) for i in argv)
    return argv[2:]


def clr() -> type[ClrBase]:
    """Like efro.terminal.Clr but for use with pcommand.clientprint().

    This properly colorizes or doesn't colorize based on whether the
    *client* where output will be displayed is running on a terminal.
    Regular print() output should still use efro.terminal.Clr for this
    purpose.
    """
    import efro.terminal

    if _g_batch_server_mode:
        assert _g_thread_local_storage is not None
        clrtp: type[ClrBase] = _g_thread_local_storage.clr
        assert issubclass(clrtp, efro.terminal.ClrBase)
        return clrtp

    return efro.terminal.Clr


def clientprint(
    *args: Any, stderr: bool = False, end: str | None = None
) -> None:
    """Print to client stdout.

    Note that, in batch mode, the results of all clientprints will show
    up only after the command completes. In regular mode, clientprint()
    simply passes through to regular print().
    """
    if _g_batch_server_mode:
        assert _g_thread_local_storage is not None
        print(
            *args,
            file=_g_thread_local_storage.stderr
            if stderr
            else _g_thread_local_storage.stdout,
            end=end,
        )
    else:
        print(*args, end=end)


def _run_pcommand(sysargv: list[str]) -> None:
    """Run a pcommand given raw sys args."""
    from efro.error import CleanError

    assert _g_funcs is not None

    clrtp = clr()
    error = False
    show_help = False
    if len(sysargv) < 2:
        clientprint(f'{clrtp.SRED}Error: Command expected.{clrtp.RST}')
        show_help = True
        error = True
    else:
        if sysargv[1] == 'help':
            if len(sysargv) == 2:
                show_help = True
            elif sysargv[2] not in _g_funcs:
                raise CleanError('Invalid help command.')
            else:
                docs = _trim_docstring(
                    getattr(_g_funcs[sysargv[2]], '__doc__', '<no docs>')
                )
                clientprint(
                    f'\n{clrtp.MAG}{clrtp.BLD}'
                    f'pcommand {sysargv[2]}:{clrtp.RST}\n'
                    f'{clrtp.MAG}{docs}{clrtp.RST}\n'
                )
        elif sysargv[1] in _g_funcs:
            _g_funcs[sysargv[1]]()
        else:
            raise CleanError(f"Unknown pcommand '{sysargv[1]}'.")

    if show_help:
        clientprint(
            f'The {clrtp.MAG}{clrtp.BLD}pcommand{clrtp.RST} script encapsulates'
            f' a collection of project-related commands.'
        )
        clientprint(
            f"Run {clrtp.MAG}{clrtp.BLD}'pcommand [COMMAND] ...'"
            f'{clrtp.RST} to run a command.'
        )
        clientprint(
            f"Run {clrtp.MAG}{clrtp.BLD}'pcommand help [COMMAND]'"
            f'{clrtp.RST} for full documentation for a command.'
        )
        clientprint('Available commands:')
        for func, obj in sorted(_g_funcs.items()):
            doc = getattr(obj, '__doc__', '').splitlines()[0].strip()
            clientprint(f'{clrtp.MAG}{func}{clrtp.BLU} - {doc}{clrtp.RST}')

    if error:
        raise CleanError()


def enter_batch_server_mode() -> None:
    """Called by pcommandserver when we start serving."""
    # (try to avoid importing this in non-batch mode in case it shaves
    # off a bit of time)
    import threading

    # pylint: disable=global-statement
    global _g_batch_server_mode, _g_thread_local_storage
    assert not _g_batch_server_mode
    _g_batch_server_mode = True

    # Spin up our thread-local storage.
    assert _g_thread_local_storage is None
    _g_thread_local_storage = threading.local()


def is_batch() -> bool:
    """Is the current pcommand running under a batch server?

    Commands that do things that are unsafe to do in server mode
    such as chdir should assert that this is not true.
    """
    return _g_batch_server_mode


def run_client_pcommand(
    args: list[str], clrtp: type[ClrBase], logpath: str
) -> tuple[int, str, str]:
    """Call a pcommand function as a server.

    Returns a result code and stdout output.
    """
    import io
    import traceback

    from efro.error import CleanError

    assert _g_batch_server_mode
    assert _g_thread_local_storage is not None

    with io.StringIO() as stdout, io.StringIO() as stderr:
        # Stuff some state into thread-local storage for the handler thread
        # to access.
        _g_thread_local_storage.stdout = stdout
        _g_thread_local_storage.stderr = stderr
        _g_thread_local_storage.argv = args
        _g_thread_local_storage.clr = clrtp

        try:
            _run_pcommand(args)
            resultcode = 0
        except KeyboardInterrupt as exc:
            clientprint(f'{clrtp.RED}{exc}{clrtp.RST}')
            resultcode = 1
        except CleanError as exc:
            exc.pretty_print(file=stderr, clr=clrtp)
            resultcode = 1
        except Exception:
            traceback.print_exc(file=stderr)
            print(
                f'More error output may be available at {logpath}', file=stderr
            )
            resultcode = 1

        stdout_str = stdout.getvalue()
        stderr_str = stderr.getvalue()

    return resultcode, stdout_str, stderr_str


def disallow_in_batch() -> None:
    """Utility call to raise a clean error if running under batch mode."""
    from efro.error import CleanError

    if _g_batch_server_mode:
        raise CleanError(
            'This pcommand does not support batch mode.\n'
            'See docs in efrotools.pcommand if you want to add it.'
        )


def _trim_docstring(docstring: str) -> str:
    """Trim raw doc-strings for pretty printing.

    Taken straight from PEP 257.
    """
    if not docstring:
        return ''

    # Convert tabs to spaces (following the normal Python rules) and
    # split into a list of lines.
    lines = docstring.expandtabs().splitlines()

    # Determine minimum indentation (first line doesn't count).
    indent = sys.maxsize
    for line in lines[1:]:
        stripped = line.lstrip()
        if stripped:
            indent = min(indent, len(line) - len(stripped))

    # Remove indentation (first line is special).
    trimmed = [lines[0].strip()]
    if indent < sys.maxsize:
        for line in lines[1:]:
            trimmed.append(line[indent:].rstrip())

    # Strip off trailing and leading blank lines.
    while trimmed and not trimmed[-1]:
        trimmed.pop()
    while trimmed and not trimmed[0]:
        trimmed.pop(0)

    # Return a single string.
    return '\n'.join(trimmed)
