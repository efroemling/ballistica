# Released under the MIT License. See LICENSE for details.
#
"""Documentation generation functionality."""

from __future__ import annotations

import os
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


def generate_sphinx_docs() -> None:
    """Run docs generation with sphinx."""
    # pylint: disable=too-many-locals
    # pylint: disable=too-many-statements

    import time
    import shutil
    from multiprocessing import cpu_count
    from concurrent.futures import ProcessPoolExecutor

    from jinja2 import Environment, FileSystemLoader

    # Make sure dummy-modules are up to date.
    subprocess.run(['make', 'dummymodules'], check=True)

    settings = get_sphinx_settings('.')

    cache_dir = Path('.cache/sphinx')
    sphinx_src_dir = Path('src/assets/sphinx')
    build_dir = Path('build/docs')
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

    def _printstatus(msg: str) -> None:
        print(f'{Clr.BLU}{Clr.BLD}{msg}{Clr.RST}', flush=True)

    # Create copies of all Python sources we're documenting. This way we
    # can filter them beforehand to make some docs prettier (in
    # particular, the Annotated[] stuff we use a lot makes things very
    # ugly so we strip those out).
    _printstatus('Gathering sources...')
    subprocess.run(['rm', '-rf', filtered_data_dir], check=True)

    dirpairs: list[tuple[str, str]] = [
        ('src/assets/ba_data/python/', f'{ba_data_filtered_dir}/'),
        ('build/dummymodules/', f'{dummy_modules_filtered_dir}/'),
        ('tools/', f'{tools_filtered_dir}/'),
    ]
    for srcdir, dstdir in dirpairs:
        os.makedirs(dstdir, exist_ok=True)
        shutil.copytree(srcdir, dstdir, dirs_exist_ok=True)
        # subprocess.run(['cp', '-rv', srcdir, dstdir], check=True)

    # Filter all files. Doing this with multiprocessing gives us a very
    # nice speedup vs multithreading which seems gil-constrained.
    _printstatus('Filtering sources...')
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

    _printstatus('Updating source modtimes...')
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

    _printstatus('Generating index.rst...')
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

    sphinx_apidoc_cmd = [
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

    _printstatus('Generating runtimemodules...')
    subprocess.run(
        sphinx_apidoc_cmd
        + [
            '--doc-project',
            'Runtime',
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

    _printstatus('Generating toolsmodules...')
    subprocess.run(
        sphinx_apidoc_cmd
        + [
            '--doc-project',
            'Tools',
            '--tocfile',
            'toolsmodules',
            module_first_arg,
            '--maxdepth',
            module_list_max_depth,
            '-f',
            str(tools_filtered_dir),
        ]
        + excludes_tools,
        env=environ,
        check=True,
    )

    _printstatus('Generating commonmodules...')
    subprocess.run(
        sphinx_apidoc_cmd
        + [
            '--doc-project',
            'Common',
            '--tocfile',
            'commonmodules',
            module_first_arg,
            '--maxdepth',
            module_list_max_depth,
            '-f',
            str(tools_filtered_dir),
        ]
        + excludes_common,
        env=environ,
        check=True,
    )

    # raise RuntimeError('SO FAR SO GOOD')

    _printstatus('Running sphinx-build...')
    subprocess.run(
        [
            'sphinx-build',
            '--fail-on-warning',
            '--conf-dir',
            static_dir,
            '--doctree-dir',
            cache_dir,
            cache_dir,  # input dir
            build_dir,  # output dir
        ],
        env=environ,
        check=True,
    )

    duration = time.monotonic() - starttime
    print(f'Generated sphinx documentation in {duration:.1f}s.')


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
            '  Generator, Awaitable, Sequence, Self)\n'
            'import asyncio\n'
            'from concurrent.futures import Future\n'
            'from pathlib import Path\n'
            'from enum import Enum\n'
        )

    with open(filenameout, 'w', encoding='utf-8') as f:
        f.write(final_code)
