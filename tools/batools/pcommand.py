# Released under the MIT License. See LICENSE for details.
#
"""Standard snippets that can be pulled into project pcommand scripts.

A snippet is a mini-program that directly takes input from stdin and does
some focused task. This module consists of ballistica-specific ones.
"""
from __future__ import annotations

# Note: import as little as possible here at the module level to
# keep launch times fast for small snippets.
import sys
from typing import TYPE_CHECKING

from efrotools.pcommand import PROJROOT

if TYPE_CHECKING:
    from typing import Optional, List, Set, Dict


def stage_server_file() -> None:
    """Stage files for the server environment with some filtering."""
    from efro.error import CleanError
    import batools.assetstaging
    if len(sys.argv) != 5:
        raise CleanError('Expected 3 args (mode, infile, outfile).')
    mode, infilename, outfilename = sys.argv[2], sys.argv[3], sys.argv[4]
    batools.assetstaging.stage_server_file(str(PROJROOT), mode, infilename,
                                           outfilename)


def py_examine() -> None:
    """Run a python examination at a given point in a given file."""
    import os
    from pathlib import Path
    import efrotools
    if len(sys.argv) != 7:
        print('ERROR: expected 7 args')
        sys.exit(255)
    filename = Path(sys.argv[2])
    line = int(sys.argv[3])
    column = int(sys.argv[4])
    selection: Optional[str] = (None if sys.argv[5] == '' else sys.argv[5])
    operation = sys.argv[6]

    # This stuff assumes it is being run from project root.
    os.chdir(PROJROOT)

    # Set up pypaths so our main distro stuff works.
    scriptsdir = os.path.abspath(
        os.path.join(os.path.dirname(sys.argv[0]),
                     '../assets/src/ba_data/python'))
    toolsdir = os.path.abspath(
        os.path.join(os.path.dirname(sys.argv[0]), '../tools'))
    if scriptsdir not in sys.path:
        sys.path.append(scriptsdir)
    if toolsdir not in sys.path:
        sys.path.append(toolsdir)
    efrotools.py_examine(PROJROOT, filename, line, column, selection,
                         operation)


def clean_orphaned_assets() -> None:
    """Remove asset files that are no longer part of the build."""
    import os
    import json
    import efrotools

    # Operate from dist root..
    os.chdir(PROJROOT)

    # Our manifest is split into 2 files (public and private)
    with open('assets/.asset_manifest_public.json') as infile:
        manifest = set(json.loads(infile.read()))
    with open('assets/.asset_manifest_private.json') as infile:
        manifest.update(set(json.loads(infile.read())))
    for root, _dirs, fnames in os.walk('assets/build'):
        for fname in fnames:
            fpath = os.path.join(root, fname)
            fpathrel = fpath[13:]  # paths are relative to assets/build
            if fpathrel not in manifest:
                print(f'Removing orphaned asset file: {fpath}')
                os.unlink(fpath)

    # Lastly, clear empty dirs.
    efrotools.run('find assets/build -depth -empty -type d -delete')


def fix_mac_ssh() -> None:
    """Turn off mac ssh password access.

    (This totally doesn't belong in this project btw..)
    """
    configpath = '/etc/ssh/sshd_config'
    with open(configpath) as infile:
        lines = infile.readlines()
    index = lines.index('#PasswordAuthentication yes\n')
    lines[index] = 'PasswordAuthentication no\n'
    index = lines.index('#ChallengeResponseAuthentication yes\n')
    lines[index] = 'ChallengeResponseAuthentication no\n'
    index = lines.index('UsePAM yes\n')
    lines[index] = 'UsePAM no\n'
    with open(configpath, 'w') as outfile:
        outfile.write(''.join(lines))
    print('SSH config updated successfully!')


def check_mac_ssh() -> None:
    """Make sure ssh password access is turned off.

    (This totally doesn't belong here, but I use it it to remind myself to
    fix mac ssh after system updates which blow away ssh customizations).
    """
    with open('/etc/ssh/sshd_config') as infile:
        lines = infile.read().splitlines()
    if ('UsePAM yes' in lines or '#PasswordAuthentication yes' in lines
            or '#ChallengeResponseAuthentication yes' in lines):
        print('ERROR: ssh config is allowing password access.\n'
              'To fix: sudo tools/pcommand fix_mac_ssh')
        sys.exit(255)
    print('password ssh auth seems disabled; hooray!')


