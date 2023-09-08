# Released under the MIT License. See LICENSE for details.
#
"""Build/tool functionality shared between all efro projects.

This stuff can be a bit more sloppy/loosey-goosey since it is not used in
live client or server code.
"""

# FIXME: should migrate everything here into submodules since this adds
# overhead to anything importing from any efrotools submodule.

from __future__ import annotations

import os
import sys
import json
from pathlib import Path
from typing import TYPE_CHECKING, overload

if TYPE_CHECKING:
    from typing import Sequence, Any, Literal

# Python major version we're using for all this stuff.
PYVER = '3.11'

# Python binary assumed by these tools.
# PYTHON_BIN = f 'python{PYVER}' if platform.system() != 'Windows' else 'python'
# Update; just using the same executable used to launch us.
PYTHON_BIN = sys.executable

# Cache these since we may repeatedly fetch these in batch mode.
_g_project_configs: dict[str, dict[str, Any]] = {}
_g_local_configs: dict[str, dict[str, Any]] = {}


def explicit_bool(value: bool) -> bool:
    """Simply return input value; can avoid unreachable-code type warnings."""
    return value


def getlocalconfig(projroot: Path | str) -> dict[str, Any]:
    """Return a project's localconfig contents (or default if missing)."""
    projrootstr = str(projroot)
    if projrootstr not in _g_local_configs:
        localconfig: dict[str, Any]

        # Allow overriding path via env var.
        path = os.environ.get('EFRO_LOCALCONFIG_PATH')
        if path is None:
            path = 'config/localconfig.json'

        try:
            with open(Path(projroot, path), encoding='utf-8') as infile:
                localconfig = json.loads(infile.read())
        except FileNotFoundError:
            localconfig = {}
        _g_local_configs[projrootstr] = localconfig

    return _g_local_configs[projrootstr]


def getprojectconfig(projroot: Path | str) -> dict[str, Any]:
    """Return a project's projectconfig contents (or default if missing)."""
    projrootstr = str(projroot)
    if projrootstr not in _g_project_configs:
        config: dict[str, Any]
        try:
            with open(
                Path(projroot, 'config/projectconfig.json'), encoding='utf-8'
            ) as infile:
                config = json.loads(infile.read())
        except FileNotFoundError:
            config = {}
        _g_project_configs[projrootstr] = config
    return _g_project_configs[projrootstr]


def setprojectconfig(projroot: Path | str, config: dict[str, Any]) -> None:
    """Set the project config contents."""
    projrootstr = str(projroot)
    _g_project_configs[projrootstr] = config
    os.makedirs(Path(projroot, 'config'), exist_ok=True)
    with Path(projroot, 'config/projectconfig.json').open(
        'w', encoding='utf-8'
    ) as outfile:
        outfile.write(json.dumps(config, indent=2))


def extract_flag(args: list[str], name: str) -> bool:
    """Given a list of args and a flag name, returns whether it is present.

    The arg flag, if present, is removed from the arg list.
    """
    from efro.error import CleanError

    count = args.count(name)
    if count > 1:
        raise CleanError(f'Flag {name} passed multiple times.')
    if not count:
        return False
    args.remove(name)
    return True


@overload
def extract_arg(
    args: list[str], name: str, required: Literal[False] = False
) -> str | None:
    ...


@overload
def extract_arg(args: list[str], name: str, required: Literal[True]) -> str:
    ...


def extract_arg(
    args: list[str], name: str, required: bool = False
) -> str | None:
    """Given a list of args and an arg name, returns a value.

    The arg flag and value are removed from the arg list.
    raises CleanErrors on any problems.
    """
    from efro.error import CleanError

    count = args.count(name)
    if not count:
        if required:
            raise CleanError(f'Required argument {name} not passed.')
        return None

    if count > 1:
        raise CleanError(f'Arg {name} passed multiple times.')

    argindex = args.index(name)
    if argindex + 1 >= len(args):
        raise CleanError(f'No value passed after {name} arg.')

    val = args[argindex + 1]
    del args[argindex : argindex + 2]

    return val


def replace_section(
    text: str,
    begin_marker: str,
    end_marker: str,
    replace_text: str = '',
    keep_markers: bool = False,
    error_if_missing: bool = True,
) -> str:
    """Replace all text between two marker strings (including the markers)."""
    if begin_marker not in text:
        if error_if_missing:
            raise RuntimeError(f"Marker not found in text: '{begin_marker}'.")
        return text
    splits = text.split(begin_marker)
    if len(splits) != 2:
        raise RuntimeError(
            f"Expected one marker '{begin_marker}'"
            f'; found {text.count(begin_marker)}.'
        )
    before_begin, after_begin = splits
    splits = after_begin.split(end_marker)
    if len(splits) != 2:
        raise RuntimeError(
            f"Expected one marker '{end_marker}'"
            f'; found {text.count(end_marker)}.'
        )
    _before_end, after_end = splits
    if keep_markers:
        replace_text = f'{begin_marker}{replace_text}{end_marker}'
    return f'{before_begin}{replace_text}{after_end}'


def get_public_license(style: str) -> str:
    """Return the license notice as used for our public facing stuff.

    'style' arg can be 'python', 'c++', or 'makefile, or 'raw'.
    """
    if style == 'raw':
        return 'Released under the MIT License. See LICENSE for details.'
    if style == 'python':
        # Add a line at the bottom since our python-formatters tend to smush
        # our code up against the license; this keeps things a bit more
        # visually separated.
        return '# Released under the MIT License. See LICENSE for details.'
    if style == 'makefile':
        # Basically same as python except without the last line.
        return '# Released under the MIT License. See LICENSE for details.'
    if style == 'c++':
        return '// Released under the MIT License. See LICENSE for details.'
    raise RuntimeError(f'Invalid style: {style}')


