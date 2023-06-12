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
    pass


@dataclass
class AttributeInfo:
    """Info about an attribute of a class."""

    name: str
    attr_type: str | None = None
    docs: str | None = None


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
        cur_attr: AttributeInfo | None = None
        for i in range(attr_line + 1, len(docs_lines)):
            line = docs_lines[i].strip()

            # A line with a single alphanumeric word preceding a colon
            # is a new attr.
            splits = line.split(' ', maxsplit=1)
            if splits[0].replace('_', '').isalnum() and splits[-1].endswith(
                ':'
            ):
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


def generate_pdoc(projroot: str) -> None:
    """Main entry point."""
    del projroot  # Unused.
    print('WOULD DO DOCS')


def do_generate_pdoc(projroot: str) -> None:
    """Main entry point."""
    from batools.version import get_current_version
    import pdoc

    # Since we're operating on source dirs, suppress .pyc generation.
    # (__pycache__ dirs accumulating in source dirs causes some subtle
    # headaches)
    sys.dont_write_bytecode = True

    # Make sure we're running from the dir above this script.
    os.chdir(projroot)

    templatesdir = (
        Path(projroot) / 'assets' / 'src' / 'pdoc' / 'templates'
    ).absolute()
    pythondir = (
        Path(projroot) / 'assets' / 'src' / 'ba_data' / 'python'
    ).absolute()
    outdirname = (Path(projroot) / 'build' / 'docs_html').absolute()
    sys.path.append(str(pythondir))

    version, build_number = get_current_version()

    try:
        os.environ['BA_DOCS_GENERATION'] = '1'
        pdoc.render.env.globals['ba_version'] = version
        pdoc.render.env.globals['ba_build'] = build_number
        pdoc.render.configure(
            search=True, show_source=True, template_directory=templatesdir
        )
        pdoc.pdoc(
            'babase',
            'bascenev1lib',
            'baclassic',
            'bascenev1',
            'bauiv1',
            output_directory=outdirname,
        )
    except Exception as exc:
        import traceback

        traceback.print_exc()
        raise CleanError('Docs generation failed') from exc

    print(f'{Clr.GRN}Docs generation complete.{Clr.RST}')
