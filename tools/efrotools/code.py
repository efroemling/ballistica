"""Functionality for formatting, linting, etc. code."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import TYPE_CHECKING

from efrotools.filecache import FileCache

if TYPE_CHECKING:
    from typing import Set, List, Dict, Any, Union, Optional


def formatcode(projroot: Path, full: bool) -> None:
    """Run clang-format on all of our source code (multithreaded)."""
    import time
    import concurrent.futures
    from efrotools import get_files_hash, get_proc_count
    os.chdir(projroot)
    cachepath = Path(projroot, 'config/.cache-formatcode')
    if full and cachepath.exists():
        cachepath.unlink()
    cache = FileCache(cachepath)
    cfconfig = Path(projroot, '.clang-format')

    filenames = get_code_filenames(projroot)
    confighash = get_files_hash([cfconfig])
    cache.update(filenames, confighash)

    dirtyfiles = cache.get_dirty_files()

    def format_file(filename: str) -> Dict[str, Any]:
        start_time = time.time()

        # Note: seems os.system does not unlock the gil;
        # make sure to use subprocess.
        result = subprocess.call(['clang-format', '-i', filename])
        if result != 0:
            raise Exception(f'Formatting failed for {filename}')
        duration = time.time() - start_time
        print(f'Formatted {filename} in {duration:.2f} seconds')
        sys.stdout.flush()
        return {'f': filename, 't': duration}

    # NOTE: using fewer workers than we have logical procs for now;
    # we're bottlenecked by one or two long running instances
    # so it actually helps to lighten the load around them.
    # may want to revisit later when we have everything chopped up
    # better
    with concurrent.futures.ThreadPoolExecutor(max_workers=get_proc_count() //
                                               2) as executor:
        # Converting this to a list will propagate any errors.
        list(executor.map(format_file, dirtyfiles))

    if dirtyfiles:
        # Since we changed files, need to update hashes again.
        cache.update(filenames, confighash)
        cache.mark_clean(filenames)
        cache.write()
    print(f'Formatting up to date for {len(filenames)} code files.')


def cpplintcode(projroot: Path, full: bool) -> None:
    """Run lint-checking on all code deemed lint-able."""
    from concurrent.futures import ThreadPoolExecutor
    from efrotools import get_config, get_proc_count
    os.chdir(projroot)
    filenames = get_code_filenames(projroot)
    if any(' ' in name for name in filenames):
        raise Exception('found space in path; unexpected')

    # Check the config for a list of ones to ignore.
    code_blacklist: List[str] = get_config(projroot).get(
        'cpplint_blacklist', [])

    # Just pretend blacklisted ones don't exist.
    filenames = [f for f in filenames if f not in code_blacklist]
    filenames = [f for f in filenames if not f.endswith('.mm')]

    cachepath = Path(projroot, 'config/.cache-lintcode')
    if full and cachepath.exists():
        cachepath.unlink()

    cache = FileCache(cachepath)

    # Clear out entries and hashes for files that have changed/etc.
    cache.update(filenames, '')
    dirtyfiles = cache.get_dirty_files()

    if dirtyfiles:
        print(f'CppLint checking {len(dirtyfiles)} file(s)...')

    def lint_file(filename: str) -> None:
        result = subprocess.call(['cpplint', '--root=src', filename])
        if result != 0:
            raise Exception(f'Linting failed for {filename}')

    with ThreadPoolExecutor(max_workers=get_proc_count() // 2) as executor:
        # Converting this to a list will propagate any errors.
        list(executor.map(lint_file, dirtyfiles))

    if dirtyfiles:
        cache.mark_clean(filenames)
        cache.write()
    print(f'CppLint: {len(filenames)} files up to date.')


def get_code_filenames(projroot: Path) -> List[str]:
    """Return the list of files to lint-check or auto-formatting."""
    from efrotools import get_config
    exts = ('.h', '.cc', '.m', '.mm')
    places = get_config(projroot).get('code_source_dirs', None)
    if places is None:
        raise RuntimeError('code_source_dirs not declared in config')
    codefilenames = []
    for place in places:
        for root, _dirs, files in os.walk(place):
            for fname in files:
                if any(fname.endswith(ext) for ext in exts):
                    codefilenames.append(os.path.join(root, fname))
    codefilenames.sort()
    return codefilenames


def formatscripts(projroot: Path, full: bool) -> None:
    """Runs yapf on all our scripts (multithreaded)."""
    import time
    from concurrent.futures import ThreadPoolExecutor
    from efrotools import get_proc_count, get_files_hash
    os.chdir(projroot)
    cachepath = Path(projroot, 'config/.cache-formatscripts')
    if full and cachepath.exists():
        cachepath.unlink()

    cache = FileCache(cachepath)
    yapfconfig = Path(projroot, '.style.yapf')

    filenames = get_script_filenames(projroot)
    confighash = get_files_hash([yapfconfig])
    cache.update(filenames, confighash)

    dirtyfiles = cache.get_dirty_files()

    def format_file(filename: str) -> None:
        start_time = time.time()
        result = subprocess.call(['yapf', '--in-place', filename])
        if result != 0:
            raise Exception(f'Formatting failed for {filename}')
        duration = time.time() - start_time
        print(f'Formatted {filename} in {duration:.2f} seconds')
        sys.stdout.flush()

    # NOTE: using fewer workers than we have logical procs for now;
    # we're bottlenecked by one or two long running instances
    # so it actually helps to lighten the load around them.
    # may want to revisit later when we have everything chopped up
    # better
    with ThreadPoolExecutor(max_workers=get_proc_count() // 2) as executor:
        # Converting this to a list will propagate any errors
        list(executor.map(format_file, dirtyfiles))

    if dirtyfiles:
        # Since we changed files, need to update hashes again.
        cache.update(filenames, confighash)
        cache.mark_clean(filenames)
        cache.write()
    print(f'Formatting up to date for {len(filenames)} script files.')


def _should_include_script(fnamefull: str) -> bool:
    fname = os.path.basename(fnamefull)

    if fname.endswith('.py'):
        return True

    # Look for 'binary' scripts with no extensions too.
    if not fname.startswith('.') and '.' not in fname:
        try:
            with open(fnamefull) as infile:
                line = infile.readline()
            if '/usr/bin/env python' in line or '/usr/bin/python' in line:
                return True
        except UnicodeDecodeError:
            # actual binary files will probably kick back this error..
            pass
    return False


def get_script_filenames(projroot: Path) -> List[str]:
    """Return the Python filenames to lint-check or auto-format."""
    from efrotools import get_config
    filenames = set()
    places = get_config(projroot).get('python_source_dirs', None)
    if places is None:
        raise RuntimeError('python_source_dirs not declared in config')
    for place in places:
        for root, _dirs, files in os.walk(place):
            for fname in files:
                fnamefull = os.path.join(root, fname)
                if _should_include_script(fnamefull):
                    filenames.add(fnamefull)
    return sorted(list(f for f in filenames if 'flycheck_' not in f))


def pylintscripts(projroot: Path, full: bool, fast: bool) -> None:
    """Run lint-checking on all scripts deemed lint-able."""
    from efrotools import get_files_hash
    pylintrc = Path(projroot, '.pylintrc')
    if not os.path.isfile(pylintrc):
        raise Exception('pylintrc not found where expected')
    filenames = get_script_filenames(projroot)

    if any(' ' in name for name in filenames):
        raise Exception('found space in path; unexpected')
    script_blacklist: List[str] = []
    filenames = [f for f in filenames if f not in script_blacklist]

    cachebasename = '.cache-lintscriptsfast' if fast else '.cache-lintscripts'
    cachepath = Path(projroot, 'config', cachebasename)
    if full and cachepath.exists():
        cachepath.unlink()
    cache = FileCache(cachepath)

    # Clear out entries and hashes for files that have changed/etc.
    cache.update(filenames, get_files_hash([pylintrc]))

    # Do a recursive dependency check and mark all files who are
    # either dirty or have a dependency that is dirty.
    filestates: Dict[str, bool] = {}
    for fname in filenames:
        _dirty_dep_check(fname, filestates, cache, fast, 0)

    dirtyfiles = [k for k, v in filestates.items() if v]

    # Let's sort by modification time, so ones we're actively trying
    # to fix get linted first and we see remaining errors faster.
    dirtyfiles.sort(reverse=True, key=lambda f: os.stat(f).st_mtime)

    if dirtyfiles:
        print(f'Pylint checking {len(dirtyfiles)} file(s)...', flush=True)
        try:
            _run_script_lint(projroot, pylintrc, cache, dirtyfiles, filenames)
        except Exception:
            # Note: even if we fail here, we still want to
            # update our disk cache (since some lints may have passed).
            print('Pylint failed.', flush=True)
            import traceback
            traceback.print_exc()
            cache.write()
            sys.exit(255)
    print(f'Pylint: {len(filenames)} files up to date.', flush=True)

    cache.write()


def _dirty_dep_check(fname: str, filestates: Dict[str, bool], cache: FileCache,
                     fast: bool, recursion: int) -> bool:
    """Recursively check a file's deps and return whether it is dirty."""
    # pylint: disable=too-many-branches

    if not fast:
        # Check for existing dirty state (only applies in non-fast where
        # we recurse infinitely).
        curstate = filestates.get(fname)
        if curstate is not None:
            return curstate

        # Ok; there's no current state for this file.
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
                if not fname.endswith('/ba/__init__.py'):
                    recursion2 += 1
            if recursion2 <= 1:
                deps = cacheentry.get('deps', [])
                for dep in deps:
                    # If we have a dep that no longer exists, WE are dirty.
                    if not os.path.exists(dep):
                        dirty = True
                        break
                    if _dirty_dep_check(dep, filestates, cache, fast,
                                        recursion2):
                        dirty = True
                        break

    # Cache and return our dirty state..
    # Note: for fast mode we limit to recursion==0 so we only write when
    # the file itself is being directly visited.
    if recursion == 0:
        filestates[fname] = dirty
    return dirty