def resize_image() -> None:
    """Resize an image and save it to a new location.

    args: xres, yres, src, dst
    """
    import os
    import efrotools
    if len(sys.argv) != 6:
        raise Exception('expected 5 args')
    width = int(sys.argv[2])
    height = int(sys.argv[3])
    src = sys.argv[4]
    dst = sys.argv[5]
    if not dst.endswith('.png'):
        raise RuntimeError(f'dst must be a png; got "{dst}"')
    if not src.endswith('.png'):
        raise RuntimeError(f'src must be a png; got "{src}"')
    print('Creating: ' + os.path.basename(dst), file=sys.stderr)
    efrotools.run(f'convert "{src}" -resize {width}x{height} "{dst}"')


def check_clean_safety() -> None:
    """Ensure all files are are added to git or in gitignore.

    Use to avoid losing work if we accidentally do a clean without
    adding something.
    """
    import os
    from efrotools.pcommand import check_clean_safety as std_snippet

    # First do standard checks.
    std_snippet()

    # Then also make sure there are no untracked changes to core files
    # (since we may be blowing core away here).
    spinoff_bin = os.path.join(str(PROJROOT), 'tools', 'spinoff')
    if os.path.exists(spinoff_bin):
        status = os.system(spinoff_bin + ' cleancheck')
        if status != 0:
            sys.exit(255)


def archive_old_builds() -> None:
    """Stuff our old public builds into the 'old' dir.

    (called after we push newer ones)
    """
    import batools.build
    if len(sys.argv) < 3:
        raise Exception('invalid arguments')
    ssh_server = sys.argv[2]
    builds_dir = sys.argv[3]
    ssh_args = sys.argv[4:]
    batools.build.archive_old_builds(ssh_server, builds_dir, ssh_args)


def lazy_increment_build() -> None:
    """Increment build number only if C++ sources have changed.

    This is convenient to place in automatic commit/push scripts.
    It could make sense to auto update build number when scripts/assets
    change too, but a build number change requires rebuilding all binaries
    so I'll leave that as an explicit choice to save work.
    """
    import os
    import subprocess
    from efro.terminal import Clr
    from efro.error import CleanError
    from efrotools import get_files_hash
    from efrotools.code import get_code_filenames
    if sys.argv[2:] not in [[], ['--update-hash-only']]:
        raise CleanError('Invalid arguments')
    update_hash_only = '--update-hash-only' in sys.argv
    codefiles = get_code_filenames(PROJROOT)
    codehash = get_files_hash(codefiles)
    hashfilename = '.cache/lazy_increment_build'
    try:
        with open(hashfilename) as infile:
            lasthash = infile.read()
    except FileNotFoundError:
        lasthash = ''
    if codehash != lasthash:
        print(f'{Clr.SMAG}Source(s) changed; incrementing build...{Clr.RST}')

        if not update_hash_only:
            # Just go ahead and bless; this will increment the build as needed.
            # subprocess.run(['make', 'bless'], check=True)
            subprocess.run(['tools/version_utils', 'incrementbuild'],
                           check=True)

        # We probably just changed code, so we need to re-calc the hash.
        codehash = get_files_hash(codefiles)
        os.makedirs(os.path.dirname(hashfilename), exist_ok=True)
        with open(hashfilename, 'w') as outfile:
            outfile.write(codehash)


def get_master_asset_src_dir() -> None:
    """Print master-asset-source dir for this repo."""
    import subprocess
    import os

    master_assets_dir = '/Users/ericf/Dropbox/ballisticacore_master_assets'
    dummy_dir = '/__DUMMY_MASTER_SRC_DISABLED_PATH__'

    # Only apply this on my setup
    if os.path.exists(master_assets_dir):

        # Ok, for now lets simply use our hard-coded master-src
        # path if we're on master in and not otherwise.  Should
        # probably make this configurable.
        output = subprocess.check_output(
            ['git', 'status', '--branch', '--porcelain']).decode()

        # Also compare repo name to split version of itself to
        # see if we're outside of core (filtering will cause mismatch if so).
        if ('origin/master' in output.splitlines()[0]
                and 'ballistica' + 'core' == 'ballisticacore'):

            # We seem to be in master in core repo; lets do it.
            print(master_assets_dir)
            return

    # Still need to supply dummy path for makefile if not..
    print(dummy_dir)


