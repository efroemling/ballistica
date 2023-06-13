# Released under the MIT License. See LICENSE for details.
#
"""Documentation generation functionality."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

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
    """Generate a set of pdoc documentation."""
    from batools import apprun

    del projroot  # Unused.

    # Assemble and launch an app and do our docs generation from there.
    # Note: we set EFRO_SUPPRESS_SET_CANONICAL_MODULE_NAMES because pdoc
    # spits out lots of "UserWarning: cannot determine where FOO was
    # taken from" warnings if not. Haven't actually seen what difference
    # it makes in the output though. Basically the canonical names stuff
    # makes things like bascenev1._actor.Actor show up as
    # bascenev1.Actor instead.
    if bool(True):
        # Gen docs from the engine.
        apprun.python_command(
            'import batools.docs; batools.docs._run_pdoc_in_engine()',
            purpose='pdocs generation',
            include_project_tools=True,
            env=dict(os.environ, EFRO_SUPPRESS_SET_CANONICAL_MODULE_NAMES='1'),
        )
    else:
        # Gen docs using dummy modules.
        _run_pdoc_with_dummy_modules()


def _run_pdoc_with_dummy_modules() -> None:
    """Generate docs outside of the engine using our dummy modules.

    Dummy modules stand in for native engine modules, and should be
    just intact enough for us to spit out docs from. The upside is
    that they have full typing information about arguments/etc. so our
    docs will be more complete than if we talk to the live engine.
    """
    raise RuntimeError('UNDER CONSTRUCTION')


def _run_pdoc_in_engine() -> None:
    """Generate docs from within the running engine.

    The upside of this way is we have all built-in native modules
    available. The downside is that we don't have typing information for
    those modules aside from what's embedded in their docstrings (which
    is not parsed by pdoc). So we get lots of 'unknown' arg types in
    docs/etc.

    The ideal solution might be to start writing .pyi files for our
    native modules to provide their type information instead of or in
    addition to our dummy-module approach. Just need to see how that
    works with our pipeline.
    """
    import time

    import pdoc
    from batools.version import get_current_version

    starttime = time.monotonic()

    # Tell pdoc to go through all the modules in ba_data/python.
    modulenames = sorted(
        n.removesuffix('.py')
        for n in os.listdir('src/assets/ba_data/python')
        if not n.startswith('.')
    )
    assert modulenames

    templatesdir = Path('src/assets/pdoc/templates')
    assert templatesdir.is_dir()

    version, buildnum = get_current_version()

    pdoc.render.env.globals['ba_version'] = version
    pdoc.render.env.globals['ba_build'] = buildnum
    pdoc.render.configure(
        search=True,
        show_source=True,
        template_directory=Path('src/assets/pdoc/templates'),
    )
    pdoc.pdoc(*modulenames, output_directory=Path('build/docs_pdoc_html'))

    duration = time.monotonic() - starttime
    print(f'{Clr.GRN}Generated pdoc documentation in {duration:.1f}s.{Clr.RST}')