def _run_script_lint(projroot: Path, pylintrc: Union[Path, str],
                     cache: FileCache, dirtyfiles: List[str],
                     allfiles: List[str]) -> Dict[str, Any]:
    import time
    from pylint import lint
    start_time = time.time()
    args = ['--rcfile', str(pylintrc)]

    args += dirtyfiles
    name = f'{len(dirtyfiles)} file(s)'
    run = lint.Run(args, do_exit=False)
    result = _apply_pylint_run_to_cache(projroot, run, dirtyfiles, allfiles,
                                        cache)
    if result != 0:
        raise Exception(f'Linting failed for {result} file(s).')

    # Sanity check: when the linter fails we should always be failing too.
    # If not, it means we're probably missing something and incorrectly
    # marking a failed file as clean.
    if run.linter.msg_status != 0 and result == 0:
        raise Exception('linter returned non-zero result but we did not;'
                        ' this is probably a bug.')
    # result = run.linter.msg_status
    # we can run
    duration = time.time() - start_time
    print(f'Pylint passed for {name} in {duration:.1f} seconds.')
    sys.stdout.flush()
    return {'f': dirtyfiles, 't': duration}


def _apply_pylint_run_to_cache(projroot: Path, run: Any, dirtyfiles: List[str],
                               allfiles: List[str], cache: FileCache) -> int:
    # pylint: disable=too-many-locals
    # pylint: disable=too-many-branches
    # pylint: disable=too-many-statements
    from astroid import modutils
    from efrotools import get_config

    # First off, build a map of dirtyfiles to module names
    # (and the corresponding reverse map).
    paths_to_names: Dict[str, str] = {}
    names_to_paths: Dict[str, str] = {}
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
    # don't want to add the logic to figure out which ones the cycles cover
    # since they all seems to appear as errors for the last file in the list.
    cycles: int = run.linter.stats.get('by_msg', {}).get('cyclic-import', 0)
    have_dep_cycles: bool = cycles > 0
    if have_dep_cycles:
        print(f'Found {cycles} cycle-errors; keeping all dirty files dirty.')

    # Update dependencies for what we just ran.
    # A run leaves us with a map of modules to a list of the modules that
    # imports them.  We want the opposite though: for each of our modules
    # we want a list of the modules it imports.
    reversedeps = {}

    # Make sure these are all proper module names; no foo.bar.__init__ stuff.
    for key, val in run.linter.stats['dependencies'].items():
        sval = [_filter_module_name(m) for m in val]
        reversedeps[_filter_module_name(key)] = sval
    deps: Dict[str, Set[str]] = {}
    untracked_deps = set()
    for mname, mallimportedby in reversedeps.items():
        for mimportedby in mallimportedby:
            if mname in names_to_paths:
                deps.setdefault(mimportedby, set()).add(mname)
            else:
                untracked_deps.add(mname)

    ignored_untracked_deps: List[str] = get_config(projroot).get(
        'pylint_ignored_untracked_deps', [])

    # Add a few that this package itself triggers.
    ignored_untracked_deps += ['pylint.lint', 'astroid.modutils', 'astroid']

    # Ignore some specific untracked deps; complain about any others.
    untracked_deps = set(dep for dep in untracked_deps
                         if dep not in ignored_untracked_deps)
    if untracked_deps:
        raise Exception(
            f'Found untracked dependencies: {untracked_deps}.'
            ' If these are external to your project, add them to'
            ' "pylint_ignored_untracked_deps" in the project config.')

    # Finally add the dependency lists to our entries (operate on
    # everything in the run; it may not be mentioned in deps).
    no_deps_modules = set()
    for fname in dirtyfiles:
        fmod = paths_to_names[fname]
        if fmod not in deps:

            # Since this code is a bit flaky, lets always announce when
            # we come up empty and keep a whitelist of expected values to
            # ignore.
            no_deps_modules.add(fmod)
            depsval: List[str] = []
        else:
            # Our deps here are module names; store paths.
            depsval = [names_to_paths[dep] for dep in deps[fmod]]
        cache.entries[fname]['deps'] = depsval

    # Let's print a list of modules with no detected deps so we can make sure
    # this is behaving.
    if no_deps_modules:
        # noinspection PyUnreachableCode
        if False:  # pylint: disable=using-constant-test
            print('NOTE: no dependencies found for:',
                  ', '.join(no_deps_modules))

    # Ok, now go through all dirtyfiles involved in this run.
    # Mark them as either errored or clean depending on whether there's
    # error info for them in the run stats.

    # Once again need to convert any foo.bar.__init__ to foo.bar.
    stats_by_module: Dict[str, Any] = {
        _filter_module_name(key): val
        for key, val in run.linter.stats['by_module'].items()
    }
    errcount = 0

    for fname in dirtyfiles:
        mname2 = paths_to_names.get(fname)
        if mname2 is None:
            raise Exception('unable to get module name for "' + fname + '"')
        counts = (None if mname2 is None else stats_by_module.get(mname2))

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
            cache.entries[fname]['hash'] = (cache.curhashes[fname])

    return errcount