def androidaddr() -> None:
    """Return the source file location for an android program-counter.

    command line args: archive_dir architecture addr
    """
    import batools.android
    from efro.error import CleanError
    if len(sys.argv) != 5:
        raise CleanError(f'ERROR: expected 3 args; got {len(sys.argv) - 2}\n'
                         f'Usage: "tools/pcommand android_addr'
                         f' <ARCHIVE-PATH> <ARCH> <ADDR>"')
    archive_dir = sys.argv[2]
    arch = sys.argv[3]
    addr = sys.argv[4]
    batools.android.androidaddr(archive_dir=archive_dir, arch=arch, addr=addr)


def push_ipa() -> None:
    """Construct and push ios IPA for testing."""
    from pathlib import Path
    import efrotools.ios
    root = Path(sys.argv[0], '../..').resolve()
    if len(sys.argv) != 3:
        raise Exception('expected 1 arg (debug or release)')
    modename = sys.argv[2]
    efrotools.ios.push_ipa(root, modename)


def printcolors() -> None:
    """Print all colors available in efro.terminals.TerminalColor."""
    from efro.error import CleanError
    from efro.terminal import TerminalColor, Clr

    if Clr.RED == '':
        raise CleanError('Efro color terminal output is disabled.')

    clrnames = {getattr(Clr, s): s for s in dir(Clr) if s.isupper()}

    # Print everything in Clr (since that's what users should be using
    # but do it in the order of TerminalColor (since Clr is just a class
    # so is unordered)
    for value in TerminalColor:
        if value is TerminalColor.RESET:
            continue
        shortname = f'Clr.{clrnames[value.value]}'
        longname = f'({value.name})'
        print(f'{shortname:<12} {longname:<20} {value.value}'
              f'The quick brown fox jumps over the lazy dog.'
              f'{TerminalColor.RESET.value}')


def gen_fulltest_buildfile_android() -> None:
    """Generate fulltest command list for jenkins.

    (so we see nice pretty split-up build trees)
    """
    import batools.build
    batools.build.gen_fulltest_buildfile_android()


def gen_fulltest_buildfile_windows() -> None:
    """Generate fulltest command list for jenkins.

    (so we see nice pretty split-up build trees)
    """
    import batools.build
    batools.build.gen_fulltest_buildfile_windows()


def gen_fulltest_buildfile_apple() -> None:
    """Generate fulltest command list for jenkins.

    (so we see nice pretty split-up build trees)
    """
    import batools.build
    batools.build.gen_fulltest_buildfile_apple()


def gen_fulltest_buildfile_linux() -> None:
    """Generate fulltest command list for jenkins.

    (so we see nice pretty split-up build trees)
    """
    import batools.build
    batools.build.gen_fulltest_buildfile_linux()


def python_build_apple() -> None:
    """Build an embeddable python for mac/ios/tvos."""
    _python_build_apple(debug=False)


def python_build_apple_debug() -> None:
    """Build embeddable python for mac/ios/tvos (dbg ver)."""
    _python_build_apple(debug=True)


def _python_build_apple(debug: bool) -> None:
    """Build an embeddable python for macOS/iOS/tvOS."""
    import os
    from efrotools import pybuild
    os.chdir(PROJROOT)
    archs = ('mac', 'ios', 'tvos')
    if len(sys.argv) != 3:
        print('ERROR: expected one <ARCH> arg: ' + ', '.join(archs))
        sys.exit(255)
    arch = sys.argv[2]
    if arch not in archs:
        print('ERROR: invalid arch. valid values are: ' + ', '.join(archs))
        sys.exit(255)
    pybuild.build_apple(arch, debug=debug)


def python_build_android() -> None:
    """Build an embeddable Python lib for Android."""
    _python_build_android(debug=False)


def python_build_android_debug() -> None:
    """Build embeddable Android Python lib (debug ver)."""
    _python_build_android(debug=True)


def _python_build_android(debug: bool) -> None:
    import os
    from efrotools import pybuild
    os.chdir(PROJROOT)
    archs = ('arm', 'arm64', 'x86', 'x86_64')
    if len(sys.argv) != 3:
        print('ERROR: expected one <ARCH> arg: ' + ', '.join(archs))
        sys.exit(255)
    arch = sys.argv[2]
    if arch not in archs:
        print('ERROR: invalid arch. valid values are: ' + ', '.join(archs))
        sys.exit(255)
    pybuild.build_android(str(PROJROOT), arch, debug=debug)


