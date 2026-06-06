# Released under the MIT License. See LICENSE for details.
#
"""Documentation generation functionality."""

from __future__ import annotations

import os
import re
import json
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


_g_genned_pdoc_with_dummy_modules = False


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
    # pylint: disable=too-many-statements
    """Run docs generation with sphinx."""
    # pylint: disable=too-many-locals

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

    # sphinx-apidoc (-f) overwrites the rst for modules that still exist but
    # never deletes the rst for modules that have since been removed or
    # renamed. Our cache_dir persists across builds on CI workspaces, so a
    # leftover rst would keep trying to autodoc-import a now-gone module and
    # trip sphinx's --fail-on-warning (and orphan itself from every toctree).
    # Clear the generated rst up front; everything here is regenerated below
    # (index.rst + the apidoc tocfiles + per-module rst). Doctree/pickle
    # caches are left in place so incremental builds stay fast.
    for stale_rst in cache_dir.glob('*.rst'):
        stale_rst.unlink()

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
        # Exclude tools/spinoff; it's a symlink into a possibly-absent
        # parent repo and we don't want to break if it is invalid.
        # Use a custom callable (not ignore_patterns) so we only skip
        # spinoff at the top level of tools/ and not tools/batools/spinoff.
        ignore = (
            (
                lambda s, ns: (
                    {'spinoff'} if os.path.normpath(s) == 'tools' else set()
                )
            )
            if srcdir == 'tools/'
            else None
        )
        shutil.copytree(srcdir, dstdir, dirs_exist_ok=True, ignore=ignore)

    # Inject auto-generated forward-declarations for instance
    # re-exports. Anything in a package's ``__all__`` that's an
    # instance (not a class/function/module) gets a ``#:`` block +
    # type annotation prepended to the filtered ``__init__.py`` so
    # sphinx documents it at the re-export site, not only at the
    # canonical home. Errors out if any public instance lacks a
    # ``#:`` block at canonical home; the design rationale is in
    # ``docs/design/python-api-packages.md``.
    _printstatus('Injecting re-export docs...')
    from batools.reexportdocs import (
        gather_reexport_injections,
        apply_injections,
    )

    reexport_injections = gather_reexport_injections(
        '.', str(ba_data_filtered_dir)
    )
    apply_injections(reexport_injections)

    # Filter all files. Doing this with multiprocessing gives us a very
    # nice speedup vs multithreading which seems gil-constrained.
    _printstatus('Filtering sources...')

    # ProcessPoolExecutor's init calls os.sysconf('SC_SEM_NSEMS_MAX')
    # to verify enough POSIX semaphores are available. Some agent
    # sandboxes deny that syscall; when they do, stub the check out
    # so the pool can still be constructed. Non-sandboxed runs probe
    # successfully and are untouched. Same trick lives in
    # efrotools.code for the parallel pylint path.
    try:
        os.sysconf('SC_SEM_NSEMS_MAX')
    except PermissionError:
        import concurrent.futures.process as _cfp

        # pylint: disable=protected-access
        _cfp._check_system_limits = lambda: None
        # pylint: enable=protected-access

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

    # Exclude private submodule rst pages from the runtime tree. Each
    # ``_foo.py`` / ``_foo/`` under a featureset package is the
    # canonical home for an implementation that the package re-
    # exposes via its ``__all__`` (see
    # ``docs/design/python-api-packages.md``). Documenting them as
    # standalone pages duplicates every re-exported class/function
    # and triggers sphinx ``duplicate object description`` warnings.
    # Skipping the pages lets the re-exports be the sole doc home —
    # which is exactly the user-facing-surface design philosophy.
    ba_data_excludes = _collect_private_submodule_paths(ba_data_filtered_dir)

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
            str(ba_data_filtered_dir),
        ]
        + ba_data_excludes,
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

    # Also exclude private submodules across the tools tree, same
    # reasoning as the runtime case above. Each public package
    # re-exports its private implementation modules via ``__all__``;
    # documenting both produces duplicate-object warnings.
    tools_private = _collect_private_submodule_paths(tools_filtered_dir)
    excludes_tools = excludes_tools + tools_private
    excludes_common = excludes_common + tools_private

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

    # Inject ``:imported-members:`` into apidoc-generated rst for
    # any ``automodule`` whose target module declares ``__all__``.
    # The flag tells autodoc not to skip members whose ``__module__``
    # is foreign — which is what we want for our user-facing
    # packages that deliberately re-export from babase / efro /
    # etc. (see ``docs/design/python-api-packages.md``). Modules
    # without ``__all__`` are left alone so their docs only show
    # their own native members, not every imported helper.
    _printstatus('Injecting imported-members for __all__-declared modules...')
    _inject_imported_members(cache_dir, environ)

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