def _filter_module_name(mpath: str) -> str:
    """Filter weird module paths such as 'foo.bar.__init__' to 'foo.bar'."""

    # Seems Pylint returns module paths with __init__ on the end in some cases
    # and not in others.  Could dig into it, but for now just filtering them
    # out...
    return mpath[:-9] if mpath.endswith('.__init__') else mpath


def runmypy(filenames: List[str], full: bool = False,
            check: bool = True) -> None:
    """Run MyPy on provided filenames."""
    args = [
        'python3.7', '-m', 'mypy', '--pretty', '--config-file', '.mypy.ini'
    ] + filenames
    if full:
        args.insert(1, '--no-incremental')
    subprocess.run(args, check=check)


def mypyscripts(projroot: Path, full: bool) -> None:
    """Run mypy on all of our scripts."""
    import time
    filenames = get_script_filenames(projroot)
    print('Running Mypy ' + ('(full)' if full else '(incremental)') + '...')
    starttime = time.time()
    try:
        runmypy(filenames, full)
    except Exception:
        print('Mypy: fail.')
        sys.exit(255)
    duration = time.time() - starttime
    print(f'Mypy passed in {duration:.1f} seconds.')


def _parse_idea_results(path: Path) -> int:
    """Print errors found in an idea inspection xml file.

    Returns the number of errors found.
    """
    import xml.etree.ElementTree as Et
    error_count = 0
    root = Et.parse(str(path)).getroot()
    for child in root:
        line: Optional[str] = None
        description: Optional[str] = None
        fname: Optional[str] = None
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


