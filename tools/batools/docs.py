# Released under the MIT License. See LICENSE for details.
#
"""Documentation generation functionality."""

from __future__ import annotations

import sys
import os
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from efro.error import CleanError
from efro.terminal import Clr

if TYPE_CHECKING:
    from typing import Optional


@dataclass
class AttributeInfo:
    """Info about an attribute of a class."""
    name: str
    attr_type: Optional[str] = None
    docs: Optional[str] = None


def parse_docs_attrs(attrs: list[AttributeInfo], docs: str) -> str:
    """Given a docs str, parses attribute descriptions contained within."""
    docs_lines = docs.splitlines()
    attr_line = None
    for i, line in enumerate(docs_lines):
        if line.strip() in ['Attributes:', 'Attrs:']:
            attr_line = i
            break

    if attr_line is not None:
        # Docs is now everything *up to* this.
        docs = '\n'.join(docs_lines[:attr_line])

        # Go through remaining lines creating attrs and docs for each.
        cur_attr: Optional[AttributeInfo] = None
        for i in range(attr_line + 1, len(docs_lines)):
            line = docs_lines[i].strip()

            # A line with a single alphanumeric word preceding a colon
            # is a new attr.
            splits = line.split(' ')
            if (len(splits) in (1, 2)
                    and splits[0].replace('_', '').isalnum()):
                if cur_attr is not None:
                    attrs.append(cur_attr)
                cur_attr = AttributeInfo(name=splits[0])
                if len(splits) == 2:
                    # Remove brackets and convert from
                    # (type): to type.
                    cur_attr.attr_type = splits[1][1:-2]

            # Any other line gets tacked onto the current attr.
            else:
                if cur_attr is not None:
                    if cur_attr.docs is None:
                        cur_attr.docs = ''
                    cur_attr.docs += line + '\n'

        # Finish out last.
        if cur_attr is not None:
            attrs.append(cur_attr)

        for attr in attrs:
            if attr.docs is not None:
                attr.docs = attr.docs.strip()
    return docs


def generate(projroot: str) -> None:
    """Main entry point."""
    import pdoc

    # Make sure we're running from the dir above this script.
    os.chdir(projroot)

    pythondir = str(
        Path(projroot, 'assets', 'src', 'ba_data', 'python').absolute())
    sys.path.append(pythondir)
    outdirname = Path('build', 'docs_html').absolute()

    try:
        pdoc.render.configure(docformat='google',
                              search=True,
                              show_source=True)
        pdoc.pdoc('ba', 'bastd', output_directory=outdirname)
    except Exception as exc:
        import traceback
        traceback.print_exc()
        raise CleanError('Docs generation failed') from exc

    print(f'{Clr.GRN}Docs generation complete.{Clr.RST}')
