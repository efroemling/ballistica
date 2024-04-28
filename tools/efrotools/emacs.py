# Released under the MIT License. See LICENSE for details.
#
"""Stuff intended to be used from emacs"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    pass


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
