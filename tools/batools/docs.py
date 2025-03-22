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

from efro.util import utc_now, strict_partial
from efro.terminal import Clr

if TYPE_CHECKING:
    from concurrent.futures import Future

    from libcst import BaseExpression
    from libcst.metadata import CodeRange


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


def generate_sphinxdoc() -> None:
    """Generate a set of pdoc documentation."""
    _run_sphinx()


@dataclass
class SphinxSettings:
    """Our settings for sphinx stuff."""

    project_name: str
    project_author: str
    copyright: str
    version: str
    buildnum: int
    logo_small: str
    logo_large: str


def get_sphinx_settings(projroot: str) -> SphinxSettings:
    """Settings for our Sphinx runs."""
    from batools.version import get_current_version

    version, buildnum = get_current_version(projroot=projroot)
    return SphinxSettings(
        project_name='Ballistica',
        project_author='Eric Froemling',
        copyright=f'{utc_now().year} Eric Froemling',
        version=version,
        buildnum=buildnum,
        logo_small=(
            'https://files.ballistica.net/'
            'ballistica_media/ballistica_logo_half.png'
        ),
        logo_large=(
            'https://files.ballistica.net/'
            'ballistica_media/ballistica_logo.png'
        ),
    )


def _sphinx_pre_filter_file(path: str) -> None:
    from typing import override

    import libcst as cst
    from libcst import CSTTransformer, Name, Index, Subscript

    filename = path
    filenameout = path

    class RemoveAnnotatedTransformer(CSTTransformer):
        """Replaces `Annotated[FOO, ...]` with just `FOO`"""

        @override
        def leave_Subscript(
            self, original_node: BaseExpression, updated_node: BaseExpression
        ) -> BaseExpression:
            if (
                isinstance(updated_node, Subscript)
                and isinstance(updated_node.value, Name)
                and updated_node.value.value == 'Annotated'
                and isinstance(updated_node.slice[0].slice, Index)
            ):
                return updated_node.slice[0].slice.value
            return updated_node

    with open(filename, 'r', encoding='utf-8') as f:
        source_code: str = f.read()

    tree: cst.Module = cst.parse_module(source_code)
    modified_tree: cst.Module = tree.visit(RemoveAnnotatedTransformer())

    final_code = modified_tree.code

    # It seems there's a good amount of stuff that sphinx can't create
    # links for because we don't actually import it at runtime; it is
    # just forward-declared under a 'if TYPE_CHECKING' block. We want to
    # actually import that stuff so that sphinx can find it. However we
    # can't simply run the code in the 'if TYPE_CHECKING' block because
    # we get cyclical reference errors (modules importing other ones
    # before they are finished being built). For now let's just
    # hard-code some common harmless imports at the end of filtered
    # files. Perhaps the ideal solution would be to run 'if
    # TYPE_CHECKING' blocks in the context of each module but only after
    # everything had been initially imported. Sounds tricky but could
    # work I think.
    if bool(False):
        final_code = final_code.replace(
            '\nif TYPE_CHECKING:\n',
            (
                '\nTYPE_CHECKING = True  # Docs-generation hack\n'
                'if TYPE_CHECKING:\n'
            ),
        )
    if bool(True):
        final_code = final_code + (
            '\n\n# Docs-generation hack; import some stuff that we'
            ' likely only forward-declared\n'
            '# in our actual source code so that docs tools can find it.\n'
            'from typing import (Coroutine, Any, Literal, Callable,\n'
            '  Generator, Awaitable, Sequence)\n'
            'import asyncio\n'
            'from concurrent.futures import Future'
        )

    with open(filenameout, 'w', encoding='utf-8') as f:
        f.write(final_code)