def _run_idea_inspections(projroot: Path,
                          scripts: List[str],
                          displayname: str,
                          inspect: Path,
                          verbose: bool,
                          inspectdir: Path = None) -> None:
    """Actually run idea inspections.

    Throw an Exception if anything is found or goes wrong.
    """
    # pylint: disable=too-many-locals
    import tempfile
    import time
    import datetime
    start_time = time.time()
    print(f'{displayname} checking', len(scripts), 'file(s)...', flush=True)
    tmpdir = tempfile.TemporaryDirectory()
    iprof = Path(projroot, '.idea/inspectionProfiles/Default.xml')
    if not iprof.exists():
        iprof = Path(projroot, '.idea/inspectionProfiles/Project_Default.xml')
        if not iprof.exists():
            raise Exception("No default inspection profile found.")
    cmd = [str(inspect), str(projroot), str(iprof), tmpdir.name, '-v2']
    if inspectdir is not None:
        cmd += ['-d', str(inspectdir)]
    running = True

    def heartbeat() -> None:
        """Print the time occasionally to make the log more informative."""
        while running:
            time.sleep(60)
            print("Heartbeat", datetime.datetime.now(), flush=True)

    if verbose:
        import threading
        print(cmd, flush=True)
        threading.Thread(target=heartbeat, daemon=True).start()

    result = subprocess.run(cmd, capture_output=not verbose, check=False)
    running = False
    if result.returncode != 0:
        # In verbose mode this stuff got printed already.
        if not verbose:
            stdout = (result.stdout.decode() if isinstance(
                result.stdout, bytes) else str(result.stdout))
            stderr = (result.stderr.decode() if isinstance(
                result.stdout, bytes) else str(result.stdout))
            print(f'{displayname} inspection failure stdout:\n{stdout}' +
                  f'{displayname} inspection failure stderr:\n{stderr}')
        raise RuntimeError(f"{displayname} inspection failed.")
    files = [f for f in os.listdir(tmpdir.name) if not f.startswith('.')]
    total_errors = 0
    if files:
        for fname in files:
            total_errors += _parse_idea_results(Path(tmpdir.name, fname))
    if total_errors > 0:
        raise RuntimeError(
            f"{displayname} inspection found {total_errors} error(s).")
    duration = time.time() - start_time

    print(
        f'{displayname} passed for {len(scripts)} files'
        f' in {duration:.1f} seconds.',
        flush=True)