def python_android_patch() -> None:
    """Patches Python to prep for building for Android."""
    import os
    from efrotools import pybuild
    os.chdir(sys.argv[2])
    pybuild.android_patch()


def python_gather() -> None:
    """Gather build python components into the project.

    This assumes all embeddable py builds have been run successfully.
    """
    import os
    from efrotools import pybuild
    os.chdir(PROJROOT)
    pybuild.gather()


def python_winprune() -> None:
    """Prune unneeded files from windows python."""
    import os
    from efrotools import pybuild
    os.chdir(PROJROOT)
    pybuild.winprune()


def capitalize() -> None:
    """Print args capitalized."""
    print(' '.join(w.capitalize() for w in sys.argv[2:]))


def efrocache_update() -> None:
    """Build & push files to efrocache for public access."""
    from efrotools.efrocache import update_cache
    makefile_dirs = ['', 'assets']
    update_cache(makefile_dirs)


def efrocache_get() -> None:
    """Get a file from efrocache."""
    from efrotools.efrocache import get_target
    if len(sys.argv) != 3:
        raise RuntimeError('Expected exactly 1 arg')
    get_target(sys.argv[2])


def get_modern_make() -> None:
    """Print name of a modern make command."""
    import platform
    import subprocess

    # Mac gnu make is outdated (due to newer versions using GPL3 I believe).
    # so let's return 'gmake' there which will point to homebrew make which
    # should be up to date.
    if platform.system() == 'Darwin':
        if subprocess.run(['which', 'gmake'], check=False,
                          capture_output=True).returncode != 0:
            print(
                'WARNING: this requires gmake (mac system make is too old).'
                " Install it with 'brew install make'",
                file=sys.stderr,
                flush=True)
        print('gmake')
    else:
        print('make')


def warm_start_asset_build() -> None:
    """Prep asset builds to run faster."""
    import os
    import subprocess
    from pathlib import Path
    from efrotools import getconfig
    public: bool = getconfig(PROJROOT)['public']

    if public:
        from efrotools.efrocache import warm_start_cache
        os.chdir(PROJROOT)
        warm_start_cache()
    else:
        # For internal builds we don't use efrocache but we do use an
        # internal build cache. Download an initial cache/etc. if need be.
        subprocess.run(
            [str(Path(PROJROOT, 'tools/convert_util')), '--init-asset-cache'],
            check=True)


def update_docs_md() -> None:
    """Updates docs markdown files if necessary."""
    import batools.build
    batools.build.update_docs_md(check='--check' in sys.argv)


def list_pip_reqs() -> None:
    """List Python Pip packages needed for this project."""
    from batools.build import get_pip_reqs
    print(' '.join(get_pip_reqs()))


def install_pip_reqs() -> None:
    """Install Python Pip packages needed for this project."""
    import subprocess
    from efrotools import PYTHON_BIN
    from efro.terminal import Clr
    from batools.build import get_pip_reqs
    subprocess.run([PYTHON_BIN, '-m', 'pip', 'install', '--upgrade'] +
                   get_pip_reqs(),
                   check=True)
    print(f'{Clr.GRN}All pip requirements installed!{Clr.RST}')


def checkenv() -> None:
    """Check for tools necessary to build and run the app."""
    import batools.build
    batools.build.checkenv()


def ensure_prefab_platform() -> None:
    """Ensure we are running on a particular prefab platform."""
    import batools.build
    from efro.error import CleanError
    if len(sys.argv) != 3:
        raise CleanError('Expected 1 platform name arg.')
    needed = sys.argv[2]
    current = batools.build.get_current_prefab_platform()
    if current != needed:
        raise CleanError(
            f'Incorrect platform: we are {current}, this requires {needed}.')


def prefab_run_var() -> None:
    """Print a var for running a prefab run for the current platform.

    We use this mechanism instead of just having a command recursively run
    a make target so that ctrl-c can be handled cleanly and directly by the
    command getting run instead of generating extra errors in the recursive
    processes.
    """
    import batools.build
    if len(sys.argv) != 3:
        raise RuntimeError('Expected 1 arg.')
    base = sys.argv[2].replace('-', '_').upper()
    platform = batools.build.get_current_prefab_platform().upper()
    print(f'RUN_PREFAB_{platform}_{base}', end='')


