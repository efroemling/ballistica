"""EfroTools: Various build related functionality for use in my projects."""

from __future__ import annotations

import os
import json
import subprocess
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Dict, Union, Sequence, Optional, Any


def explicit_bool(value: bool) -> bool:
    """Simply return input value; can avoid unreachable-code type warnings."""
    return value


def get_localconfig(projroot: Path) -> Dict[str, Any]:
    """Return a project's localconfig contents (or default if missing)."""
    localconfig: Dict[str, Any]
    try:
        with open(Path(projroot, 'config/localconfig.json')) as infile:
            localconfig = json.loads(infile.read())
    except FileNotFoundError:
        localconfig = {}
    return localconfig


def get_config(projroot: Path) -> Dict[str, Any]:
    """Return a project's config contents (or default if missing)."""
    config: Dict[str, Any]
    try:
        with open(Path(projroot, 'config/config.json')) as infile:
            config = json.loads(infile.read())
    except FileNotFoundError:
        config = {}
    return config


def set_config(projroot: Path, config: Dict[str, Any]) -> None:
    """Set the project config contents."""
    os.makedirs(Path(projroot, 'config'), exist_ok=True)
    with Path(projroot, 'config/config.json').open('w') as outfile:
        outfile.write(json.dumps(config, indent=2))


def readfile(path: Union[str, Path]) -> str:
    """Read a text file and return a str."""
    with open(path) as infile:
        return infile.read()


def writefile(path: Union[str, Path], txt: str) -> None:
    """Write a string to a file."""
    with open(path, 'w') as outfile:
        outfile.write(txt)


def replace_one(opstr: str, old: str, new: str) -> str:
    """Replace text ensuring that exactly one occurrence is replaced."""
    count = opstr.count(old)
    if count != 1:
        raise Exception(
            f'expected 1 string occurrence; found {count}. String = {old}')
    return opstr.replace(old, new)


def run(cmd: str) -> None:
    """Run a shell command, checking errors."""
    subprocess.run(cmd, shell=True, check=True)


def get_files_hash(filenames: Sequence[Union[str, Path]],
                   extrahash: str = '',
                   int_only: bool = False) -> str:
    """Return a md5 hash for the given files."""
    import hashlib
    if not isinstance(filenames, list):
        raise Exception('expected a list')
    md5 = hashlib.md5()
    for fname in filenames:
        with open(fname, 'rb') as infile:
            while True:
                data = infile.read(2**20)
                if not data:
                    break
                md5.update(data)
    md5.update(extrahash.encode())

    if int_only:
        return str(int.from_bytes(md5.digest(), byteorder='big'))

    return md5.hexdigest()


def _py_symbol_at_column(line: str, col: int) -> str:
    start = col
    while start > 0 and line[start - 1] != ' ':
        start -= 1
    end = col
    while end < len(line) and line[end] != ' ':
        end += 1
    return line[start:end]


def py_examine(filename: Path, line: int, column: int,
               selection: Optional[str], operation: str) -> None:
    """Given file position info, performs some code inspection."""
    # pylint: disable=too-many-locals
    # pylint: disable=cyclic-import
    import astroid
    import re
    from efrotools import code

    # Pull in our pylint plugin which really just adds astroid filters.
    # That way our introspection here will see the same thing as pylint's does.
    with open(filename) as infile:
        fcontents = infile.read()
    if '#@' in fcontents:
        raise Exception('#@ marker found in file; this breaks examinations.')
    flines = fcontents.splitlines()

    if operation == 'pylint_infer':

        # See what asteroid can infer about the target symbol.
        symbol = (selection if selection is not None else _py_symbol_at_column(
            flines[line - 1], column))

        # Insert a line after the provided one which is just the symbol so we
        # can ask for its value alone.
        match = re.match(r"\s*", flines[line - 1])
        whitespace = match.group() if match is not None else ''
        sline = whitespace + symbol + ' #@'
        flines = flines[:line] + [sline] + flines[line:]
        node = astroid.extract_node('\n'.join(flines))
        inferred = list(node.infer())
        print(symbol + ':', ', '.join([str(i) for i in inferred]))
    elif operation in ('mypy_infer', 'mypy_locals'):

        # Ask mypy for the type of the target symbol.
        symbol = (selection if selection is not None else _py_symbol_at_column(
            flines[line - 1], column))

        # Insert a line after the provided one which is just the symbol so we
        # can ask for its value alone.
        match = re.match(r"\s*", flines[line - 1])
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
        with tmppath.open('w') as outfile:
            outfile.write('\n'.join(flines))
        try:
            code.runmypy([str(tmppath)], check=False)
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
