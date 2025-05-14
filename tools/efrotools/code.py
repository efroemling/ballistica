# Released under the MIT License. See LICENSE for details.
#
# pylint: disable=too-many-lines
"""Functionality for formatting, linting, etc. code."""

from __future__ import annotations

import os
import sys
import time
import tempfile
import datetime
import subprocess
from pathlib import Path
from typing import TYPE_CHECKING

from efro.error import CleanError

# WTF Pylint. This is our package. It goes last.
# pylint: disable=useless-suppression, wrong-import-order
from efrotools.filecache import FileCache

# pylint: enable=useless-suppression, wrong-import-order

if TYPE_CHECKING:
    from typing import Any


def format_cpp_str(
    projroot: Path, text: str, filename: str = 'untitled.cc'
) -> str:
    """Run clang-format inline on c++ code.

    Note that some cpp formatting keys off the filename, so a fake one can
    be optionally provided.
    """
    cfconfig = os.path.join(projroot, '.clang-format')

    if not os.path.isfile(cfconfig):
        raise CleanError(
            f".clang-format file not found in '{projroot}';"
            " do 'make env' to generate it."
        )

    with tempfile.TemporaryDirectory() as tempdir:
        tfilename = os.path.join(tempdir, filename)
        with open(tfilename, 'w', encoding='utf-8') as outfile:
            outfile.write(text)

        # Note: clang-format allows '--style=file:<path>' in version 14
        # or newer, but older versions are still common, so the easiest
        # way to work everywhere is to just copy our config file into
        # the temp dir.
        with open(cfconfig, 'rb') as infileb:
            with open(os.path.join(tempdir, '.clang-format'), 'wb') as outfileb:
                outfileb.write(infileb.read())

        subprocess.run(
            ['clang-format', '--style=file', '-i', tfilename], check=True
        )
        with open(tfilename, encoding='utf-8') as infile:
            return infile.read()


def format_project_cpp_files(projroot: Path, full: bool) -> None:
    """Run clang-format on all of our source code (multithreaded)."""
    import concurrent.futures
    from multiprocessing import cpu_count

    from efrotools.util import get_files_hash

    if os.path.abspath(projroot) != os.getcwd():
        raise RuntimeError('We expect to be running from project root.')

    cachepath = Path(projroot, '.cache/format_project_cpp_files')
    if full and cachepath.exists():
        cachepath.unlink()
    cache = FileCache(cachepath)
    cfconfig = '.clang-format'

    if not os.path.isfile(cfconfig):
        raise CleanError(
            f".clang-format file not found in '{os.getcwd()}';"
            " do 'make env' to generate it."
        )

    # Exclude generated files or else we could mess up dependencies
    # by mucking with their modtimes.
    filenames = get_code_filenames(projroot, include_generated=False)
    confighash = get_files_hash([cfconfig])
    cache.update(filenames, confighash)

    dirtyfiles = cache.get_dirty_files()

    def format_file(filename: str) -> dict[str, Any]:
        start_time = time.monotonic()

        result = subprocess.call(['clang-format', '-i', filename])
        if result != 0:
            raise RuntimeError(f'Formatting failed for {filename}')
        duration = time.monotonic() - start_time
        print(f'Formatted {filename} in {duration:.2f} seconds.')
        sys.stdout.flush()
        return {'f': filename, 't': duration}

    with concurrent.futures.ThreadPoolExecutor(
        max_workers=cpu_count()
    ) as executor:
        # Converting this to a list will propagate any errors.
        list(executor.map(format_file, dirtyfiles))

    if dirtyfiles:
        # Since we changed files, need to update hashes again.
        cache.update(filenames, confighash)
        cache.mark_clean(filenames)
        cache.write()
    print(
        f'Formatting is up to date for {len(filenames)} code files.', flush=True
    )


