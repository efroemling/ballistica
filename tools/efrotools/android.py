#!/usr/bin/env python3.7
# Copyright (c) 2011-2020 Eric Froemling
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
# -----------------------------------------------------------------------------
"""Functionality related to android builds."""
from __future__ import annotations

from typing import TYPE_CHECKING
from dataclasses import dataclass

if TYPE_CHECKING:
    from typing import List, Optional, Set


@dataclass
class GradleFilterSection:
    """Filtered section of gradle file."""
    tag: str
    firstline: int
    lastline: int


def filter_gradle_file(buildfilename: str, enabled_tags: Set[str]) -> None:
    """Filter 'EFRO_IF' sections in a gradle file."""

    sections: List[GradleFilterSection] = []

    with open(buildfilename) as infile:
        original = infile.read()
    lines = original.splitlines()

    current_section: Optional[GradleFilterSection] = None
    for i, line in enumerate(lines):
        if line.strip().startswith('// EFRO_IF'):
            if current_section is not None:
                raise RuntimeError('Malformed gradle file')
            current_section = GradleFilterSection(tag=line.split()[2],
                                                  firstline=i,
                                                  lastline=i)
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

    # Only write if its not changed (potentially avoid triggering builds).
    out = '\n'.join(lines) + '\n'
    if out != original:
        with open(buildfilename, 'w') as outfile:
            outfile.write(out)