def _run_sphinx() -> None:
    """Do the actual docs generation with sphinx."""
    # pylint: disable=too-many-locals
    # pylint: disable=too-many-statements

    import time
    from multiprocessing import cpu_count
    from concurrent.futures import ProcessPoolExecutor

    from jinja2 import Environment, FileSystemLoader

    settings = get_sphinx_settings('.')

    cache_dir = Path('.cache/sphinx')
    sphinx_src_dir = Path('src/assets/sphinx')
    build_dir = Path('build/sphinx')
    template_dir = Path(sphinx_src_dir, 'template')
    static_dir = Path(sphinx_src_dir, 'static')

    filtered_data_dir = Path('.cache/sphinxfiltered')
    ba_data_filtered_dir = Path(filtered_data_dir, 'ba_data')
    dummy_modules_filtered_dir = Path(filtered_data_dir, 'dummymodules')
    tools_filtered_dir = Path(filtered_data_dir, 'tools')

    assert template_dir.is_dir()
    assert static_dir.is_dir()

    build_dir.mkdir(parents=True, exist_ok=True)
    cache_dir.mkdir(parents=True, exist_ok=True)

    os.environ['BALLISTICA_ROOT'] = os.getcwd()  # used in sphinx conf.py

    # Create copies of all Python sources we're documenting. This way we
    # can filter them beforehand to make some docs prettier (in
    # particular, the Annotated[] stuff we use a lot makes things very
    # ugly so we strip those out).
    print('Copying sources...', flush=True)
    subprocess.run(['rm', '-rf', filtered_data_dir], check=True)
    dirpairs: list[tuple[str, str]] = [
        ('src/assets/ba_data/python/', str(ba_data_filtered_dir)),
        ('build/dummymodules/', str(dummy_modules_filtered_dir)),
        ('tools/', str(tools_filtered_dir)),
    ]
    for srcdir, dstdir in dirpairs:
        os.makedirs(dstdir, exist_ok=True)
        subprocess.run(['cp', '-r', srcdir, dstdir], check=True)

    # Filter all files. Doing this with multiprocessing gives us a very
    # nice speedup vs multithreading which seems gil-constrained.
    print('Filtering sources...', flush=True)
    futures: list[Future] = []
    with ProcessPoolExecutor(max_workers=cpu_count()) as executor:
        for root, _dirs, files in os.walk(filtered_data_dir):
            for fname in files:
                if not fname.endswith('.py'):
                    continue
                fpath = os.path.join(root, fname)
                futures.append(
                    executor.submit(
                        strict_partial(_sphinx_pre_filter_file, fpath)
                    )
                )
    # Surface any exceptions.
    for future in futures:
        _ = future.result()

    # Lastly, copy mod-times from original files onto our filtered ones.
    # Otherwise the 'highlighting module code' step has to run on
    # everything each time which is crazy slow.
    def _copy_modtime(src_file: str, dest_file: str) -> None:
        if not os.path.isfile(dest_file):
            raise RuntimeError(f'Expected file not found: "{dest_file}".')

        # Get the modification time of the source file
        mod_time = os.path.getmtime(src_file)

        # Set the modification time of the destination file to match the
        # source
        os.utime(dest_file, (mod_time, mod_time))

    print('Updating source modtimes...', flush=True)
    futures = []
    for srcdir, dstdir in dirpairs:
        for root, _dirs, files in os.walk(srcdir):
            for fname in files:
                if not fname.endswith('.py'):
                    continue
                fpath = os.path.join(root, fname)
                assert fpath.startswith(srcdir)
                dstpath = os.path.join(dstdir, fpath.removeprefix(srcdir))
                _copy_modtime(fpath, dstpath)

    print('Running sphinx stuff...', flush=True)
    env = Environment(loader=FileSystemLoader(template_dir))
    index_template = env.get_template('index.rst_t')
    # maybe make it automatically render all files in templates dir in future
    with open(Path(cache_dir, 'index.rst'), 'w', encoding='utf-8') as index_rst:
        data = {
            # 'ballistica_image_url': 'https://camo.githubusercontent.com/25021344ceaa7def6fa6523f79115f7ffada8d26b4768bb9a0cf65fc33304f45/68747470733a2f2f66696c65732e62616c6c6973746963612e6e65742f62616c6c6973746963615f6d656469612f62616c6c6973746963615f6c6f676f5f68616c662e706e67',  # pylint: disable=line-too-long
            'version_no': settings.version,
            'build_no': str(settings.buildnum),
        }
        index_rst.write(index_template.render(data=data))

    starttime = time.monotonic()

    apidoc_cmd = [
        'sphinx-apidoc',
        '--doc-author',
        settings.project_author,
        '--doc-version',
        str(settings.version),
        '--doc-release',
        str(settings.buildnum),
        '--output-dir',
        str(cache_dir),
    ]

    # Make sure we won't break some existing use of PYTHONPATH.
    assert 'PYTHONPATH' not in os.environ

    environ = dict(
        os.environ,
        # Prevent Python from writing __pycache__ dirs in our source tree
        # which leads to slight annoyances.
        PYTHONDONTWRITEBYTECODE='1',
        # Allow Ballistica stuff to partially bootstrap itself using
        # dummy modules.
        BA_RUNNING_WITH_DUMMY_MODULES='1',
        # Also prevent our set_canonical_module_names() stuff from running
        # which seems to prevent sphinx from parsing docs from comments. It
        # seems that sphinx spits out pretty class names based on where we
        # expose the classes anyway so its all good.
        EFRO_SUPPRESS_SET_CANONICAL_MODULE_NAMES='1',
        # Also set PYTHONPATH so sphinx can find all our stuff.
        PYTHONPATH=(
            f'{ba_data_filtered_dir}:'
            f'{tools_filtered_dir}:'
            f'{dummy_modules_filtered_dir}'
        ),
    )

    # To me, the default max-depth of 4 seems weird for these categories
    # we create. We start on our top level page with a high level view
    # of our categories and the modules & packages directly under them,
    # but then if we click a category we suddenly see an extremely long
    # exhaustive list of children of children of children. Going with
    # maxdepth 1 so we instead just see the top level stuff for that
    # category. Clicking anything there then takes us to the
    # ultra-detailed page, which feels more natural.
    module_list_max_depth = '1'

    # This makes package module docs the first thing you see when you
    # click a package which feels clean to me.
    module_first_arg = '--module-first'

    # Generate modules.rst containing everything in ba_data.
    subprocess.run(
        apidoc_cmd
        + [
            '--doc-project',
            'runtime',
            '--tocfile',
            'runtimemodules',
            module_first_arg,
            '--maxdepth',
            module_list_max_depth,
            '-f',
            ba_data_filtered_dir,
        ],
        check=True,
        env=environ,
    )

    # Both our common and our tools packages live in 'tools' dir. So we
    # need to build a list of things to ignore in that dir when creating
    # those two listings.
    excludes_tools: list[str] = []
    excludes_common: list[str] = []
    for name in os.listdir(tools_filtered_dir):

        # Skip anything not looking like a Python package.
        if (
            not Path(tools_filtered_dir, name).is_dir()
            or not Path(tools_filtered_dir, name, '__init__.py').exists()
        ):
            continue

        # Assume anything with 'tools' in the name goes with tools.
        exclude_list = excludes_common if 'tools' in name else excludes_tools
        exclude_list.append(str(Path(tools_filtered_dir, name)))

    subprocess.run(
        apidoc_cmd
        + [
            '--doc-project',
            'tools',
            '--tocfile',
            'toolsmodules',
            module_first_arg,
            '--maxdepth',
            module_list_max_depth,
            '-f',
            str(tools_filtered_dir),
        ]
        + excludes_tools,
        check=True,
        env=environ,
    )

    subprocess.run(
        apidoc_cmd
        + [
            '--doc-project',
            'common',
            '--tocfile',
            'commonmodules',
            module_first_arg,
            '--maxdepth',
            module_list_max_depth,
            '-f',
            str(tools_filtered_dir),
        ]
        + excludes_common,
        check=True,
        env=environ,
    )

    subprocess.run(
        [
            'sphinx-build',
            '--conf-dir',
            static_dir,
            '--doctree-dir',
            cache_dir,
            cache_dir,  # input dir
            build_dir,  # output dir
        ],
        check=True,
        env=environ,
    )

    duration = time.monotonic() - starttime
    print(f'Generated sphinx documentation in {duration:.1f}s.')