def check_cpplint(projroot: Path, full: bool) -> None:
    """Run cpplint on all our applicable code."""
    # pylint: disable=too-many-locals
    from concurrent.futures import ThreadPoolExecutor
    from multiprocessing import cpu_count

    from efrotools.project import getprojectconfig
    from efro.terminal import Clr

    os.chdir(projroot)
    filenames = get_code_filenames(projroot, include_generated=True)
    for fpath in filenames:
        if ' ' in fpath:
            raise RuntimeError(f'Found space in path {fpath}; unexpected.')

    # Check the config for a list of ones to ignore.
    code_blacklist: list[str] = getprojectconfig(projroot).get(
        'cpplint_blacklist', []
    )

    # Just pretend blacklisted ones don't exist.
    filenames = [f for f in filenames if f not in code_blacklist]
    filenames = [f for f in filenames if not f.endswith('.mm')]

    cachepath = Path(projroot, '.cache/check_cpplint')
    if full and cachepath.exists():
        cachepath.unlink()

    cache = FileCache(cachepath)

    # Clear out entries and hashes for files that have changed/etc.
    cache.update(filenames, '')
    dirtyfiles = cache.get_dirty_files()

    if dirtyfiles:
        print(
            f'{Clr.BLU}CppLint checking'
            f' {len(dirtyfiles)} file(s)...{Clr.RST}',
            flush=True,
        )

    disabled_filters: list[str] = [
        # 'build/include_what_you_use',
        # 'build/c++11',
        'build/c++17',
        'readability/nolint',
        'legal/copyright',
        # As of cpplint 2.0 (Oct 2024), seeing a bunch of false positives
        # for this based on how clang-format formats things.
        'whitespace/indent_namespace',
    ]
    filterstr = ','.join(f'-{x}' for x in disabled_filters)

    def lint_file(filename: str) -> None:
        result = subprocess.call(
            [
                sys.executable,
                # Currently (May 2023) seeing a bunch of warnings
                # about 'sre_compile deprecated'. Ignoring them.
                # '-W',
                # 'ignore::DeprecationWarning',
                '-m',
                'cpplint',
                '--root=src',
                f'--filter={filterstr}',
                filename,
            ]
        )
        if result != 0:
            raise CleanError(
                f'{Clr.RED}Cpplint failed for {filename}.{Clr.RST}'
            )

    with ThreadPoolExecutor(max_workers=cpu_count()) as executor:
        # Converting this to a list will propagate any errors.
        list(executor.map(lint_file, dirtyfiles))

    if dirtyfiles:
        cache.mark_clean(filenames)
        cache.write()
    print(
        f'{Clr.GRN}CppLint: all {len(filenames)} files are passing.{Clr.RST}',
        flush=True,
    )


def get_code_filenames(projroot: Path, include_generated: bool) -> list[str]:
    """Return the list of files to lint-check or auto-format.

    Be sure to pass False for include_generated if performing any
    operation that can modify files (such as formatting). Otherwise it
    could cause dirty generated files to not get updated properly when
    their sources change).
    """
    from efrotools.project import getprojectconfig

    exts = ('.h', '.c', '.cc', '.cpp', '.cxx', '.m', '.mm')
    places = getprojectconfig(projroot).get('code_source_dirs', None)
    if places is None:
        raise RuntimeError('code_source_dirs not declared in config')
    codefilenames = []
    for place in places:
        for root, _dirs, files in os.walk(place):
            for fname in files:
                if any(fname.endswith(ext) for ext in exts):
                    path = os.path.join(root, fname)
                    if '/mgen/' in path and not include_generated:
                        pass
                    else:
                        codefilenames.append(path)
    out = sorted(codefilenames)

    # Watch for breakage.
    if places and not out:
        print(
            'WARNING: get_code_filename returning no results;'
            ' is something broken?',
            file=sys.stderr,
        )

    return out


def black_base_args(projroot: Path) -> list[str]:
    """Build base args for running black Python formatting."""
    from efrotools.pyver import PYVER, get_project_python_executable

    pyver = 'py' + PYVER.replace('.', '')
    if len(pyver) != 5:
        raise RuntimeError('Py version filtering err.')

    return [
        get_project_python_executable(projroot),
        '-m',
        'black',
        '--target-version',
        pyver,
        '--line-length',
        '80',
        '--skip-string-normalization',
    ]


def format_project_python_files(projroot: Path, full: bool) -> None:
    """Runs formatting on all of our Python code."""
    from efrotools.util import get_string_hash

    os.chdir(projroot)
    cachepath = Path(projroot, '.cache/format_project_python_files')
    if full and cachepath.exists():
        cachepath.unlink()

    cache = FileCache(cachepath)
    filenames = get_script_filenames(projroot)

    # Calc a config hash so we redo formatting after it changes.
    confighash = get_string_hash(' '.join(black_base_args(projroot)))
    cache.update(filenames, confighash)

    dirtyfiles = cache.get_dirty_files()

    if dirtyfiles:
        # Run a single black command to batch everything.
        cmd = black_base_args(projroot) + list(dirtyfiles)
        if subprocess.run(cmd, check=False).returncode != 0:
            raise CleanError(
                f'Black formatting failed for {len(dirtyfiles)} files.'
            )

    if dirtyfiles:
        # Since we changed files, need to update hashes again.
        cache.update(filenames, confighash)
        cache.mark_clean(filenames)
        cache.write()
    print(
        f'Formatting is up to date for {len(filenames)} script files.',
        flush=True,
    )


def format_python_str(projroot: Path | str, code: str) -> str:
    """Run our Python formatting on the provided inline code."""
    if isinstance(projroot, str):
        projroot = Path(projroot)

    cmd = black_base_args(projroot) + ['--code', code]
    results = subprocess.run(cmd, capture_output=True, check=False)
    if results.returncode == 0:
        return results.stdout.decode()

    cmdprint = cmd[:-1] + ['<input text>']
    raise RuntimeError(
        f'Black command failed: {cmdprint}. stderr: {results.stderr.decode()}'
    )