def _run_idea_inspections_cached(cachepath: Path,
                                 filenames: List[str],
                                 full: bool,
                                 projroot: Path,
                                 displayname: str,
                                 inspect: Path,
                                 verbose: bool,
                                 inspectdir: Path = None) -> None:
    # pylint: disable=too-many-locals
    import hashlib
    import json
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
        Path(projroot, '.idea/dictionaries/ericf.xml')
    ]
    for epath in extra_hash_paths:
        if os.path.exists(epath):
            with open(epath, 'rb') as infile:
                md5.update(infile.read())

    current_hash = md5.hexdigest()
    existing_hash: Optional[str]
    try:
        with open(cachepath) as infile2:
            existing_hash = json.loads(infile2.read())['hash']
    except Exception:
        existing_hash = None
    if full or current_hash != existing_hash:
        _run_idea_inspections(projroot,
                              filenames,
                              displayname,
                              inspect=inspect,
                              verbose=verbose,
                              inspectdir=inspectdir)
        with open(cachepath, 'w') as outfile:
            outfile.write(json.dumps({'hash': current_hash}))
    print(f'{displayname}: {len(filenames)} files up to date.')


def pycharmscripts(projroot: Path, full: bool, verbose: bool) -> None:
    """Run pycharm inspections on all our scripts."""

    import time

    cachepath = Path('config/.cache-pycharmscripts')
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
    if full and os.environ.get('EFROTOOLS_FULL_PYCHARM_RECACHE') == '1':
        print('Clearing PyCharm caches...', flush=True)
        subprocess.run('rm -rf ~/Library/Caches/PyCharmCE*',
                       shell=True,
                       check=True)
        print('Launching GUI PyCharm to rebuild caches...', flush=True)
        process = subprocess.Popen(str(pycharmbin))

        # Wait a bit and ask it nicely to die.
        # We need to make sure it has enough time to do its cache updating
        # thing even if the system is fully under load.
        time.sleep(10 * 60)

        # Seems killing it via applescript is more likely to leave it
        # in a working state for offline inspections than TERM signal..
        subprocess.run(
            "osascript -e 'tell application \"PyCharm CE\" to quit'",
            shell=True,
            check=False)
        # process.terminate()
        print('Waiting for GUI PyCharm to quit...', flush=True)
        process.wait()

    _run_idea_inspections_cached(cachepath=cachepath,
                                 filenames=filenames,
                                 full=full,
                                 projroot=projroot,
                                 displayname='PyCharm',
                                 inspect=inspect,
                                 verbose=verbose)


