# Released under the MIT License. See LICENSE for details.
#
"""Documentation generation functionality."""

# pyright: reportPrivateImportUsage=false

from __future__ import annotations

import os
import sys
import subprocess
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


_g_genned_pdoc_with_dummy_modules = False  # pylint: disable=invalid-name


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
    del projroot  # Unused.

    if bool(False):
        _run_pdoc_in_engine()
    else:
        _run_pdoc_with_dummy_modules()


def _run_pdoc_in_engine() -> None:
    """Generate docs from within the running engine.

    The upside of this way is we have all built-in native modules
    available. The downside is that we don't have typing information
    for those modules aside from what's embedded in their docstrings
    (which is not parsed by pdoc). So we get lots of ugly 'unknown'
    arg types in docs/etc.

    The ideal solution might be to start writing .pyi files for
    our native modules to provide their type information instead
    of or in addition to our dummy-module approach. Just need to
    see how that works with our pipeline.
    """
    from batools import apprun

    # Assemble and launch an app and do our docs generation from there.
    # Note: we set EFRO_SUPPRESS_SET_CANONICAL_MODULE_NAMES because pdoc
    # spits out lots of "UserWarning: cannot determine where FOO was
    # taken from" warnings if not. Haven't actually seen what difference
    # it makes in the output though. Basically the canonical names stuff
    # makes things like bascenev1._actor.Actor show up as
    # bascenev1.Actor instead.

    # Grab names from live objects so things don't break if names
    # change.
    pycmd = f'import {__name__}; {__name__}.{_run_pdoc.__name__}()'
    apprun.python_command(
        pycmd,
        purpose='pdocs generation',
        include_project_tools=True,
        env=dict(os.environ, EFRO_SUPPRESS_SET_CANONICAL_MODULE_NAMES='1'),
    )


def _run_pdoc_with_dummy_modules() -> None:
    """Generate docs outside of the engine using our dummy modules.

    Dummy modules stand in for native engine modules, and should be just
    intact enough for us to spit out docs from.

    The upside is that dummy modules have full typing information about
    arguments/etc. so some docs will be more complete than if we talk to
    the live engine.

    The downside is that we have to hack the engine a bit to be able to
    spin itself up this way and there may be bits missing that would
    otherwise not be when running in a live engine.
    """

    # Not that this is likely to happen, but we muck with sys paths and
    # whatnot here so let's make sure we only do this once.
    global _g_genned_pdoc_with_dummy_modules  # pylint: disable=global-statement
    if _g_genned_pdoc_with_dummy_modules:
        raise RuntimeError(
            'Can only run this once; it mucks with the environment.'
        )
    _g_genned_pdoc_with_dummy_modules = True

    # Make sure dummy-modules are up to date and make them discoverable
    # to Python.
    subprocess.run(['make', 'dummymodules'], check=True)
    sys.path.append('build/dummymodules')

    # Turn off canonical module name muckery (see longer note above).
    os.environ['EFRO_SUPPRESS_SET_CANONICAL_MODULE_NAMES'] = '1'

    # Short circuits a few things in our Python code allowing this to
    # work.
    os.environ['BA_RUNNING_WITH_DUMMY_MODULES'] = '1'

    # Use raw sources for our other stuff.
    sys.path.append('src/assets/ba_data/python')

    # We're using raw source dirs in this case, and we don't want Python
    # dumping .pyc files there as it causes various small headaches with
    # build pipeline stuff.
    sys.dont_write_bytecode = True

    _run_pdoc()


def _run_pdoc() -> None:
    """Do the actual docs generation with pdoc."""
    import time

    import pdoc
    from batools.version import get_current_version

    starttime = time.monotonic()

    # Tell pdoc to go through all the modules in ba_data/python.
    modulenames = [
        n.removesuffix('.py')
        for n in os.listdir('src/assets/ba_data/python')
        if not n.startswith('.')
    ]
    assert modulenames

    # Also add in a few common ones from tools.
    for mname in ['efro', 'bacommon']:
        assert mname not in modulenames
        modulenames.append(mname)

    modulenames.sort()  # Just in case it matters.

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
