# Released under the MIT License. See LICENSE for details.
#
"""Functionality related to android builds."""
from __future__ import annotations

from typing import TYPE_CHECKING
from dataclasses import dataclass

if TYPE_CHECKING:
    pass


@dataclass
class GradleFilterSection:
    """Filtered section of gradle file."""

    tag: str
    firstline: int
    lastline: int


def filter_gradle_file(buildfilename: str, enabled_tags: set[str]) -> None:
    """Filter ``EFRO_IF`` sections in a gradle file."""

    sections: list[GradleFilterSection] = []

    with open(buildfilename, encoding='utf-8') as infile:
        original = infile.read()
    lines = original.splitlines()

    current_section: GradleFilterSection | None = None
    for i, line in enumerate(lines):
        if line.strip().startswith('// EFRO_IF'):
            if current_section is not None:
                raise RuntimeError('Malformed gradle file')
            current_section = GradleFilterSection(
                tag=line.split()[2], firstline=i, lastline=i
            )
        elif line.strip().startswith('// EFRO_ENDIF'):
            if current_section is None:
                raise RuntimeError('Malformed gradle file')
            current_section.lastline = i
            sections.append(current_section)
            current_section = None
    if current_section is not None:
        raise RuntimeError('Malformed gradle file')

    for section in sections:
        for lineno in range(section.firstline + 1, section.lastline):
            enable = section.tag in enabled_tags
            line = lines[lineno]
            leading = ''
            while line.startswith(' '):
                leading += ' '
                line = line[1:]
            if not enable and not line.startswith('// '):
                line = '// ' + line
            if enable and line.startswith('// '):
                line = line[3:]
            lines[lineno] = leading + line

    # Only write if its changed (potentially avoid triggering builds).
    out = '\n'.join(lines) + '\n'
    if out != original:
        with open(buildfilename, 'w', encoding='utf-8') as outfile:
            outfile.write(out)
