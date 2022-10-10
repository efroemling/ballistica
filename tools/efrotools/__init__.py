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
import json
import platform
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Sequence, Any, Literal

# Python major version we're using for all this stuff.
PYVER = '3.10'

# Python binary assumed by these tools.
PYTHON_BIN = f'python{PYVER}' if platform.system() != 'Windows' else 'python'


def explicit_bool(value: bool) -> bool:
    """Simply return input value; can avoid unreachable-code type warnings."""
    return value


def getlocalconfig(projroot: Path) -> dict[str, Any]:
    """Return a project's localconfig contents (or default if missing)."""
    localconfig: dict[str, Any]
    try:
        with open(
            Path(projroot, 'config/localconfig.json'), encoding='utf-8'
        ) as infile:
            localconfig = json.loads(infile.read())
    except FileNotFoundError:
        localconfig = {}
    return localconfig


def getconfig(projroot: Path) -> dict[str, Any]:
    """Return a project's config contents (or default if missing)."""
    config: dict[str, Any]
    try:
        with open(
            Path(projroot, 'config/config.json'), encoding='utf-8'
        ) as infile:
            config = json.loads(infile.read())
    except FileNotFoundError:
        config = {}
    return config


def setconfig(projroot: Path, config: dict[str, Any]) -> None:
    """Set the project config contents."""
    os.makedirs(Path(projroot, 'config'), exist_ok=True)
    with Path(projroot, 'config/config.json').open(
        'w', encoding='utf-8'
    ) as outfile:
        outfile.write(json.dumps(config, indent=2))


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
    """Read a text file and return a str."""
    with open(path, encoding='utf-8') as infile:
        return infile.read()


def writefile(path: str | Path, txt: str) -> None:
    """Write a string to a file."""
    with open(path, 'w', encoding='utf-8') as outfile:
        outfile.write(txt)


def replace_exact(opstr: str, old: str, new: str, count: int = 1) -> str:
    """Replace text ensuring that exactly x occurrences are replaced.

    Useful when filtering data in some predefined way to ensure the original
    has not changed.
    """
    found = opstr.count(old)
    if found != count:
        raise Exception(
            f'expected {count} string occurrence(s);'
            f' found {found}. String = {old}'
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
        raise Exception('expected a list')
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
        raise Exception('#@ marker found in file; this breaks examinations.')
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
            code.runmypy(projroot, [str(tmppath)], check=False)
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