def _should_include_script(fnamefull: str) -> bool:
    fname = os.path.basename(fnamefull)

    if fname.endswith('.py'):
        return True

    # Look for 'binary' scripts with no extensions too.
    if not fname.startswith('.') and '.' not in fname:
        try:
            with open(fnamefull, encoding='utf-8') as infile:
                line = infile.readline()
            if '/usr/bin/env python' in line or '/usr/bin/python' in line:
                return True
        except UnicodeDecodeError:
            # Actual binary files will probably kick back this error.
            pass
    return False


def get_script_filenames(projroot: Path) -> list[str]:
    """Return the Python filenames to lint-check or auto-format."""
    from efrotools.project import getprojectconfig

    proot = f'{projroot}/'

    filenames = set()
    places = getprojectconfig(projroot).get('python_source_dirs', None)
    if places is None:
        raise RuntimeError('python_source_dirs not declared in config')
    for place in places:
        for root, _dirs, files in os.walk(os.path.join(projroot, place)):
            for fname in files:
                fnamefull = os.path.join(root, fname)
                # Skip symlinks (we conceivably operate on the original too)
                if os.path.islink(fnamefull):
                    continue
                if _should_include_script(fnamefull):
                    assert fnamefull.startswith(proot)
                    filenames.add(fnamefull.removeprefix(proot))
    out = sorted(list(f for f in filenames if 'flycheck_' not in f))

    # Watch for breakage.
    if places and not out:
        print(
            'WARNING: get_script_filename returning no results;'
            ' is something broken?',
            file=sys.stderr,
        )

    return out


def runpylint(projroot: Path, filenames: list[str]) -> None:
    """Run Pylint explicitly on files."""

    pylintrc = Path(projroot, '.pylintrc')
    if not os.path.isfile(pylintrc):
        raise RuntimeError('pylintrc not found where expected')

    # Technically we could just run pylint standalone via command line here,
    # but let's go ahead and run it inline so we're consistent with our cached
    # full-project version.
    _run_pylint(
        projroot, pylintrc, cache=None, dirtyfiles=filenames, allfiles=None
    )


def pylint(projroot: Path, full: bool, fast: bool) -> None:
    """Run Pylint on all scripts in our project (with smart dep tracking)."""
    from efrotools.util import get_files_hash
    from efro.terminal import Clr

    pylintrc = Path(projroot, '.pylintrc')
    if not os.path.isfile(pylintrc):
        raise RuntimeError('pylintrc not found where expected')
    filenames = get_script_filenames(projroot)

    if any(' ' in name for name in filenames):
        raise RuntimeError('found space in path; unexpected')
    script_blacklist: list[str] = []
    filenames = [f for f in filenames if f not in script_blacklist]

    cachebasename = 'check_pylint_fast' if fast else 'check_pylint'
    cachepath = Path(projroot, '.cache', cachebasename)
    if full and cachepath.exists():
        cachepath.unlink()
    cache = FileCache(cachepath)

    # Clear out entries and hashes for files that have changed/etc.
    cache.update(filenames, get_files_hash([pylintrc]))

    # Do a recursive dependency check and mark all files who are
    # either dirty or have a dependency that is dirty.
    filestates: dict[str, bool] = {}
    for fname in filenames:
        _dirty_dep_check(fname, filestates, cache, fast, 0)

    dirtyfiles = [k for k, v in filestates.items() if v]

    # Let's sort by modification time, so ones we're actively trying
    # to fix get linted first and we see remaining errors faster.
    dirtyfiles.sort(reverse=True, key=lambda f: os.stat(f).st_mtime)

    if dirtyfiles:
        print(
            f'{Clr.BLU}Pylint checking {len(dirtyfiles)} file(s)...{Clr.RST}',
            flush=True,
        )
        try:
            _run_pylint(projroot, pylintrc, cache, dirtyfiles, filenames)
        finally:
            # No matter what happens, we still want to
            # update our disk cache (since some lints may have passed).
            cache.write()
    print(
        f'{Clr.GRN}Pylint: all {len(filenames)} files are passing.{Clr.RST}',
        flush=True,
    )

    cache.write()


def _dirty_dep_check(
    fname: str,
    filestates: dict[str, bool],
    cache: FileCache,
    fast: bool,
    recursion: int,
) -> bool:
    """Recursively check a file's deps and return whether it is dirty."""
    # pylint: disable=too-many-branches

    if not fast:
        # Check for existing dirty state (only applies in non-fast where
        # we recurse infinitely).
        curstate = filestates.get(fname)
        if curstate is not None:
            return curstate

        # Ok; there's no current state for this file.
        #
        # First lets immediately mark it as clean so if a dependency of ours
        # queries it we won't loop infinitely.  (If we're actually dirty that
        # will be reflected properly once we're done).
        if not fast:
            filestates[fname] = False

    # If this dependency has disappeared, consider that dirty.
    if fname not in cache.entries:
        dirty = True
    else:
        cacheentry = cache.entries[fname]

        # See if we ourself are dirty
        if 'hash' not in cacheentry:
            dirty = True
        else:
            # Ok we're clean; now check our dependencies..
            dirty = False

            # Only increment recursion in fast mode, and
            # skip dependencies if we're pass the recursion limit.
            recursion2 = recursion
            if fast:
                # Our one exception is top level ba which basically aggregates.
                if not fname.endswith('/babase/__init__.py'):
                    recursion2 += 1
            if recursion2 <= 1:
                deps = cacheentry.get('deps', [])
                for dep in deps:
                    # If we have a dep that no longer exists, WE are dirty.
                    if not os.path.exists(dep):
                        dirty = True
                        break
                    if _dirty_dep_check(
                        dep, filestates, cache, fast, recursion2
                    ):
                        dirty = True
                        break

    # Cache and return our dirty state.
    #
    # Note: for fast mode we limit to recursion==0 so we only write when
    # the file itself is being directly visited.
    if recursion == 0:
        filestates[fname] = dirty
    return dirty