def make_prefab() -> None:
    """Run prefab builds for the current platform."""
    import subprocess
    import batools.build
    if len(sys.argv) != 3:
        raise RuntimeError('Expected one argument')
    target = batools.build.PrefabTarget(sys.argv[2])
    platform = batools.build.get_current_prefab_platform()

    # We use dashes instead of underscores in target names.
    platform = platform.replace('_', '-')
    try:
        subprocess.run(['make', f'prefab-{platform}-{target.value}-build'],
                       check=True)
    except (Exception, KeyboardInterrupt) as exc:
        if str(exc):
            print(f'make_prefab failed with error: {exc}')
        sys.exit(-1)


def update_makebob() -> None:
    """Build fresh make_bob binaries for all relevant platforms."""
    import batools.build
    batools.build.update_makebob()


def lazybuild() -> None:
    """Run a build command only if an input has changed."""
    import subprocess
    import batools.build
    from efro.error import CleanError
    if len(sys.argv) < 5:
        raise CleanError('Expected at least 3 args')
    try:
        category = batools.build.SourceCategory(sys.argv[2])
    except ValueError as exc:
        raise CleanError(exc) from exc
    target = sys.argv[3]
    command = ' '.join(sys.argv[4:])
    try:
        batools.build.lazybuild(target, category, command)
    except subprocess.CalledProcessError as exc:
        raise CleanError(exc) from exc


def android_archive_unstripped_libs() -> None:
    """Copy libs to a build archive."""
    import subprocess
    from pathlib import Path
    from efro.error import CleanError
    from efro.terminal import Clr
    if len(sys.argv) != 4:
        raise CleanError('Expected 2 args; src-dir and dst-dir')
    src = Path(sys.argv[2])
    dst = Path(sys.argv[3])
    if dst.exists():
        subprocess.run(['rm', '-rf', dst], check=True)
    dst.mkdir(parents=True, exist_ok=True)
    if not src.is_dir():
        raise CleanError(f"Source dir not found: '{src}'")
    libname = 'libmain'
    libext = '.so'
    for abi, abishort in [
        ('armeabi-v7a', 'arm'),
        ('arm64-v8a', 'arm64'),
        ('x86', 'x86'),
        ('x86_64', 'x86-64'),
    ]:
        srcpath = Path(src, abi, libname + libext)
        dstname = f'{libname}_{abishort}{libext}'
        dstpath = Path(dst, dstname)
        if srcpath.exists():
            print(f'Archiving unstripped library: {Clr.BLD}{dstname}{Clr.RST}')
            subprocess.run(['cp', srcpath, dstpath], check=True)
            subprocess.run(['tar', '-zcf', dstname + '.tgz', dstname],
                           cwd=dst,
                           check=True)
            subprocess.run(['rm', dstpath], check=True)


def _camel_case_split(string: str) -> List[str]:
    words = [[string[0]]]
    for char in string[1:]:
        if words[-1][-1].islower() and char.isupper():
            words.append(list(char))
        else:
            words[-1].append(char)
    return [''.join(word) for word in words]


def efro_gradle() -> None:
    """Calls ./gradlew with some extra magic."""
    import subprocess
    from efro.terminal import Clr
    from efrotools.android import filter_gradle_file
    args = ['./gradlew'] + sys.argv[2:]
    print(f'{Clr.BLU}Running gradle with args:{Clr.RST} {args}.', flush=True)
    enabled_tags: Set[str] = set()
    target_words = [w.lower() for w in _camel_case_split(args[-1])]
    if 'google' in target_words:
        enabled_tags = {'google', 'crashlytics'}

    buildfilename = 'BallisticaCore/build.gradle'

    # Move the original file out of the way and operate on a copy of it.
    subprocess.run(['mv', buildfilename, f'{buildfilename}.prev'], check=True)
    subprocess.run(['cp', f'{buildfilename}.prev', buildfilename], check=True)

    filter_gradle_file(buildfilename, enabled_tags)

    try:
        subprocess.run(args, check=True)
        errored = False
    except BaseException:
        errored = True

    # Restore the original.
    subprocess.run(['mv', f'{buildfilename}.prev', buildfilename], check=True)

    if errored:
        sys.exit(1)


def stage_assets() -> None:
    """Stage assets for a build."""
    from batools.assetstaging import main
    from efro.error import CleanError
    try:
        main(projroot=str(PROJROOT), args=sys.argv[2:])
    except CleanError as exc:
        exc.pretty_print()
        sys.exit(1)


def update_assets_makefile() -> None:
    """Update the assets makefile."""
    from batools.assetsmakefile import update_assets_makefile as uam
    check = ('--check' in sys.argv)
    uam(projroot=str(PROJROOT), check=check)


