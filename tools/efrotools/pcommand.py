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
    import threading
    from typing import Any

    from efro.terminal import ClrBase

# Absolute path of the project root.
PROJROOT = Path(__file__).resolve().parents[2]

# Set of arguments for the currently running command.
# Note that, unlike sys.argv, this will not include the script path or
# the name of the pcommand; only the arguments *to* the command.
_g_thread_local_storage: threading.local | None = None

# Discovered functions for the currently running pcommand instance.
_g_funcs: dict | None = None

# Are we running as a server?
_g_batch_server_mode: bool = False


def pcommand_main(globs: dict[str, Any]) -> None:
    """Main entry point to pcommand scripts.

    We simply look for all public functions and call
    the one corresponding to the first passed arg.
    """
    import types

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

    # Call the one based on sys args.
    sys.exit(_run_pcommand(sys.argv))


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
    """Like efro.terminal.Clr but works correctly under pcommandbatch."""
    import efro.terminal

    # Note: currently just using the 'isatty' value from the client.
    # ideally should expand the client-side logic to exactly match what
    # efro.terminal.Clr does locally.
    if _g_batch_server_mode:
        assert _g_thread_local_storage is not None
        isatty = _g_thread_local_storage.isatty
        assert isinstance(isatty, bool)
        return efro.terminal.ClrAlways if isatty else efro.terminal.ClrNever

    return efro.terminal.Clr


def set_output(output: str, newline: bool = True) -> None:
    """Set an output string for the current pcommand.

    This will be printed to stdout on the client even in batch mode.
    """
    if newline:
        output = f'{output}\n'

    if not _g_batch_server_mode:
        print(output, end='')
        return

    # Ok, we're in batch mode. Stuff this into thread-local storage to
    # be returned once we're done.
    assert _g_thread_local_storage is not None
    if hasattr(_g_thread_local_storage, 'output'):
        raise RuntimeError('Output is already set for this pcommand.')
    _g_thread_local_storage.output = output


def _run_pcommand(sysargv: list[str]) -> int:
    """Do the thing."""
    from efro.error import CleanError
    from efro.terminal import Clr

    assert _g_funcs is not None

    retval = 0
    show_help = False
    if len(sysargv) < 2:
        print(f'{Clr.RED}ERROR: command expected.{Clr.RST}')
        show_help = True
        retval = 1
    else:
        if sysargv[1] == 'help':
            if len(sysargv) == 2:
                show_help = True
            elif sysargv[2] not in _g_funcs:
                print('Invalid help command.')
                retval = 1
            else:
                docs = _trim_docstring(
                    getattr(_g_funcs[sysargv[2]], '__doc__', '<no docs>')
                )
                print(
                    f'\n{Clr.MAG}{Clr.BLD}pcommand {sysargv[2]}:{Clr.RST}\n'
                    f'{Clr.MAG}{docs}{Clr.RST}\n'
                )
        elif sysargv[1] in _g_funcs:
            try:
                _g_funcs[sysargv[1]]()
            except KeyboardInterrupt as exc:
                print(f'{Clr.RED}{exc}{Clr.RST}')
                retval = 1
            except CleanError as exc:
                exc.pretty_print()
                retval = 1
        else:
            print(
                f'{Clr.RED}Unknown pcommand: "{sysargv[1]}"{Clr.RST}',
                file=sys.stderr,
            )
            retval = 1

    if show_help:
        print(
            f'The {Clr.MAG}{Clr.BLD}pcommand{Clr.RST} script encapsulates'
            f' a collection of project-related commands.'
        )
        print(
            f"Run {Clr.MAG}{Clr.BLD}'pcommand [COMMAND] ...'"
            f'{Clr.RST} to run a command.'
        )
        print(
            f"Run {Clr.MAG}{Clr.BLD}'pcommand help [COMMAND]'"
            f'{Clr.RST} for full documentation for a command.'
        )
        print('Available commands:')
        for func, obj in sorted(_g_funcs.items()):
            doc = getattr(obj, '__doc__', '').splitlines()[0].strip()
            print(f'{Clr.MAG}{func}{Clr.BLU} - {doc}{Clr.RST}')

    return retval


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


def run_client_pcommand(args: list[str], isatty: bool) -> tuple[int, str]:
    """Call a pcommand function when running as a batch server."""
    assert _g_batch_server_mode
    assert _g_thread_local_storage is not None

    # Clear any output from previous commands on this thread.
    if hasattr(_g_thread_local_storage, 'output'):
        delattr(_g_thread_local_storage, 'output')

    # Stuff args into our thread-local storage so the user can get at
    # them.
    _g_thread_local_storage.argv = args
    _g_thread_local_storage.isatty = isatty

    # Run the command. This may return an explicit code or may throw an
    # exception.
    resultcode: int = _run_pcommand(args)

    # Handle error result-codes consistently with exceptions.
    if resultcode != 0:
        raise RuntimeError(f'client pcommand returned error code {resultcode}.')

    output = getattr(_g_thread_local_storage, 'output', '')
    assert isinstance(output, str)

    return (resultcode, output)


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