def _run_pylint(
    projroot: Path,
    pylintrc: Path | str,
    cache: FileCache | None,
    dirtyfiles: list[str],
    allfiles: list[str] | None,
) -> dict[str, Any]:
    from pylint import lint
    from efro.terminal import Clr

    start_time = time.monotonic()
    args = ['--rcfile', str(pylintrc), '--output-format=colorized']

    args += dirtyfiles
    name = f'{len(dirtyfiles)} file(s)'
    run = lint.Run(args, exit=False)
    if cache is not None:
        assert allfiles is not None
        result = _apply_pylint_run_to_cache(
            projroot, run, dirtyfiles, allfiles, cache
        )
        if result != 0:
            raise CleanError(f'Pylint failed for {result} file(s).')

        # Sanity check: when the linter fails we should always be
        # failing too. If not, it means we're probably missing something
        # and incorrectly marking a failed file as clean.
        if run.linter.msg_status != 0 and result == 0:
            raise RuntimeError(
                'Pylint linter returned non-zero result'
                ' but we did not; this is probably a bug.'
            )
    else:
        if run.linter.msg_status != 0:
            raise CleanError('Pylint failed.')

    duration = time.monotonic() - start_time
    print(
        f'{Clr.GRN}Pylint passed for {name}'
        f' in {duration:.1f} seconds.{Clr.RST}'
    )
    sys.stdout.flush()
    return {'f': dirtyfiles, 't': duration}