def update_project() -> None:
    """Update project files."""
    from batools.updateproject import Updater
    check = '--check' in sys.argv
    fix = '--fix' in sys.argv

    Updater(check=check, fix=fix).run()


def update_prefab_libs() -> None:
    """Update prefab internal libs for builds."""
    import subprocess
    import os
    from efro.error import CleanError
    import batools.build
    if len(sys.argv) != 5:
        raise CleanError('Expected 2 args (standard/server, debug/release)')
    buildtype = sys.argv[2]
    mode = sys.argv[3]
    builddir = sys.argv[4]
    if buildtype not in {'standard', 'server'}:
        raise CleanError(f'Invalid buildtype: {buildtype}')
    if mode not in {'debug', 'release'}:
        raise CleanError(f'Invalid mode: {mode}')
    platform = batools.build.get_current_prefab_platform()
    suffix = '_server' if buildtype == 'server' else ''
    target = (f'build/prefab/lib/{platform}{suffix}/{mode}/'
              f'libballisticacore_internal.a')

    # Build the target and then copy it to dst if it doesn't exist there yet
    # or the existing one is older than our target.
    subprocess.run(['make', target], check=True)

    # prefix = 'server-' if buildtype == 'server' else ''
    # suffix = '/dist' if buildtype == 'server' else ''
    # libdir = f'build/cmake/{prefix}{mode}{suffix}/prefablib'
    libdir = os.path.join(builddir, 'prefablib')
    libpath = os.path.join(libdir, 'libballisticacore_internal.a')

    update = True
    time1 = os.path.getmtime(target)
    if os.path.exists(libpath):
        time2 = os.path.getmtime(libpath)
        if time1 <= time2:
            update = False

    if update:
        if not os.path.exists(libdir):
            os.makedirs(libdir, exist_ok=True)
        subprocess.run(['cp', target, libdir], check=True)


def cmake_prep_dir() -> None:
    """Create a dir, recreating it when cmake/python/etc. version changes.

    Useful to prevent builds from breaking when cmake or other components
    are updated.
    """
    # pylint: disable=too-many-locals
    import os
    import subprocess
    import json
    from efro.error import CleanError
    from efro.terminal import Clr
    from efrotools import PYVER

    if len(sys.argv) != 3:
        raise CleanError('Expected 1 arg (dir name)')
    dirname = sys.argv[2]

    verfilename = os.path.join(dirname, '.ba_cmake_env')

    versions: Dict[str, str]
    if os.path.isfile(verfilename):
        with open(verfilename) as infile:
            versions = json.loads(infile.read())
            assert isinstance(versions, dict)
    else:
        versions = {}

    # Get version of installed cmake.
    cmake_ver_output = subprocess.run(['cmake', '--version'],
                                      check=True,
                                      capture_output=True).stdout.decode()
    cmake_ver = cmake_ver_output.splitlines()[0].split('cmake version ')[1]

    cmake_ver_existing = versions.get('cmake')
    assert isinstance(cmake_ver_existing, (str, type(None)))

    # Get specific version of our target python.
    python_ver_output = subprocess.run([f'python{PYVER}', '--version'],
                                       check=True,
                                       capture_output=True).stdout.decode()
    python_ver = python_ver_output.splitlines()[0].split('Python ')[1]

    python_ver_existing = versions.get('python')
    assert isinstance(python_ver_existing, (str, type(None)))

    # If they don't match, blow away the dir and write the current version.
    if cmake_ver_existing != cmake_ver or python_ver_existing != python_ver:
        if (cmake_ver_existing != cmake_ver
                and cmake_ver_existing is not None):
            print(f'{Clr.BLU}CMake version changed from {cmake_ver_existing}'
                  f' to {cmake_ver}; clearing existing build at'
                  f' "{dirname}".{Clr.RST}')
        if (python_ver_existing != python_ver
                and python_ver_existing is not None):
            print(f'{Clr.BLU}Python version changed from {python_ver_existing}'
                  f' to {python_ver}; clearing existing build at'
                  f' "{dirname}".{Clr.RST}')
        subprocess.run(['rm', '-rf', dirname], check=True)
        os.makedirs(dirname, exist_ok=True)
        with open(verfilename, 'w') as outfile:
            outfile.write(
                json.dumps({
                    'cmake': cmake_ver,
                    'python': python_ver
                }))