def clioncode(projroot: Path, full: bool, verbose: bool) -> None:
    """Run clion inspections on all our code."""
    import time

    cachepath = Path('config/.cache-clioncode')
    filenames = get_code_filenames(projroot)
    clionroot = Path('/Applications/CLion.app')
    clionbin = Path(clionroot, 'Contents/MacOS/clion')
    inspect = Path(clionroot, 'Contents/bin/inspect.sh')

    # At the moment offline clion inspections seem a bit flaky.
    # They don't seem to run at all if we haven't opened the project
    # in the GUI, and it seems recent changes can get ignored for that
    # reason too.
    # So for now let's try blowing away caches, launching the gui
    # temporarily, and then kicking off inspections after that. Sigh.
    print('Clearing clion caches...', flush=True)
    subprocess.run('rm -rf ~/Library/Caches/CLion*', shell=True, check=True)

    # Note: I'm assuming this project needs to be open when the GUI
    # comes up. Currently just have one project so can rely on auto-open
    # but may need to get fancier later if that changes.
    print('Launching GUI CLion to rebuild caches...', flush=True)
    process = subprocess.Popen(str(clionbin))

    # Wait a moment and ask it nicely to die.
    time.sleep(120)

    # Seems killing it via applescript is more likely to leave it
    # in a working state for offline inspections than TERM signal..
    subprocess.run("osascript -e 'tell application \"CLion\" to quit'",
                   shell=True,
                   check=False)

    # process.terminate()
    print('Waiting for GUI CLion to quit...', flush=True)
    process.wait(timeout=60)

    print('Launching Offline CLion to run inspections...', flush=True)
    _run_idea_inspections_cached(
        cachepath=cachepath,
        filenames=filenames,
        full=full,
        projroot=Path(projroot, 'ballisticacore-cmake'),
        inspectdir=Path(projroot, 'ballisticacore-cmake/src/ballistica'),
        displayname='CLion',
        inspect=inspect,
        verbose=verbose)


def androidstudiocode(projroot: Path, full: bool, verbose: bool) -> None:
    """Run Android Studio inspections on all our code."""
    # import time

    cachepath = Path('config/.cache-androidstudiocode')
    filenames = get_code_filenames(projroot)
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
        projroot=Path(projroot, 'ballisticacore-android'),
        inspectdir=Path(
            projroot,
            'ballisticacore-android/BallisticaCore/src/main/cpp/src/ballistica'
        ),
        # inspectdir=None,
        displayname='Android Studio',
        inspect=inspect,
        verbose=verbose)