def _apply_pylint_run_to_cache(
    projroot: Path,
    run: Any,
    dirtyfiles: list[str],
    allfiles: list[str],
    cache: FileCache,
) -> int:
    # pylint: disable=too-many-locals
    # pylint: disable=too-many-branches
    # pylint: disable=too-many-statements

    from astroid import modutils

    from efrotools.project import getprojectconfig

    # First off, build a map of dirtyfiles to module names (and the
    # corresponding reverse map).
    paths_to_names: dict[str, str] = {}
    names_to_paths: dict[str, str] = {}
    for fname in allfiles:
        try:
            mpath = modutils.modpath_from_file(fname)
            mpath = _filter_module_name('.'.join(mpath))
            paths_to_names[fname] = mpath
        except ImportError:
            # This probably means its a tool or something not in our
            # standard path.  In this case just use its base name.
            # (seems to be what pylint does)
            dummyname = os.path.splitext(os.path.basename(fname))[0]
            paths_to_names[fname] = dummyname
    for key, val in paths_to_names.items():
        names_to_paths[val] = key

    # If there's any cyclic-import errors, just mark all deps as dirty;
    # don't want to add the logic to figure out which ones the cycles
    # cover since they all seems to appear as errors for the last file
    # in the list.
    cycles: int = run.linter.stats.by_msg.get('cyclic-import', 0)
    have_dep_cycles: bool = cycles > 0
    if have_dep_cycles:
        print(f'Found {cycles} cycle-errors; keeping all dirty files dirty.')

    # Update dependencies for what we just ran.
    #
    # A run leaves us with a map of modules to a list of the modules
    # that imports them. We want the opposite though: for each of our
    # modules we want a list of the modules it imports.
    reversedeps = {}

    # Make sure these are all proper module names; no foo.bar.__init__ stuff.
    for key, val in run.linter.stats.dependencies.items():
        sval = [_filter_module_name(m) for m in val]
        reversedeps[_filter_module_name(key)] = sval
    deps: dict[str, set[str]] = {}
    untracked_deps = set()
    for mname, mallimportedby in reversedeps.items():
        for mimportedby in mallimportedby:
            if mname in names_to_paths:
                deps.setdefault(mimportedby, set()).add(mname)
            else:
                untracked_deps.add(mname)

    ignored_untracked_deps: set[str] = set(
        getprojectconfig(projroot).get('pylint_ignored_untracked_deps', [])
    )

    # Add a few that this package itself triggers.
    ignored_untracked_deps |= {'pylint.lint', 'astroid.modutils', 'astroid'}

    # EW; as of Python 3.9, suddenly I'm seeing system modules showing
    # up here where I wasn't before. I wonder what changed. Anyway,
    # explicitly suppressing them here but should come up with a more
    # robust system as I feel this will get annoying fast.
    ignored_untracked_deps |= {
        're',
        'importlib',
        'os',
        'xml.dom',
        'weakref',
        'random',
        'collections.abc',
        'textwrap',
        'webbrowser',
        'signal',
        'pathlib',
        'zlib',
        'json',
        'pydoc',
        'base64',
        'functools',
        'asyncio',
        'xml',
        '__future__',
        'traceback',
        'typing',
        'urllib.parse',
        'ctypes.wintypes',
        'code',
        'urllib.error',
        'threading',
        'xml.etree.ElementTree',
        'pickle',
        'dataclasses',
        'enum',
        'py_compile',
        'urllib.request',
        'math',
        'multiprocessing',
        'socket',
        'getpass',
        'hashlib',
        'ctypes',
        'inspect',
        'rlcompleter',
        'http.client',
        'readline',
        'platform',
        'datetime',
        'copy',
        'concurrent.futures',
        'ast',
        'subprocess',
        'numbers',
        'logging',
        'xml.dom.minidom',
        'uuid',
        'types',
        'tempfile',
        'shutil',
        'shlex',
        'stat',
        'wave',
        'html',
        'binascii',
    }

    # Special case:
    #
    # Ignore generated dummy-modules (we don't directly check those anymore
    # so they'll be listed as external).
    if os.path.exists('build/dummymodules'):
        assert os.path.isdir('build/dummymodules')
        for fname in os.listdir('build/dummymodules'):
            if fname.endswith('.py'):
                ignored_untracked_deps.add(fname.removesuffix('.py'))

    # Ignore some specific untracked deps; complain about any others.
    untracked_deps = set(
        dep
        for dep in untracked_deps
        if dep not in ignored_untracked_deps
        # and not dep.startswith('baplusmeta')
    )
    if untracked_deps:
        raise CleanError(
            f'Pylint found untracked dependencies: {untracked_deps}.'
            ' If these are external to your project, add them to'
            ' "pylint_ignored_untracked_deps" in the project config.'
        )

    # Finally add the dependency lists to our entries (operate on
    # everything in the run; it may not be mentioned in deps).
    no_deps_modules = set()
    for fname in dirtyfiles:
        fmod = paths_to_names[fname]
        if fmod not in deps:
            # Since this code is a bit flaky, lets always announce when we
            # come up empty and keep a whitelist of expected values to ignore.
            no_deps_modules.add(fmod)
            depsval: list[str] = []
        else:
            # Our deps here are module names; store paths.
            depsval = [names_to_paths[dep] for dep in deps[fmod]]
        cache.entries[fname]['deps'] = depsval

    # Let's print a list of modules with no detected deps so we can make
    # sure this is behaving.
    if no_deps_modules:
        if bool(False):
            print(
                'NOTE: no dependencies found for:', ', '.join(no_deps_modules)
            )

    # Ok, now go through all dirtyfiles involved in this run. Mark them
    # as either errored or clean depending on whether there's error info
    # for them in the run stats.

    # Once again need to convert any foo.bar.__init__ to foo.bar.
    stats_by_module: dict[str, Any] = {
        _filter_module_name(key): val
        for key, val in run.linter.stats.by_module.items()
    }
    errcount = 0

    for fname in dirtyfiles:
        mname2 = paths_to_names.get(fname)
        if mname2 is None:
            raise RuntimeError('unable to get module name for "' + fname + '"')
        counts = stats_by_module.get(mname2)

        # 'statement' count seems to be new and always non-zero; ignore it
        if counts is not None:
            counts = {c: v for c, v in counts.items() if c != 'statement'}
        if (counts is not None and any(counts.values())) or have_dep_cycles:
            # print('GOT FAIL FOR', fname, counts)
            if 'hash' in cache.entries[fname]:
                del cache.entries[fname]['hash']
            errcount += 1
        else:
            # print('MARKING FILE CLEAN', mname2, fname)
            cache.entries[fname]['hash'] = cache.curhashes[fname]

    return errcount


def _filter_module_name(mpath: str) -> str:
    """Filter weird module paths such as 'foo.bar.__init__' to 'foo.bar'."""

    # Seems Pylint returns module paths with __init__ on the end in some cases
    # and not in others.  Could dig into it, but for now just filtering them
    # out...
    return mpath[:-9] if mpath.endswith('.__init__') else mpath


def mypy_files(
    projroot: Path, filenames: list[str], full: bool = False, check: bool = True
) -> None:
    """Run MyPy on provided filenames."""

    args = [
        sys.executable,
        '-m',
        'mypy',
        '--pretty',
        '--no-error-summary',
        '--config-file',
        str(Path(projroot, '.mypy.ini')),
    ] + filenames
    if full:
        args.insert(args.index('mypy') + 1, '--no-incremental')
    subprocess.run(args, check=check)


