# Released under the MIT License. See LICENSE for details.
#
"""Generate a Python module containing Enum classes from C++ code.

Note that the general strategy moving forward is the opposite of
this: to generate C++ code as needed from Python sources. That is
generally a better direction to go since introspecting Python objects
or source code ast is more foolproof than the text based parsing we
are doing here.
"""
from __future__ import annotations

import re
import os
from typing import TYPE_CHECKING

from efro.terminal import Clr
from efrotools.project import get_public_legal_notice

if TYPE_CHECKING:
    pass


def camel_case_convert(name: str) -> str:
    """Convert camel-case text to upcase-with-underscores."""
    str1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', str1).upper()


def _gen_enums(infilename: str) -> str:
    out = ''
    enum_lnums: list[int] = []
    with open(infilename, encoding='utf-8') as infile:
        lines = infile.read().splitlines()

    # Tally up all places tagged for exporting python enums.
    for i, line in enumerate(lines):
        if '// BA_EXPORT_PYTHON_ENUM' in line:
            enum_lnums.append(i + 1)

    # Now export each of them.
    for lnum in enum_lnums:
        doclines, lnum = _parse_doc_lines(lines, lnum)
        enum_name = _parse_name(lines, lnum)

        out += f'\n\nclass {enum_name}(Enum):\n    """'
        out += '\n    '.join(doclines)
        if len(doclines) > 1:
            out += '\n    """\n\n'
        else:
            out += '"""\n\n'

        lnumend = _find_enum_end(lines, lnum)
        out = _parse_values(lines, lnum, lnumend, out)

    # Clear lines with only spaces.
    return (
        '\n'.join('' if line == '    ' else line for line in out.splitlines())
        + '\n'
    )


def _parse_name(lines: list[str], lnum: int) -> str:
    bits = lines[lnum].split(' ')

    # Special case: allow for specifying underlying type.
    if len(bits) == 6 and bits[3] == ':' and bits[4] in {'uint8_t', 'uint16_t'}:
        bits = [bits[0], bits[1], bits[2], bits[5]]
    if (
        len(bits) != 4
        or bits[0] != 'enum'
        or bits[1] != 'class'
        or bits[3] != '{'
    ):
        raise RuntimeError(f'Unexpected format for enum on line {lnum + 1}.')
    enum_name = bits[2]
    return enum_name


def _parse_values(lines: list[str], lnum: int, lnumend: int, out: str) -> str:
    val = 0
    for i in range(lnum + 1, lnumend):
        line = lines[i]
        if line.strip().startswith('//'):
            continue

        # Strip off any trailing comment.
        if '//' in line:
            line = line.split('//')[0].strip()

        # Strip off any trailing comma.
        if line.endswith(','):
            line = line[:-1].strip()

        # If they're explicitly assigning a value, parse it.
        if '=' in line:
            splits = line.split()
            if (
                len(splits) != 3
                or splits[1] != '='
                or not splits[2].isnumeric()
            ):
                raise RuntimeError(f'Unable to parse enum value for: {line}')
            name = splits[0]
            val = int(splits[2])
        else:
            name = line

        # name = line.split(',')[0].split('//')[0].strip()
        if not name.startswith('k') or len(name) < 2:
            raise RuntimeError(f"Expected name to start with 'k'; got {name}")

        # We require kLast to be the final value
        # (C++ requires this for bounds checking)
        if i == lnumend - 1:
            if name != 'kLast':
                raise RuntimeError(
                    f'Expected last enum value of kLast; found {name}.'
                )
            continue
        name = camel_case_convert(name[1:])
        out += f'    {name} = {val}\n'
        val += 1
    return out


def _find_enum_end(lines: list[str], lnum: int) -> int:
    lnumend = lnum + 1
    while True:
        if lnumend > len(lines) - 1:
            raise RuntimeError(f'No end found for enum on line {lnum + 1}.')
        if '};' in lines[lnumend]:
            break
        lnumend += 1
    return lnumend


def _parse_doc_lines(lines: list[str], lnum: int) -> tuple[list[str], int]:
    # First parse the doc-string
    doclines: list[str] = []
    lnumorig = lnum
    while True:
        if lnum > len(lines) - 1:
            raise RuntimeError(
                f'No end found for enum docstr line {lnumorig + 1}.'
            )
        if lines[lnum].startswith('enum class '):
            break
        if not lines[lnum].startswith('///'):
            raise RuntimeError(f'Invalid docstr at line {lnum + 1}.')
        doclines.append(lines[lnum][4:])
        lnum += 1
    return doclines, lnum


def generate(projroot: str, infilename: str, outfilename: str) -> None:
    """Main script entry point."""
    from batools.project import project_centric_path

    out = (
        get_public_legal_notice('python')
        + f'\n"""Enum vals generated by {__name__}; do not edit by hand."""'
        f'\n\nfrom enum import Enum\n'
    )

    out += _gen_enums(infilename)

    path = project_centric_path(projroot=projroot, path=outfilename)
    print(f'Meta-building {Clr.BLD}{path}{Clr.RST}')
    os.makedirs(os.path.dirname(outfilename), exist_ok=True)
    with open(outfilename, 'w', encoding='utf-8') as outfile:
        outfile.write(out)