def readfile(path: str | Path) -> str:
    """Read a utf-8 text file into a string."""
    with open(path, encoding='utf-8') as infile:
        return infile.read()


def writefile(path: str | Path, txt: str) -> None:
    """Write a string to a utf-8 text file."""
    with open(path, 'w', encoding='utf-8') as outfile:
        outfile.write(txt)


def replace_exact(
    opstr: str, old: str, new: str, count: int = 1, label: str | None = None
) -> str:
    """Replace text ensuring that exactly x occurrences are replaced.

    Useful when filtering data in some predefined way to ensure the original
    has not changed.
    """
    found = opstr.count(old)
    label_str = f' in {label}' if label is not None else ''
    if found != count:
        raise RuntimeError(
            f'Expected {count} string occurrence(s){label_str};'
            f' found {found}. String: {repr(old)}'
        )
    return opstr.replace(old, new)


def get_files_hash(
    filenames: Sequence[str | Path],
    extrahash: str = '',
    int_only: bool = False,
    hashtype: Literal['md5', 'sha256'] = 'md5',
) -> str:
    """Return a hash for the given files."""
    import hashlib

    if not isinstance(filenames, list):
        raise RuntimeError(f'Expected a list; got a {type(filenames)}.')
    if TYPE_CHECKING:
        # Help Mypy infer the right type for this.
        hashobj = hashlib.md5()
    else:
        hashobj = getattr(hashlib, hashtype)()
    for fname in filenames:
        with open(fname, 'rb') as infile:
            while True:
                data = infile.read(2**20)
                if not data:
                    break
                hashobj.update(data)
    hashobj.update(extrahash.encode())

    if int_only:
        return str(int.from_bytes(hashobj.digest(), byteorder='big'))

    return hashobj.hexdigest()


def get_string_hash(
    value: str,
    int_only: bool = False,
    hashtype: Literal['md5', 'sha256'] = 'md5',
) -> str:
    """Return a hash for the given files."""
    import hashlib

    if not isinstance(value, str):
        raise TypeError('Expected a str.')
    if TYPE_CHECKING:
        # Help Mypy infer the right type for this.
        hashobj = hashlib.md5()
    else:
        hashobj = getattr(hashlib, hashtype)()
    hashobj.update(value.encode())

    if int_only:
        return str(int.from_bytes(hashobj.digest(), byteorder='big'))

    return hashobj.hexdigest()


def _py_symbol_at_column(line: str, col: int) -> str:
    start = col
    while start > 0 and line[start - 1] != ' ':
        start -= 1
    end = col
    while end < len(line) and line[end] != ' ':
        end += 1
    return line[start:end]


def py_examine(
    projroot: Path,
    filename: Path,
    line: int,
    column: int,
    selection: str | None,
    operation: str,
) -> None:
    """Given file position info, performs some code inspection."""
    # pylint: disable=too-many-locals
    # pylint: disable=cyclic-import
    import astroid
    import re
    from efrotools import code

    # Pull in our pylint plugin which really just adds astroid filters.
    # That way our introspection here will see the same thing as pylint's does.
    with open(filename, encoding='utf-8') as infile:
        fcontents = infile.read()
    if '#@' in fcontents:
        raise RuntimeError('#@ marker found in file; this breaks examinations.')
    flines = fcontents.splitlines()

    if operation == 'pylint_infer':
        # See what asteroid can infer about the target symbol.
        symbol = (
            selection
            if selection is not None
            else _py_symbol_at_column(flines[line - 1], column)
        )

        # Insert a line after the provided one which is just the symbol so
        # that we can ask for its value alone.
        match = re.match(r'\s*', flines[line - 1])
        whitespace = match.group() if match is not None else ''
        sline = whitespace + symbol + ' #@'
        flines = flines[:line] + [sline] + flines[line:]
        node = astroid.extract_node('\n'.join(flines))
        inferred = list(node.infer())
        print(symbol + ':', ', '.join([str(i) for i in inferred]))
    elif operation in ('mypy_infer', 'mypy_locals'):
        # Ask mypy for the type of the target symbol.
        symbol = (
            selection
            if selection is not None
            else _py_symbol_at_column(flines[line - 1], column)
        )

        # Insert a line after the provided one which is just the symbol so
        # that we can ask for its value alone.
        match = re.match(r'\s*', flines[line - 1])
        whitespace = match.group() if match is not None else ''
        if operation == 'mypy_infer':
            sline = whitespace + 'reveal_type(' + symbol + ')'
        else:
            sline = whitespace + 'reveal_locals()'
        flines = flines[:line] + [sline] + flines[line:]

        # Write a temp file and run the check on it.
        # Let's use ' flycheck_*' for the name since pipeline scripts
        # are already set to ignore those files.
        tmppath = Path(filename.parent, 'flycheck_mp_' + filename.name)
        with tmppath.open('w', encoding='utf-8') as outfile:
            outfile.write('\n'.join(flines))
        try:
            code.mypy_files(projroot, [str(tmppath)], check=False)
        except Exception as exc:
            print('error running mypy:', exc)
        tmppath.unlink()
    elif operation == 'pylint_node':
        flines[line - 1] += ' #@'
        node = astroid.extract_node('\n'.join(flines))
        print(node)
    elif operation == 'pylint_tree':
        flines[line - 1] += ' #@'
        node = astroid.extract_node('\n'.join(flines))
        print(node.repr_tree())
    else:
        print('unknown operation: ' + operation)