def mypy(projroot: Path, full: bool) -> None:
    """Type check all of our scripts using mypy."""
    from efro.terminal import Clr

    filenames = get_script_filenames(projroot)
    desc = '(full)' if full else '(incremental)'
    print(f'{Clr.BLU}Running Mypy {desc}...{Clr.RST}', flush=True)
    starttime = time.monotonic()
    try:
        mypy_files(projroot, filenames, full)
    except Exception as exc:
        raise CleanError('Mypy failed.') from exc
    duration = time.monotonic() - starttime
    print(
        f'{Clr.GRN}Mypy passed in {duration:.1f} seconds.{Clr.RST}', flush=True
    )


def dmypy(projroot: Path) -> None:
    """Type check all of our scripts using mypy in daemon mode."""
    from efro.terminal import Clr

    filenames = get_script_filenames(projroot)

    # Special case; explicitly kill the daemon.
    if '-stop' in sys.argv:
        subprocess.run(['dmypy', 'stop'], check=False)
        return

    print('Running Mypy (daemon)...', flush=True)
    starttime = time.monotonic()
    try:
        args = [
            'dmypy',
            'run',
            '--timeout',
            '3600',
            '--',
            '--config-file',
            '.mypy.ini',
            '--pretty',
        ] + filenames
        subprocess.run(args, check=True)
    except Exception as exc:
        raise CleanError('Mypy daemon: fail.') from exc
    duration = time.monotonic() - starttime
    print(
        f'{Clr.GRN}Mypy daemon passed in {duration:.1f} seconds.{Clr.RST}',
        flush=True,
    )


def _parse_idea_results(path: Path) -> int:
    """Print errors found in an idea inspection xml file.

    Returns the number of errors found.
    """
    import xml.etree.ElementTree as Et

    error_count = 0
    root = Et.parse(str(path)).getroot()
    for child in root:
        line: str | None = None
        description: str | None = None
        fname: str | None = None
        if child.tag == 'problem':
            is_error = True
            for pchild in child:
                if pchild.tag == 'problem_class':
                    # We still report typos but we don't fail the
                    # check due to them (that just gets tedious).
                    if pchild.text == 'Typo':
                        is_error = False
                if pchild.tag == 'line':
                    line = pchild.text
                if pchild.tag == 'description':
                    description = pchild.text
                if pchild.tag == 'file':
                    fname = pchild.text
                    if isinstance(fname, str):
                        fname = fname.replace('file://$PROJECT_DIR$/', '')
            print(f'{fname}:{line}: {description}')
            if is_error:
                error_count += 1
    return error_count


def _run_idea_inspections(
    projroot: Path,
    scripts: list[str],
    displayname: str,
    inspect: Path,
    verbose: bool,
    inspectdir: Path | None = None,
) -> None:
    """Actually run idea inspections.

    Throw an Exception if anything is found or goes wrong.
    """
    # pylint: disable=too-many-positional-arguments
    # pylint: disable=too-many-locals
    # pylint: disable=consider-using-with

    from efro.terminal import Clr

    start_time = time.monotonic()
    print(
        f'{Clr.BLU}{displayname} checking'
        f' {len(scripts)} file(s)...{Clr.RST}',
        flush=True,
    )
    tmpdir = tempfile.TemporaryDirectory()
    iprof = Path(projroot, '.idea/inspectionProfiles/Default.xml')
    if not iprof.exists():
        iprof = Path(projroot, '.idea/inspectionProfiles/Project_Default.xml')
        if not iprof.exists():
            raise RuntimeError('No default inspection profile found.')
    cmd = [str(inspect), str(projroot), str(iprof), tmpdir.name, '-v2']
    if inspectdir is not None:
        cmd += ['-d', str(inspectdir)]
    running = True

    def heartbeat() -> None:
        """Print the time occasionally to make the log more informative."""
        while running:
            time.sleep(60)
            print('Heartbeat', datetime.datetime.now(), flush=True)

    if verbose:
        import threading

        print(cmd, flush=True)
        threading.Thread(target=heartbeat, daemon=True).start()

    result = subprocess.run(cmd, capture_output=not verbose, check=False)
    running = False
    if result.returncode != 0:
        # In verbose mode this stuff got printed already.
        if not verbose:
            stdout = result.stdout.decode()
            stderr = result.stderr.decode()
            print(
                f'{displayname} inspection failure stdout:\n{stdout}'
                + f'{displayname} inspection failure stderr:\n{stderr}'
            )
        raise RuntimeError(f'{displayname} inspection failed.')
    files = [f for f in os.listdir(tmpdir.name) if not f.startswith('.')]
    total_errors = 0
    if files:
        for fname in files:
            total_errors += _parse_idea_results(Path(tmpdir.name, fname))
    if total_errors > 0:
        raise CleanError(
            f'{Clr.SRED}{displayname} inspection'
            f' found {total_errors} error(s).{Clr.RST}'
        )
    duration = time.monotonic() - start_time
    print(
        f'{Clr.GRN}{displayname} passed for {len(scripts)} files'
        f' in {duration:.1f} seconds.{Clr.RST}',
        flush=True,
    )


