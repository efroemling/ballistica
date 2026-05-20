# Released under the MIT License. See LICENSE for details.
#
"""Generate a standalone check-environment for static analysis.

Builds ``build/check_environment/`` containing the runtime Python
tree, C-extension dummy stubs, the ``efro``/``efrotools``/
``bacommon`` libraries, and minimal ``mypy``/``pylint`` configs
rewritten with paths relative to the env root. A small ``Makefile``
inside the env exposes ``mypy`` and ``pylint`` targets — both
delegate to a thin ``_check.py`` entry that calls
``efrotools.code.mypy`` / ``efrotools.code.pylint`` directly, so
the env shares the in-tree client's check infrastructure (same
args, same SC_SEM_NSEMS_MAX shim, same parallel jobs handling)
rather than duplicating it. The env-specific bits are limited to
config-file path rewriting and a ``pconfig/projectconfig.json``
declaring the env's source dirs.

Driven by ``make check_environment`` via lazybuild. Output also
lands at ``build/check_environment.tar.gz``. Intended for
downstream consumers (e.g. bamaster's workspace checker on beef)
that need to run mypy/pylint against ballisticakit-API-aware
Python code without bundling a full client checkout — the
consumer drops user Python files into the env, runs
``make mypy`` / ``make pylint`` (against bamaster's venv), and
gets the same results the in-tree client targets produce.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tarfile

from efro.terminal import Clr

#: Trees copied verbatim into the assembled env.
#:
#: First element is the source path relative to ``projroot``; second
#: is the destination relative to the env root.
_TREES: list[tuple[str, str]] = [
    ('src/assets/ba_data/python', 'python'),
    ('build/dummymodules', 'dummymodules'),
    ('tools/efro', 'tools/efro'),
    # ``efrotools`` is needed for the ``efrotools.pylintplugins``
    # plugin loaded by ``.pylintrc`` AND for ``efrotools.code``
    # which the env's ``_check.py`` entry shells out to.
    ('tools/efrotools', 'tools/efrotools'),
    # ``bacommon`` is imported across the runtime tree
    # (``bacommon.login``, ``bacommon.servermanager``, etc.).
    ('tools/bacommon', 'tools/bacommon'),
]

#: Python-path entries injected into the env's mypy/pylint configs.
#: Always relative to the env root; ``_check.py`` runs from there
#: so relative paths resolve correctly.
_ENV_PYTHON_PATHS = ['python', 'dummymodules', 'tools']


def generate_check_environment(projroot: str) -> None:
    """Top-level entry: assemble the check-environment dir + tarball.

    Ensures ``make dummymodules`` is fresh, copies the
    runtime/library trees, writes config files + a small Makefile,
    and packages everything into ``build/check_environment.tar.gz``.
    """
    print(f'{Clr.BLU}{Clr.BLD}Generating check environment...{Clr.RST}')

    # Dummy-modules must exist so the env can resolve the C-extension
    # stubs at check time. ``make dummymodules`` is lazybuild-tracked
    # so this is cheap when fresh.
    subprocess.run(['make', 'dummymodules'], check=True, cwd=projroot)

    out_root = os.path.join(projroot, 'build', 'check_environment')
    if os.path.isdir(out_root):
        shutil.rmtree(out_root)
    os.makedirs(out_root)

    for src_rel, dst_rel in _TREES:
        src = os.path.join(projroot, src_rel)
        dst = os.path.join(out_root, dst_rel)
        parent = os.path.dirname(dst)
        if parent:
            os.makedirs(parent, exist_ok=True)
        # Strip ``__pycache__`` and ``*.pyc`` — they bloat the bundle
        # and aren't useful for downstream consumers (mypy/pylint
        # regenerate caches themselves).
        shutil.copytree(
            src,
            dst,
            symlinks=False,
            dirs_exist_ok=False,
            ignore=shutil.ignore_patterns('__pycache__', '*.pyc'),
        )

    _write_pylintrc(projroot, out_root)
    _write_mypy_ini(projroot, out_root)
    _write_projectconfig(out_root)
    _write_check_entry(out_root)
    _write_makefile(out_root)

    # No ``.mypy_cache`` is populated here. Downstream consumers
    # (e.g. bamaster's workspace checker) build the cache against
    # *their own* venv at staging time so the cache's options hash
    # and stub-package resolution match what the runtime mypy sees.
    # See ``bamastertools/project.py:_prepopulate_mypy_cache`` for
    # the consumer-side step.

    tar_path = os.path.join(projroot, 'build', 'check_environment.tar.gz')
    if os.path.isfile(tar_path):
        os.remove(tar_path)
    with tarfile.open(tar_path, 'w:gz') as tar:
        tar.add(out_root, arcname='check_environment')

    print(f'{Clr.BLU}Wrote {out_root}.{Clr.RST}')
    print(f'{Clr.BLU}Wrote {tar_path}.{Clr.RST}')


def _write_pylintrc(projroot: str, out_root: str) -> None:
    """Write ``.pylintrc`` with init-hook pointing at env-relative paths.

    Mirrors the in-tree generation logic in
    ``efrotools.toolconfig.filter_toolconfig`` for the
    ``__EFRO_PYLINT_INIT__`` substitution, but uses paths relative
    to the env root instead of absolute paths under projroot.
    """
    template_path = os.path.join(projroot, 'pconfig/toolconfigsrc/pylintrc')
    with open(template_path, encoding='utf-8') as infile:
        body = infile.read()

    cstr = 'init-hook=import sys;'
    for i, path in enumerate(_ENV_PYTHON_PATHS):
        cstr += f" sys.path.insert({i}, '{path}');"
    body = body.replace('__EFRO_PYLINT_INIT__', cstr)

    with open(
        os.path.join(out_root, '.pylintrc'), 'w', encoding='utf-8'
    ) as outfile:
        outfile.write(body)


def _write_mypy_ini(projroot: str, out_root: str) -> None:
    """Write ``.mypy.ini`` with mypy_path pointing at env-relative paths.

    Mirrors ``filter_toolconfig`` for ``__EFRO_PYTHON_PATHS__`` and
    ``__EFRO_MYPY_STANDARD_SETTINGS__`` substitution. The standard
    settings block comes from ``efrotools.toolconfig`` so the env
    and the in-tree client stay in sync.
    """
    import textwrap

    template_path = os.path.join(projroot, 'pconfig/toolconfigsrc/mypy.ini')
    with open(template_path, encoding='utf-8') as infile:
        body = infile.read()

    body = body.replace('__EFRO_PYTHON_PATHS__', ':'.join(_ENV_PYTHON_PATHS))

    # Canonical mypy settings block. Kept in sync verbatim with
    # ``efrotools.toolconfig.filter_toolconfig``'s local
    # ``mypy_standard_settings`` (which generates the in-tree
    # ``.mypy.ini``). Both call sites read this block from the same
    # toolconfigsrc template; the duplicated string here is the only
    # bit that has to stay aligned by hand. Daily
    # ``verify-check-environment`` catches drift via end-to-end check
    # behavior — if the in-tree client lints clean but the env's
    # check fails on the same files, this block is the first thing
    # to compare.
    mypy_standard_settings = textwrap.dedent("""
    # We don't want all of our plain scripts complaining
    # about __main__ being redefined.
    scripts_are_modules = True

    # Try to be as strict as we can about using types everywhere.
    no_implicit_optional = True
    warn_unused_ignores = True
    warn_no_return = True
    warn_return_any = True
    warn_redundant_casts = True
    warn_unreachable = True
    warn_unused_configs = True
    disallow_incomplete_defs = True
    disallow_untyped_defs = True
    disallow_untyped_decorators = True
    disallow_untyped_calls = True
    disallow_any_unimported = True
    disallow_subclassing_any = True
    strict_equality = True
    local_partial_types = True
    no_implicit_reexport = True
    fixed_format_cache = True

    enable_error_code = redundant-expr, truthy-bool, \