def _inject_imported_members(rst_dir: Path, environ: dict[str, str]) -> None:
    """Add ``:imported-members:`` to apidoc rst directives selectively.

    Walks every ``.rst`` file produced by sphinx-apidoc, finds every
    ``.. automodule:: <name>`` directive, imports ``<name>`` in a
    subprocess (so dummy-modules are available) to check if it
    declares ``__all__``, and prepends an ``:imported-members:``
    option line when it does.

    Per ``docs/design/python-api-packages.md``: we want re-exports
    documented at consumer pages, but only when the consumer
    explicitly opted in via ``__all__``. Implementation submodules
    without ``__all__`` show only their own native members.
    """
    # Collect all module names referenced from rst files.
    rst_files = sorted(rst_dir.glob('*.rst'))
    automodule_re = re.compile(r'^\.\. automodule:: ([A-Za-z0-9_.]+)\s*$', re.M)
    referenced: set[str] = set()
    for rst in rst_files:
        with open(rst, encoding='utf-8') as infile:
            referenced.update(automodule_re.findall(infile.read()))

    if not referenced:
        return

    # Spawn a single subprocess to resolve ``__all__`` for every
    # referenced module. Cheaper than one import per file and
    # keeps the docs.py process clean of game-runtime imports.
    has_all = _modules_with_all(sorted(referenced), environ)

    def _add_option(match: re.Match[str]) -> str:
        modname = match.group(1)
        if modname not in has_all:
            return match.group(0)
        # Append the directive option as a sibling line under the
        # automodule. Sphinx rst format: option lines are indented
        # 3 spaces under the directive head.
        return match.group(0) + '\n   :imported-members:'

    for rst in rst_files:
        with open(rst, encoding='utf-8') as infile:
            text = infile.read()
        new_text = automodule_re.sub(_add_option, text)
        if new_text != text:
            with open(rst, 'w', encoding='utf-8') as outfile:
                outfile.write(new_text)


def _modules_with_all(modnames: list[str], environ: dict[str, str]) -> set[str]:
    """Return the subset of ``modnames`` that declare ``__all__``.

    Runs in a subprocess so the orchestrator's interpreter doesn't
    have to import all the game modules.
    """
    probe = (
        'import importlib, json, sys\n'
        'out = []\n'
        'for name in sys.argv[1:]:\n'
        '    try:\n'
        '        m = importlib.import_module(name)\n'
        '    except Exception:\n'
        '        continue\n'
        '    if hasattr(m, "__all__"):\n'
        '        out.append(name)\n'
        'print(json.dumps(out))\n'
    )
    result = subprocess.run(
        ['python3', '-c', probe, *modnames],
        env=environ,
        check=True,
        capture_output=True,
        text=True,
    )
    return set(json.loads(result.stdout.strip().splitlines()[-1]))


def _collect_private_submodule_paths(root: Path) -> list[str]:
    """Walk a tree, return paths of underscore-prefixed submodules.

    Used to feed sphinx-apidoc as exclude positional args so it
    won't generate rst pages for private implementation modules.
    The runtime API surface lives in the public package
    ``__init__.py`` via re-exports; private submodules are
    implementation detail and shouldn't have their own doc pages.

    Skips ``__init__.py`` / ``__pycache__`` / other dunder names —
    only ``_<single-underscore>`` items are private by convention.
    """
    paths: list[str] = []
    for dirpath, dirnames, filenames in os.walk(root):
        # Filter dirnames in-place so os.walk doesn't recurse into
        # private dirs (those we just collected the dir path for).
        for d in list(dirnames):
            if d.startswith('_') and not d.startswith('__'):
                paths.append(str(Path(dirpath, d)))
                dirnames.remove(d)
        for f in filenames:
            if not f.endswith('.py'):
                continue
            if f.startswith('_') and not f.startswith('__'):
                paths.append(str(Path(dirpath, f)))
    return paths


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