def _run_idea_inspections_cached(
    cachepath: Path,
    filenames: list[str],
    full: bool,
    projroot: Path,
    displayname: str,
    inspect: Path,
    verbose: bool,
    inspectdir: Path | None = None,
) -> None:
    # pylint: disable=too-many-locals
    # pylint: disable=too-many-positional-arguments
    import hashlib
    import json

    from efro.terminal import Clr

    md5 = hashlib.md5()

    # Let's calc a single hash from the contents of all script files and only
    # run checks when that changes.  Sadly there's not much else optimization
    # wise that we can easily do, but this will at least prevent re-checks when
    # nothing at all has changed.
    for filename in filenames:
        with open(filename, 'rb') as infile:
            md5.update(infile.read())

    # Also hash a few .idea files so we re-run inspections when they change.
    extra_hash_paths = [
        Path(projroot, '.idea/inspectionProfiles/Default.xml'),
        Path(projroot, '.idea/inspectionProfiles/Project_Default.xml'),
        Path(projroot, '.idea/dictionaries/ericf.xml'),
    ]
    for epath in extra_hash_paths:
        if os.path.exists(epath):
            with open(epath, 'rb') as infile:
                md5.update(infile.read())

    current_hash = md5.hexdigest()
    existing_hash: str | None
    try:
        with open(cachepath, encoding='utf-8') as infile2:
            existing_hash = json.loads(infile2.read())['hash']
    except Exception:
        existing_hash = None
    if full or current_hash != existing_hash:
        _run_idea_inspections(
            projroot,
            filenames,
            displayname,
            inspect=inspect,
            verbose=verbose,
            inspectdir=inspectdir,
        )
        cachepath.parent.mkdir(parents=True, exist_ok=True)
        with open(cachepath, 'w', encoding='utf-8') as outfile:
            outfile.write(json.dumps({'hash': current_hash}))
    print(
        f'{Clr.GRN}{displayname}: all {len(filenames)}'
        f' files are passing.{Clr.RST}',
        flush=True,
    )


def check_pycharm(projroot: Path, full: bool, verbose: bool) -> None:
    """Run pycharm inspections on all our scripts."""

    # FIXME: Generalize this to work with at least linux, possibly windows.
    cachepath = Path('.cache/check_pycharm')
    filenames = get_script_filenames(projroot)
    pycharmroot = Path('/Applications/PyCharm CE.app')
    pycharmbin = Path(pycharmroot, 'Contents/MacOS/pycharm')
    inspect = Path(pycharmroot, 'Contents/bin/inspect.sh')

    # In full mode, clear out pycharm's caches first.
    # It seems we need to spin up the GUI and give it a bit to
    # re-cache system python for this to work...

    # UPDATE: This really slows things down, so we now only do it in
    # very specific cases where time isn't important.
    # (such as our daily full-test-runs)

    # UPDATE 2: Looks like we might no longer need to do the GUI spin-up bit.
    # If we can be certain of this, we can go back to simply blowing away
    # the cache for 'full' mode checks without the env var.
    if full and os.environ.get('EFROTOOLS_FULL_PYCHARM_RECACHE') == '1':
        print('Clearing PyCharm caches...', flush=True)
        subprocess.run(
            'rm -rf ~/Library/Caches/JetBrains/PyCharmCE*',
            shell=True,
            check=True,
        )

        # Hoping this isn't necessary anymore. Need to rework this if it is,
        # since it now gets run through ssh and gui stuff doesn't seem to
        # work that way.
        if bool(False):
            print('Launching GUI PyCharm to rebuild caches...', flush=True)
            with subprocess.Popen(str(pycharmbin)) as process:
                # Wait a bit and ask it nicely to die.
                # We need to make sure it has enough time to do its
                # cache updating thing even if the system is fully under load.
                time.sleep(5 * 60)

                # Seems killing it via applescript is more likely to leave it
                # in a working state for offline inspections than TERM signal..
                subprocess.run(
                    "osascript -e 'tell application \"PyCharm CE\" to quit'",
                    shell=True,
                    check=False,
                )
                print('Waiting for GUI PyCharm to quit...', flush=True)
                process.wait()

    _run_idea_inspections_cached(
        cachepath=cachepath,
        filenames=filenames,
        full=full,
        projroot=projroot,
        displayname='PyCharm',
        inspect=inspect,
        verbose=verbose,
    )