truthy-function, unused-awaitable, explicit-override
    """).strip()
    body = body.replace(
        '__EFRO_MYPY_STANDARD_SETTINGS__', mypy_standard_settings
    )

    with open(
        os.path.join(out_root, '.mypy.ini'), 'w', encoding='utf-8'
    ) as outfile:
        outfile.write(body)


def _write_projectconfig(out_root: str) -> None:
    """Write the minimal ``pconfig/projectconfig.json`` the env needs.

    ``efrotools.code.get_script_filenames`` reads
    ``python_source_dirs`` from here to gather files for mypy/pylint.
    The env's default file set is just its bundled ``python/`` tree;
    downstream consumers override at invocation time (e.g. by
    pointing at a user workspace).
    """
    config = {'python_source_dirs': ['python']}
    pconfig_dir = os.path.join(out_root, 'pconfig')
    os.makedirs(pconfig_dir, exist_ok=True)
    with open(
        os.path.join(pconfig_dir, 'projectconfig.json'),
        'w',
        encoding='utf-8',
    ) as outfile:
        json.dump(config, outfile, indent=2)
        outfile.write('\n')


def _write_check_entry(out_root: str) -> None:
    """Write the ``_check.py`` entry that delegates to efrotools.code.

    The shared in-tree code path
    (``efrotools.code.mypy`` / ``efrotools.code.pylint`` for the
    projectconfig-default path; ``mypy_files`` / ``runpylint`` for an
    explicit directory) handles the actual tool invocation — same
    args, same parallel jobs config, same SC_SEM_NSEMS_MAX shim
    under sandboxed runners. ``full=True`` for mypy bypasses the
    incremental cache; ``nocache=True`` for pylint bypasses the
    FileCache dirty-dep tracking. Both modes are right for the
    env's "fresh extract, lint everything" use case where persisted
    caches would be stale anyway.

    Optional second arg: a directory path to lint instead of the
    bundled ``python/`` tree. Used by downstream consumers (beef's
    workspace checker) that drop user code into the env and want to
    lint just that subtree.

    Optional ``--format=FMT`` (``text`` default or ``json``) selects
    the output format. JSON mode emits structured diagnostics on
    stdout — pylint's ``json2`` for pylint, mypy's
    ``--output=json --show-error-end`` for mypy — which beef parses
    to map errors to source locations.
    """
    content = (
        '# Generated by tools/batools/checkenvironment.py —'
        ' do not edit.\n'
        '"""Entry point for the env\'s make mypy / make pylint."""\n'
        '\n'
        'from __future__ import annotations\n'
        '\n'
        'import os\n'
        'import sys\n'
        'from pathlib import Path\n'
        '\n'
        '# Make the env\'s bundled tools/ importable so'
        ' efrotools.code\n'
        '# resolves to the shared in-tree client check code.\n'
        '_PROJROOT = Path(__file__).resolve().parent\n'
        'sys.path.insert(0, str(_PROJROOT / "tools"))\n'
        '\n'
        '# pylint: disable=wrong-import-position\n'
        'from efrotools.code import (  # noqa: E402\n'
        '    mypy,\n'
        '    mypy_files,\n'
        '    pylint,\n'
        '    runpylint,\n'
        ')\n'
        '\n'
        '\n'
        'def _gather_py_files(rootdir: str) -> list[str]:\n'
        '    """Walk a directory for .py files (skipping symlinks +'
        ' flycheck_).\n'
        '\n'
        '    Mirrors the filters in'
        ' ``efrotools.code.get_script_filenames``.\n'
        '    Restricted to ``*.py`` (no shebang detection) — the\n'
        '    workspace-checker use case is user-authored .py files.\n'
        '    """\n'
        '    found: list[str] = []\n'
        '    for root, _dirs, files in os.walk(rootdir):\n'
        '        for fname in files:\n'
        '            full = os.path.join(root, fname)\n'
        '            if os.path.islink(full):\n'
        '                continue\n'
        "            if 'flycheck_' in fname:\n"
        '                continue\n'
        "            if not fname.endswith('.py'):\n"
        '                continue\n'
        '            found.append(full)\n'
        '    return sorted(found)\n'
        '\n'
        '\n'
        'def _usage() -> int:\n'
        '    print(\n'
        '        f"usage: {sys.argv[0]} mypy|pylint [DIR]'
        ' [--format=text|json]",\n'
        '        file=sys.stderr,\n'
        '    )\n'
        '    return 2\n'
        '\n'
        '\n'
        'def main() -> int:\n'
        '    # Parse: <cmd> [DIR] [--format=FMT]. Order is flexible'
        ' so\n'
        '    # the Makefile can pass DIR and FORMAT independently.\n'
        '    output_format = "text"\n'
        '    positional: list[str] = []\n'
        '    for arg in sys.argv[1:]:\n'
        '        if arg.startswith("--format="):\n'
        '            output_format = arg.split("=", 1)[1]\n'
        '        elif arg:\n'
        '            positional.append(arg)\n'
        '    if not positional or len(positional) > 2 or'
        ' positional[0] not in ("mypy", "pylint"):\n'
        '        return _usage()\n'
        '    if output_format not in ("text", "json"):\n'
        '        print(\n'
        '            f"unknown --format value: {output_format!r}",\n'
        '            file=sys.stderr,\n'
        '        )\n'
        '        return 2\n'
        '\n'
        '    cmd = positional[0]\n'
        '    dirarg = positional[1] if len(positional) == 2 else None\n'
        '    if dirarg:\n'
        '        files = _gather_py_files(dirarg)\n'
        '        if not files:\n'
        '            print(\n'
        '                f"No .py files found under: {dirarg}",\n'
        '                file=sys.stderr,\n'
        '            )\n'
        '            return 1\n'
        '        if cmd == "mypy":\n'
        '            mypy_files(_PROJROOT, files, full=True,\n'
        '                       output_format=output_format)\n'
        '        else:\n'
        '            runpylint(_PROJROOT, files, extra=False,\n'
        '                      output_format=output_format)\n'
        '    else:\n'
        '        if cmd == "mypy":\n'
        '            mypy(_PROJROOT, full=True,\n'
        '                 output_format=output_format)\n'
        '        else:\n'
        '            pylint(\n'
        '                _PROJROOT,\n'
        '                full=False,\n'
        '                fast=False,\n'
        '                extra=False,\n'
        '                nocache=True,\n'
        '                output_format=output_format,\n'
        '            )\n'
        '    return 0\n'
        '\n'
        '\n'
        'if __name__ == "__main__":\n'
        '    sys.exit(main())\n'
    )
    with open(
        os.path.join(out_root, '_check.py'), 'w', encoding='utf-8'
    ) as outfile:
        outfile.write(content)


