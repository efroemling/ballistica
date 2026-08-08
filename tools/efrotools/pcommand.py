# Released under the MIT License. See LICENSE for details.
#
"""Standard snippets that can be pulled into project pcommand scripts.

A snippet is a mini-program that directly takes input from stdin and does
some focused task. This module is a repository of common snippets that can
be imported into projects' pcommand script for easy reuse.
"""

# Note: import as little as possible here at the module level to keep
# launch times fast for small snippets.
import os
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

    We simply look for all public functions in the provided module globals
    and call the one corresponding to the first passed arg.
    """
    import types

    from efro.terminal import Clr
    from efro.error import CleanError

    global _g_funcs  # pylint: disable=global-statement
    assert _g_funcs is None

    # Nowadays generated pcommand scripts run themselves using the
    # project virtual environment's Python interpreter
    # (.venv/bin/pythonX.Y, etc.). This nicely sets up the Python
    # environment but does not touch PATH, meaning the stuff under
    # .venv/bin won't get found if we do subprocess.run()/etc.
    #
    # One way to solve this would be to always do `source
    # .venv/bin/activate` before running tools/pcommand. This sets PATH
    # but also seems unwieldy and easy to forget. It's nice to be able
    # to just run tools/pcommand and assume it'll do the right thing.
    #
    # So let's go ahead and set up PATH here so tools/pcommand by itself
    # *does* do the right thing.

    # Don't do this on Windows; we're not currently using virtual-envs
    # there for the little bit of tools stuff we support.
    if not sys.platform.startswith('win'):
        abs_exe_path = Path(sys.executable).absolute()
        pathparts = abs_exe_path.parts
        if (
            len(pathparts) < 3
            or pathparts[-3] != '.venv'
            or pathparts[-2] != 'bin'
            or not pathparts[-1].startswith('python')
        ):
            raise RuntimeError(
                'Unexpected Python environment;'
                f' we expect to be running under something like'
                f" .venv/bin/pythonX.Y; found '{abs_exe_path}'."
            )

        cur_paths_str = os.environ.get('PATH')
        if cur_paths_str is None:
            raise RuntimeError("'PATH' is not currently set; unexpected.")

        venv_bin_dir = str(abs_exe_path.parent)

        # Only add our entry if it's not already there; don't want PATH to
        # get out of control if we're doing recursive stuff.
        cur_paths = cur_paths_str.split(':')
        if venv_bin_dir not in cur_paths:
            os.environ['PATH'] = ':'.join([venv_bin_dir] + cur_paths)

    # Build our list of available command functions.
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
            file=(
                _g_thread_local_storage.stderr
                if stderr
                else _g_thread_local_storage.stdout
            ),
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
                docs = _format_docstring_for_terminal(
                    _trim_docstring(
                        getattr(_g_funcs[sysargv[2]], '__doc__', '<no docs>')
                    ),
                    clrtp,
                )
                clientprint(
                    f'\n{clrtp.MAG}{clrtp.BLD}'
                    f'pcommand {sysargv[2]}:{clrtp.RST}\n'
                    f'{docs}\n'
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
            docfmt = _format_inline_rst(doc, clrtp, base=clrtp.BLU)
            clientprint(f'{clrtp.MAG}{func}{clrtp.BLU} - {clrtp.RST}{docfmt}')

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


# The narrow slice of inline reST markup our docstrings use. Shared by
# the styling pass (_format_inline_rst) and the re-flow pass (which
# must treat each span as unbreakable when wrapping).
_RST_ROLE_PAT = r':[a-zA-Z][\w:.+-]*:`([^`]+)`'
_RST_LITERAL_PAT = r'``([^`]+?)``'
_RST_STRONG_PAT = r'\*\*(\S(?:[^*]*\S)?)\*\*'

# List-item markers we re-flow with a hanging indent.
_RST_LIST_ITEM_PAT = r'(?:-|\d+[.)])\s+'


def _format_docstring_for_terminal(docs: str, clrtp: type[ClrBase]) -> str:
    """Render our RST-flavored docstring markup as terminal styling.

    Our docstrings are Sphinx reST, so ``pcommand help`` output can use
    that markup instead of showing it raw — the same way HTML
    renditions do. Handles only the narrow slice of reST our docstrings
    actually use: inline literals, Sphinx roles, strong emphasis,
    literal blocks, and paragraph/list re-flowing to the terminal
    width. Anything unrecognized passes through untouched, and any
    error falls back to plain single-color output — help must never
    break over a formatting edge case.
    """
    try:
        return _do_format_docstring_for_terminal(docs, clrtp)
    except Exception:
        return f'{clrtp.MAG}{docs}{clrtp.RST}'


def _help_output_width() -> int:
    """Target wrap width for re-flowed help text."""
    import shutil

    # In batch mode output lands on a *client* terminal whose size we
    # don't know; use the classic default. Cap width for readability on
    # very wide terminals (as HTML renditions do via CSS), and floor it
    # so pathological tiny terminals don't produce degenerate wrapping.
    if _g_batch_server_mode:
        return 80
    return max(40, min(shutil.get_terminal_size((80, 24)).columns, 100))


def _do_format_docstring_for_terminal(docs: str, clrtp: type[ClrBase]) -> str:
    # pylint: disable=too-many-branches
    import re

    width = _help_output_width()
    base = clrtp.MAG
    lines = docs.splitlines()
    out: list[str] = []
    i = 0
    n = len(lines)
    while i < n:
        line = lines[i]
        stripped = line.strip()
        if not stripped:
            out.append('')
            i += 1
            continue
        indent = len(line) - len(line.lstrip())
        pad = ' ' * indent
        if stripped == '::' or stripped.startswith('.. code-block::'):
            # Standalone literal-block intro / code-block directive:
            # the marker line itself vanishes; an indented literal
            # block follows. Dropping the marker doubles up blank
            # lines around it, so collapse those too.
            i += 1
            if out and not out[-1]:
                while i < n and not lines[i].strip():
                    i += 1
            i = _emit_literal_block(lines, i, indent, out, clrtp)
            continue

        # List item: gather its (deeper-indented) continuation lines
        # and re-flow with a hanging indent. A trailing '::' hands off
        # to a literal block like a paragraph does.
        marker_match = re.match(_RST_LIST_ITEM_PAT, stripped)
        if marker_match is not None:
            marker = marker_match.group(0)
            item_lines = [stripped[len(marker) :]]
            ends_in_block = stripped.endswith('::')
            i += 1
            while i < n and not ends_in_block:
                nxt = lines[i]
                nstripped = nxt.strip()
                if not nstripped:
                    break
                if len(nxt) - len(nxt.lstrip()) <= indent:
                    break
                item_lines.append(nstripped)
                ends_in_block = nstripped.endswith('::')
                i += 1
            text = ' '.join(item_lines)
            if ends_in_block:
                text = text[:-1]
            out += _reflow_rst_text(
                text,
                clrtp,
                base,
                width=width,
                initial_indent=pad + marker,
                subsequent_indent=pad + ' ' * len(marker),
            )
            if ends_in_block:
                i = _hand_off_literal_block(lines, i, indent, out, clrtp)
            continue

        # Plain paragraph: gather same-indent lines (stopping at
        # blanks, list items, directives, or indent changes) and
        # re-flow. A trailing '::' ends the paragraph and hands off to
        # a literal block, rendering as a single ':' per reST.
        para_lines = [stripped]
        ends_in_block = stripped.endswith('::')
        i += 1
        while i < n and not ends_in_block:
            nxt = lines[i]
            nstripped = nxt.strip()
            if not nstripped:
                break
            if len(nxt) - len(nxt.lstrip()) != indent:
                break
            if re.match(
                _RST_LIST_ITEM_PAT, nstripped
            ) is not None or nstripped.startswith('.. '):
                break
            para_lines.append(nstripped)
            ends_in_block = nstripped.endswith('::')
            i += 1
        text = ' '.join(para_lines)
        if ends_in_block:
            text = text[:-1]
        out += _reflow_rst_text(
            text,
            clrtp,
            base,
            width=width,
            initial_indent=pad,
            subsequent_indent=pad,
        )
        if ends_in_block:
            i = _hand_off_literal_block(lines, i, indent, out, clrtp)
    return '\n'.join(out)


def _hand_off_literal_block(
    lines: list[str],
    i: int,
    indent: int,
    out: list[str],
    clrtp: type[ClrBase],
) -> int:
    """Emit the separating blank + literal block after a '::' intro."""
    if i < len(lines) and not lines[i].strip():
        out.append('')
        while i < len(lines) and not lines[i].strip():
            i += 1
    return _emit_literal_block(lines, i, indent, out, clrtp)


def _reflow_rst_text(
    text: str,
    clrtp: type[ClrBase],
    base: str,
    *,
    width: int,
    initial_indent: str,
    subsequent_indent: str,
) -> list[str]:
    """Wrap one paragraph/list-item's joined text to ``width``.

    Inline markup spans are protected so wrapping can never split one
    (the styling pass needs each span intact on a single line); their
    markup characters do count toward width, erring toward slightly
    early wraps. Styling is applied per wrapped line.
    """
    import re
    import textwrap

    # Swap spaces inside markup spans for a sentinel so textwrap treats
    # each span as one unbreakable word; restored after wrapping.
    for pat in (_RST_ROLE_PAT, _RST_LITERAL_PAT, _RST_STRONG_PAT):
        text = re.sub(pat, lambda m: m.group(0).replace(' ', '\x01'), text)
    wrapped = textwrap.fill(
        text,
        width=width,
        initial_indent=initial_indent,
        subsequent_indent=subsequent_indent,
        break_long_words=False,
        break_on_hyphens=False,
    ).replace('\x01', ' ')
    return [
        _format_inline_rst(wline, clrtp, base=base)
        for wline in wrapped.splitlines()
    ]


def _emit_literal_block(
    lines: list[str],
    i: int,
    indent: int,
    out: list[str],
    clrtp: type[ClrBase],
) -> int:
    """Emit a literal block (lines indented past ``indent``) verbatim.

    Returns the index of the first line past the block.
    """
    while i < len(lines):
        line = lines[i]
        if line.strip() and (len(line) - len(line.lstrip())) <= indent:
            break
        out.append(f'{clrtp.CYN}{line}{clrtp.RST}' if line.strip() else '')
        i += 1
    return i


def _format_inline_rst(text: str, clrtp: type[ClrBase], base: str) -> str:
    """Apply inline reST styling to one line, on ``base`` color."""
    import re

    if not text:
        return ''

    # Substitutions are tokenized out so later passes can't re-match
    # inside already-rendered text (or inside color escape codes).
    tokens: list[str] = []

    def _tok(rendered: str) -> str:
        tokens.append(rendered)
        return f'\x00{len(tokens) - 1}\x00'

    def _role(m: re.Match[str]) -> str:
        # Sphinx roles (e.g. :class:`~efro.terminal.Clr`): drop the
        # role syntax; the Sphinx '~' convention shows just the tail
        # name.
        target = m.group(1)
        if target.startswith('~'):
            target = target[1:].rsplit('.', 1)[-1]
        return _tok(f'{clrtp.RST}{clrtp.SCYN}{target}{clrtp.RST}{base}')

    text = re.sub(r':[a-zA-Z][\w:.+-]*:`([^`]+)`', _role, text)

    # Inline literals (``foo``).
    text = re.sub(
        r'``([^`]+?)``',
        lambda m: _tok(f'{clrtp.RST}{clrtp.SCYN}{m.group(1)}{clrtp.RST}{base}'),
        text,
    )

    # Strong emphasis (**foo**). (Single-star emphasis is left alone;
    # too collision-prone with shell globs and the payoff is small.)
    text = re.sub(
        r'\*\*(\S(?:[^*]*\S)?)\*\*',
        lambda m: _tok(f'{clrtp.BLD}{m.group(1)}{clrtp.RST}{base}'),
        text,
    )

    text = re.sub(r'\x00(\d+)\x00', lambda m: tokens[int(m.group(1))], text)
    return f'{base}{text}{clrtp.RST}'