def check_clioncode(projroot: Path, full: bool, verbose: bool) -> None:
    """Run clion inspections on all our code."""

    cachepath = Path('.cache/check_clioncode')
    filenames = get_code_filenames(projroot, include_generated=True)
    clionroot = Path('/Applications/CLion.app')
    # clionbin = Path(clionroot, 'Contents/MacOS/clion')
    inspect = Path(clionroot, 'Contents/bin/inspect.sh')

    # At the moment offline clion inspections seem a bit flaky.
    # They don't seem to run at all if we haven't opened the project
    # in the GUI, and it seems recent changes can get ignored for that
    # reason too.
    # So for now let's try blowing away caches, launching the gui
    # temporarily, and then kicking off inspections after that. Sigh.
    print('Clearing CLion caches...', flush=True)
    caches_root = os.environ['HOME'] + '/Library/Caches/JetBrains'
    if not os.path.exists(caches_root):
        raise RuntimeError(f'CLion caches root not found: {caches_root}')
    subprocess.run(
        'rm -rf ~/Library/Caches/JetBrains/CLion*', shell=True, check=True
    )

    # UPDATE: seems this is unnecessary now; should double check.
    # Note: I'm assuming this project needs to be open when the GUI
    # comes up. Currently just have one project so can rely on auto-open
    # but may need to get fancier later if that changes.
    if bool(True):
        print('Launching GUI CLion to rebuild caches...', flush=True)
        # process = subprocess.Popen(str(clionbin))
        subprocess.run(
            ['open', '-a', clionroot, Path(projroot, 'ballisticakit-cmake')],
            check=True,
        )

        # Wait a moment and ask it nicely to die.
        waittime = 60
        while waittime > 0:
            print(f'Waiting for {waittime} more seconds.', flush=True)
            time.sleep(10)
            waittime -= 10

        # For some reason this is giving a return-code 1 although
        # it appears to be working.
        print('Waiting for GUI CLion to quit...', flush=True)
        subprocess.run(
            [
                'osascript',
                '-e',
                'tell application "CLion" to quit\n'
                'repeat until application "CLion" is not running\n'
                '    delay 1\n'
                'end repeat',
            ],
            check=False,
        )
        time.sleep(5)

        # process.terminate()
        # process.wait(timeout=60)

    print('Launching Offline CLion to run inspections...', flush=True)
    _run_idea_inspections_cached(
        cachepath=cachepath,
        filenames=filenames,
        full=full,
        projroot=Path(projroot, 'ballisticakit-cmake'),
        inspectdir=Path(projroot, 'src/ballistica'),
        displayname='CLion',
        inspect=inspect,
        verbose=verbose,
    )


def check_android_studio(projroot: Path, full: bool, verbose: bool) -> None:
    """Run Android Studio inspections on all our code."""
    # import time

    cachepath = Path('.cache/check_android_studio')
    filenames = get_code_filenames(projroot, include_generated=True)
    clionroot = Path('/Applications/Android Studio.app')
    # clionbin = Path(clionroot, 'Contents/MacOS/studio')
    inspect = Path(clionroot, 'Contents/bin/inspect.sh')

    # At the moment offline clion inspections seem a bit flaky.
    # They don't seem to run at all if we haven't opened the project
    # in the GUI, and it seems recent changes can get ignored for that
    # reason too.
    # So for now let's try blowing away caches, launching the gui
    # temporarily, and then kicking off inspections after that. Sigh.
    # print('Clearing Android Studio caches...', flush=True)
    # subprocess.run('rm -rf ~/Library/Caches/AndroidStudio*',
    #                shell=True,
    #                check=True)

    # Note: I'm assuming this project needs to be open when the GUI
    # comes up. Currently just have one project so can rely on auto-open
    # but may need to get fancier later if that changes.
    # print('Launching GUI CLion to rebuild caches...', flush=True)
    # process = subprocess.Popen(str(clionbin))

    # Wait a moment and ask it nicely to die.
    # time.sleep(120)

    # Seems killing it via applescript is more likely to leave it
    # in a working state for offline inspections than TERM signal..
    # subprocess.run(
    #     "osascript -e 'tell application \"Android Studio\" to quit'",
    #     shell=True)

    # process.terminate()
    # print('Waiting for GUI CLion to quit...', flush=True)
    # process.wait(timeout=60)

    print('Launching Offline Android Studio to run inspections...', flush=True)
    _run_idea_inspections_cached(
        cachepath=cachepath,
        filenames=filenames,
        full=full,
        projroot=Path(projroot, 'ballisticakit-android'),
        inspectdir=Path(
            projroot,
            'ballisticakit-android/BallisticaKit/src/main/cpp/src/ballistica',
        ),
        # inspectdir=None,
        displayname='Android Studio',
        inspect=inspect,
        verbose=verbose,
    )


def sort_jetbrains_dict(original: str) -> str:
    """Given jetbrains dict contents, sort it the way jetbrains would."""
    lines = original.splitlines()
    if lines[2] != '    <words>':
        raise RuntimeError('Unexpected dictionary format.')
    if lines[-3] != '    </words>':
        raise RuntimeError('Unexpected dictionary format b.')
    if not all(
        l.startswith('      <w>') and l.endswith('</w>') for l in lines[3:-3]
    ):
        raise RuntimeError('Unexpected dictionary format.')

    # Sort lines in the words section.
    assert all(l.startswith('      <w>') for l in lines[3:-3])

    # Note: need to pull the </w> off the end of the line when sorting
    # or it messes with the order and we get different results than
    # Jetbrains stuff.
    return '\n'.join(
        lines[:3]
        + sorted(lines[3:-3], key=lambda x: x.replace('</w>', ''))
        + lines[-3:]
    )