def _write_makefile(out_root: str) -> None:
    """Write a minimal Makefile delegating to ``_check.py``.

    Targets mirror the in-tree ``make mypy`` / ``make pylint`` (via
    ``efrotools.code``) — same args, same shim behavior. Pass
    ``DIR=...`` to lint a specific subtree instead of the bundled
    ``python/``; pass ``FORMAT=json`` for pylint ``json2`` / mypy
    NDJSON structured output (consumed by editor / beef)::

        make mypy DIR=workspace
        make pylint DIR=workspace FORMAT=json
    """
    content = (
        '# Generated by tools/batools/checkenvironment.py —'
        ' do not edit.\n'
        '#\n'
        '# Delegates to _check.py, which calls efrotools.code\n'
        '# directly. Same code path the in-tree client uses for its'
        ' own\n'
        '# make mypy / make pylint targets.\n'
        '#\n'
        '# DIR=somedir   — lint a specific subtree instead of the\n'
        '#                 bundled python/ tree.\n'
        '# FORMAT=json   — structured stdout output (pylint json2,\n'
        '#                 mypy --output=json --show-error-end).\n'
        '#                 Default is text.\n'
        '\n'
        '.PHONY: mypy pylint\n'
        '\n'
        '# $(if VAR,then,else) emits the then-branch only when VAR\n'
        '# is non-empty, so unset DIR/FORMAT do not produce empty\n'
        '# args that confuse argv parsing in _check.py.\n'
        '\n'
        'mypy:\n'
        '\tpython3 _check.py mypy $(DIR)'
        ' $(if $(FORMAT),--format=$(FORMAT),)\n'
        '\n'
        'pylint:\n'
        '\tpython3 _check.py pylint $(DIR)'
        ' $(if $(FORMAT),--format=$(FORMAT),)\n'
    )
    with open(
        os.path.join(out_root, 'Makefile'), 'w', encoding='utf-8'
    ) as outfile:
        outfile.write(content)
