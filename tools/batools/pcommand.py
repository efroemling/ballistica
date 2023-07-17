# Released under the MIT License. See LICENSE for details.
#
"""A nice collection of ready-to-use pcommands for this package."""
from __future__ import annotations

# Note: import as little as possible here at the module level to
# keep launch times fast for small snippets.
import sys

from efrotools.pcommand import PROJROOT


def prune_includes() -> None:
    """Check for unnecessary includes in C++ files."""
    from batools.pruneincludes import Pruner

    args = sys.argv.copy()[2:]
    commit = False
    if '--commit' in args:
        args.remove('--commit')
        commit = True

    Pruner(commit=commit, paths=args).run()
    print('Prune run complete!')


def resize_image() -> None:
    """Resize an image and save it to a new location.

    args: xres, yres, src, dst
    """
    import os
    import subprocess

    if len(sys.argv) != 6:
        raise RuntimeError('Expected 5 args.')
    width = int(sys.argv[2])
    height = int(sys.argv[3])
    src = sys.argv[4]
    dst = sys.argv[5]
    if not dst.endswith('.png'):
        raise RuntimeError(f'dst must be a png; got "{dst}"')
    if not src.endswith('.png'):
        raise RuntimeError(f'src must be a png; got "{src}"')
    print('Creating: ' + os.path.basename(dst), file=sys.stderr)
    subprocess.run(
        f'convert "{src}" -resize {width}x{height} "{dst}"',
        shell=True,
        check=True,
    )


def check_clean_safety() -> None:
    """Ensure all files are are added to git or in gitignore.

    Use to avoid losing work if we accidentally do a clean without
    adding something.
    """
    import os
    import subprocess

    from efro.terminal import Clr
    from efro.error import CleanError
    import efrotools.pcommand

    ignorevar = 'BA_IGNORE_CLEAN_SAFETY_CHECK'
    if os.environ.get(ignorevar) == '1':
        return
    try:
        # First do standard checks.
        efrotools.pcommand.check_clean_safety()

        # Then also make sure there are no untracked changes to core files
        # (since we may be blowing core away here).
        spinoff_bin = os.path.join(str(PROJROOT), 'tools', 'spinoff')
        if os.path.exists(spinoff_bin):
            result = subprocess.run(
                [spinoff_bin, 'cleancheck', '--soft'], check=False
            )
            if result.returncode != 0:
                raise CleanError()
    except Exception:
        print(
            f'{Clr.RED}Clean safety check failed.'
            f' Set {ignorevar}=1 to proceed anyway.{Clr.RST}'
        )
        raise


def archive_old_builds() -> None:
    """Stuff our old public builds into the 'old' dir.

    (called after we push newer ones)
    """
    import batools.build

    if len(sys.argv) < 3:
        raise RuntimeError('Invalid arguments.')
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
    codefiles = get_code_filenames(PROJROOT, include_generated=False)
    codehash = get_files_hash(codefiles)
    hashfilename = '.cache/lazy_increment_build'
    try:
        with open(hashfilename, encoding='utf-8') as infile:
            lasthash = infile.read()
    except FileNotFoundError:
        lasthash = ''
    if codehash != lasthash:
        if not update_hash_only:
            print(
                f'{Clr.SMAG}Source(s) changed; incrementing build...{Clr.RST}'
            )
            # Just go ahead and bless; this will increment the build as needed.
            # subprocess.run(['make', 'bless'], check=True)
            subprocess.run(
                ['tools/pcommand', 'version', 'incrementbuild'], check=True
            )

        # We probably just changed code, so we need to re-calc the hash.
        codehash = get_files_hash(codefiles)
        os.makedirs(os.path.dirname(hashfilename), exist_ok=True)
        with open(hashfilename, 'w', encoding='utf-8') as outfile:
            outfile.write(codehash)


def get_master_asset_src_dir() -> None:
    """Print master-asset-source dir for this repo."""
    import subprocess
    import os

    master_assets_dir = '/Users/ericf/Documents/ballisticakit_master_assets'
    dummy_dir = '/__DUMMY_MASTER_SRC_DISABLED_PATH__'

    # Only apply this on my primary setup.
    if os.path.exists(master_assets_dir) and os.path.exists('.git'):
        # Ok, for now lets simply use our hard-coded master-src
        # path if we're on master in and not otherwise.  Should
        # probably make this configurable.
        output = subprocess.check_output(
            ['git', 'status', '--branch', '--porcelain']
        ).decode()

        # Also compare repo name to split version of itself to
        # see if we're outside of core (filtering will cause mismatch if so).
        # pylint: disable=useless-suppression
        # pylint: disable=simplifiable-condition
        # pylint: disable=condition-evals-to-constant
        if (
            'origin/master' in output.splitlines()[0]
            and 'ballistica' + 'kit' == 'ballisticakit'
        ):
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
        raise CleanError(
            f'ERROR: expected 3 args; got {len(sys.argv) - 2}\n'
            f'Usage: "tools/pcommand android_addr'
            f' <ARCHIVE-PATH> <ARCH> <ADDR>"'
        )
    archive_dir = sys.argv[2]
    arch = sys.argv[3]
    addr = sys.argv[4]
    batools.android.androidaddr(archive_dir=archive_dir, arch=arch, addr=addr)


def push_ipa() -> None:
    """Construct and push ios IPA for testing."""

    from efrotools import extract_arg
    import efrotools.ios

    args = sys.argv[2:]
    signing_config = extract_arg(args, '--signing-config')

    if len(args) != 1:
        raise RuntimeError('Expected 1 mode arg (debug or release).')
    modename = args[0].lower()
    efrotools.ios.push_ipa(PROJROOT, modename, signing_config=signing_config)


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
        print(
            f'{shortname:<12} {longname:<20} {value.value}'
            f'The quick brown fox jumps over the lazy dog.'
            f'{TerminalColor.RESET.value}'
        )


def python_version_android_base() -> None:
    """Print built Python base version."""
    from efrotools.pybuild import PY_VER_ANDROID

    print(PY_VER_ANDROID, end='')


def python_version_android() -> None:
    """Print Android embedded Python version."""
    from efrotools.pybuild import PY_VER_EXACT_ANDROID

    print(PY_VER_EXACT_ANDROID, end='')


def python_version_apple() -> None:
    """Print Apple embedded Python version."""
    from efrotools.pybuild import PY_VER_EXACT_APPLE

    print(PY_VER_EXACT_APPLE, end='')


def python_build_apple() -> None:
    """Build an embeddable python for mac/ios/tvos."""
    _python_build_apple(debug=False)


def python_build_apple_debug() -> None:
    """Build embeddable python for mac/ios/tvos (dbg ver)."""
    _python_build_apple(debug=True)


def _python_build_apple(debug: bool) -> None:
    """Build an embeddable python for macOS/iOS/tvOS."""
    import os
    from efro.error import CleanError
    from efrotools import pybuild

    os.chdir(PROJROOT)
    archs = ('mac', 'ios', 'tvos')
    if len(sys.argv) != 3:
        raise CleanError('Error: expected one <ARCH> arg: ' + ', '.join(archs))
    arch = sys.argv[2]
    if arch not in archs:
        raise CleanError(
            'Error: invalid arch. valid values are: ' + ', '.join(archs)
        )
    pybuild.build_apple(arch, debug=debug)


def python_build_android() -> None:
    """Build an embeddable Python lib for Android."""
    _python_build_android(debug=False)


def python_build_android_debug() -> None:
    """Build embeddable Android Python lib (debug ver)."""
    _python_build_android(debug=True)


def _python_build_android(debug: bool) -> None:
    import os
    from efro.error import CleanError
    from efrotools import pybuild

    os.chdir(PROJROOT)
    archs = ('arm', 'arm64', 'x86', 'x86_64')
    if len(sys.argv) != 3:
        raise CleanError('Error: Expected one <ARCH> arg: ' + ', '.join(archs))
    arch = sys.argv[2]
    if arch not in archs:
        raise CleanError(
            'Error: invalid arch. valid values are: ' + ', '.join(archs)
        )
    pybuild.build_android(str(PROJROOT), arch, debug=debug)


def python_android_patch() -> None:
    """Patches Python to prep for building for Android."""
    import os
    from efrotools import pybuild

    os.chdir(sys.argv[2])
    pybuild.android_patch()


def python_android_patch_ssl() -> None:
    """Patches Python ssl to prep for building for Android."""
    from efrotools import pybuild

    pybuild.android_patch_ssl()


def python_apple_patch() -> None:
    """Patches Python to prep for building for Apple platforms."""
    from efro.error import CleanError
    from efrotools import pybuild

    if len(sys.argv) != 3:
        raise CleanError('Expected 1 arg.')

    pydir: str = sys.argv[2]
    pybuild.apple_patch(pydir)
    # arch = sys.argv[2]
    # slc = sys.argv[3]
    # assert slc
    # assert ' ' not in slc
    # pybuild.apple_patch(arch, slc)


def python_gather() -> None:
    """Gather build python components into the project.

    This assumes all embeddable py builds have been run successfully.
    """
    import os
    from efrotools import pybuild

    os.chdir(PROJROOT)
    pybuild.gather(do_android=True, do_apple=True)


def python_gather_android() -> None:
    """python_gather but only android bits."""
    import os
    from efrotools import pybuild

    os.chdir(PROJROOT)
    pybuild.gather(do_android=True, do_apple=False)


def python_gather_apple() -> None:
    """python_gather but only apple bits."""
    import os
    from efrotools import pybuild

    os.chdir(PROJROOT)
    pybuild.gather(do_android=False, do_apple=True)


def python_winprune() -> None:
    """Prune unneeded files from windows python."""
    import os
    from efrotools import pybuild

    os.chdir(PROJROOT)
    pybuild.winprune()


def capitalize() -> None:
    """Print args capitalized."""
    print(' '.join(w.capitalize() for w in sys.argv[2:]), end='')


def upper() -> None:
    """Print args uppercased."""
    print(' '.join(w.upper() for w in sys.argv[2:]), end='')


def efrocache_update() -> None:
    """Build & push files to efrocache for public access."""
    from efrotools.efrocache import update_cache

    makefile_dirs = ['', 'src/assets', 'src/resources', 'src/meta']
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
        if (
            subprocess.run(
                ['which', 'gmake'], check=False, capture_output=True
            ).returncode
            != 0
        ):
            print(
                'WARNING: this requires gmake (mac system make is too old).'
                " Install it with 'brew install make'",
                file=sys.stderr,
                flush=True,
            )
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
            [
                str(Path(PROJROOT, 'tools/pcommand')),
                'convert_util',
                '--init-asset-cache',
            ],
            check=True,
        )


def gen_docs_pdoc() -> None:
    """Generate pdoc documentation."""
    from efro.terminal import Clr
    import batools.docs

    print(f'{Clr.BLU}Generating documentation...{Clr.RST}')
    batools.docs.generate_pdoc(projroot=str(PROJROOT))


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

    # Make sure pip itself is up to date first.
    subprocess.run(
        [PYTHON_BIN, '-m', 'pip', 'install', '--upgrade', 'pip'], check=True
    )

    subprocess.run(
        [PYTHON_BIN, '-m', 'pip', 'install', '--upgrade'] + get_pip_reqs(),
        check=True,
    )
    print(f'{Clr.GRN}All pip requirements installed!{Clr.RST}')


def checkenv() -> None:
    """Check for tools necessary to build and run the app."""
    import batools.build

    batools.build.checkenv()


def wsl_build_check_win_drive() -> None:
    """Make sure we're building on a windows drive."""
    import os
    import subprocess
    import textwrap
    from efro.error import CleanError

    if (
        subprocess.run(
            ['which', 'wslpath'], check=False, capture_output=True
        ).returncode
        != 0
    ):
        raise CleanError(
            'wslpath not found; you must run this from a WSL environment'
        )

    if os.environ.get('WSL_BUILD_CHECK_WIN_DRIVE_IGNORE') == '1':
        return

    # Get a windows path to the current dir.
    path = (
        subprocess.run(
            ['wslpath', '-w', '-a', os.getcwd()],
            capture_output=True,
            check=True,
        )
        .stdout.decode()
        .strip()
    )

    # If we're sitting under the linux filesystem, our path
    # will start with \\wsl$; fail in that case and explain why.
    if not path.startswith('\\\\wsl$'):
        return

    def _wrap(txt: str) -> str:
        return textwrap.fill(txt, 76)

    raise CleanError(
        '\n\n'.join(
            [
                _wrap(
                    'ERROR: This project appears to live'
                    ' on the Linux filesystem.'
                ),
                _wrap(
                    'Visual Studio compiles will error here for reasons related'
                    ' to Linux filesystem case-sensitivity, and thus are'
                    ' disallowed.'
                    ' Clone the repo to a location that maps to a native'
                    ' Windows drive such as \'/mnt/c/ballistica\''
                    ' and try again.'
                ),
                _wrap(
                    'Note that WSL2 filesystem performance'
                    ' is poor when accessing'
                    ' native Windows drives, so if Visual Studio builds are not'
                    ' needed it may be best to keep things'
                    ' on the Linux filesystem.'
                    ' This behavior may differ under WSL1 (untested).'
                ),
                _wrap(
                    'Set env-var WSL_BUILD_CHECK_WIN_DRIVE_IGNORE=1 to skip'
                    ' this check.'
                ),
            ]
        )
    )


def wsl_path_to_win() -> None:
    """Forward escape slashes in a provided win path arg."""
    import subprocess
    import logging
    import os
    from efro.error import CleanError

    try:
        create = False
        escape = False
        if len(sys.argv) < 3:
            raise CleanError('Expected at least 1 path arg.')
        wsl_path: str | None = None
        for arg in sys.argv[2:]:
            if arg == '--create':
                create = True
            elif arg == '--escape':
                escape = True
            else:
                if wsl_path is not None:
                    raise CleanError('More than one path provided.')
                wsl_path = arg
        if wsl_path is None:
            raise CleanError('No path provided.')

        # wslpath fails on nonexistent paths; make it clear when that happens.
        if create:
            os.makedirs(wsl_path, exist_ok=True)
        if not os.path.exists(wsl_path):
            raise CleanError(f'Path \'{wsl_path}\' does not exist.')

        results = subprocess.run(
            ['wslpath', '-w', '-a', wsl_path], capture_output=True, check=True
        )
    except Exception:
        # This gets used in a makefile so our returncode is ignored;
        # let's try to make our failure known in other ways.
        logging.exception('wsl_to_escaped_win_path failed.')
        print('wsl_to_escaped_win_path_error_occurred', end='')
        return

    out = results.stdout.decode().strip()

    # If our input ended with a slash, match in the output.
    if wsl_path.endswith('/') and not out.endswith('\\'):
        out += '\\'

    if escape:
        out = out.replace('\\', '\\\\')
    print(out, end='')


def ensure_prefab_platform() -> None:
    """Ensure we are running on a particular prefab platform.

    Note that prefab platform may not exactly match hardware/os.
    For example, when running in Linux under a WSL environment,
    the prefab platform may be Windows; not Linux. Also, a 64-bit
    os may be targeting a 32-bit platform.
    """
    import batools.build
    from efro.error import CleanError

    if len(sys.argv) != 3:
        raise CleanError('Expected 1 platform name arg.')
    needed = sys.argv[2]
    current = batools.build.get_current_prefab_platform()
    if current != needed:
        raise CleanError(
            f'Incorrect platform: we are {current}, this requires {needed}.'
        )


def prefab_run_var() -> None:
    """Print the current platform prefab run target var."""
    import batools.build

    if len(sys.argv) != 3:
        raise RuntimeError('Expected 1 arg.')
    base = sys.argv[2].replace('-', '_').upper()
    platform = batools.build.get_current_prefab_platform().upper()
    print(f'RUN_PREFAB_{platform}_{base}', end='')


def prefab_binary_path() -> None:
    """Print the current platform prefab binary path."""
    import batools.build

    if len(sys.argv) != 3:
        raise RuntimeError('Expected 1 arg.')
    buildtype, buildmode = sys.argv[2].split('-')
    platform = batools.build.get_current_prefab_platform()
    if buildtype == 'gui':
        binpath = 'ballisticakit'
    elif buildtype == 'server':
        binpath = 'dist/ballisticakit_headless'
    else:
        raise ValueError(f"Invalid buildtype '{buildtype}'.")
    print(
        f'build/prefab/full/{platform}_{buildtype}/{buildmode}/{binpath}',
        end='',
    )


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
        subprocess.run(
            ['make', f'prefab-{platform}-{target.value}-build'], check=True
        )
    except (Exception, KeyboardInterrupt) as exc:
        if str(exc):
            print(f'make_prefab failed with error: {exc}')
        sys.exit(-1)


def lazybuild() -> None:
    """Run a build command only if an input has changed."""
    import subprocess
    import batools.build
    from efro.error import CleanError

    if len(sys.argv) < 5:
        raise CleanError('Expected at least 3 args')
    try:
        category = batools.build.LazyBuildCategory(sys.argv[2])
    except ValueError as exc:
        raise CleanError(exc) from exc
    target = sys.argv[3]
    command = ' '.join(sys.argv[4:])
    try:
        batools.build.lazybuild(target, category, command)
    except subprocess.CalledProcessError as exc:
        raise CleanError(exc) from exc


def logcat() -> None:
    """Get logcat command for filtering."""
    import subprocess
    from efro.terminal import Clr
    from efro.error import CleanError

    if len(sys.argv) != 4:
        raise CleanError('Expected 2 args')
    adb = sys.argv[2]
    plat = sys.argv[3]
    print('plat is', plat)

    # My amazon tablet chokes on the color format.
    if plat == 'amazon':
        format_args = ''
    else:
        format_args = '-v color '
    cmd = (
        f'{adb} logcat {format_args}SDL:V BallisticaKit:V VrLib:V'
        ' VrApi:V VrApp:V TimeWarp:V EyeBuf:V GlUtils:V DirectRender:V'
        ' HmdInfo:V IabHelper:V CrashAnrDetector:V DEBUG:V \'*:S\''
    )
    print(f'{Clr.BLU}Running logcat command: {Clr.BLD}{cmd}{Clr.RST}')
    subprocess.run(cmd, shell=True, check=True)


def _camel_case_split(string: str) -> list[str]:
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
    enabled_tags: set[str] = {'true'}
    target_words = [w.lower() for w in _camel_case_split(args[-1])]
    if 'google' in target_words:
        enabled_tags = {'google', 'crashlytics'}
    prev_suffix = 'efro_gradle_prev'

    buildfilename = 'BallisticaKit/build.gradle'

    # Move the original file out of the way and operate on a copy of it.
    subprocess.run(
        ['mv', buildfilename, f'{buildfilename}.{prev_suffix}'], check=True
    )
    subprocess.run(
        ['cp', f'{buildfilename}.{prev_suffix}', buildfilename], check=True
    )

    filter_gradle_file(buildfilename, enabled_tags)

    try:
        subprocess.run(args, check=True)
        errored = False
    except BaseException:
        errored = True

    # Restore the original.
    subprocess.run(
        ['mv', f'{buildfilename}.{prev_suffix}', buildfilename], check=True
    )

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


def update_project() -> None:
    """Update project files.

    This command is in charge of generating Makefiles, IDE project files,
    etc. based on the current structure of the project.
    It can also perform sanity checks or cleanup tasks.

    Updating should be explicitly run by the user through commands such as
    'make update', 'make check' or 'make preflight'. Other make targets should
    avoid running this command as it can modify the project structure
    arbitrarily which is not a good idea in the middle of a build.

    If this command is invoked with a --check argument, it should not modify
    any files but instead fail if any modifications *would* have been made.
    (used in CI builds to make sure things are kosher).
    """
    import os
    from batools.project import ProjectUpdater

    check = '--check' in sys.argv
    fix = '--fix' in sys.argv

    # ProjectUpdater is supposed to work from any dir, so let's keep
    # ourself honest by forcing the issue.
    cwd = os.getcwd()
    os.chdir('/')

    ProjectUpdater(cwd, check=check, fix=fix).run()


def cmake_prep_dir() -> None:
    """Create dir & recreate when cmake/python/etc. version changes.

    Useful to prevent builds from breaking when cmake or other components
    are updated.
    """
    import os
    from efro.error import CleanError
    import batools.build

    if len(sys.argv) != 3:
        raise CleanError('Expected 1 arg (dir name)')
    dirname = sys.argv[2]
    batools.build.cmake_prep_dir(
        dirname, verbose=os.environ.get('VERBOSE') == '1'
    )


def gen_binding_code() -> None:
    """Generate a binding_foo.inc file."""
    from efro.error import CleanError
    import batools.metabuild

    if len(sys.argv) != 4:
        raise CleanError('Expected 2 args (srcfile, dstfile)')
    inpath = sys.argv[2]
    outpath = sys.argv[3]
    batools.metabuild.gen_binding_code(str(PROJROOT), inpath, outpath)


def gen_flat_data_code() -> None:
    """Generate a C++ include file from a Python file."""
    from efro.error import CleanError
    import batools.metabuild

    if len(sys.argv) != 5:
        raise CleanError('Expected 3 args (srcfile, dstfile, varname)')
    inpath = sys.argv[2]
    outpath = sys.argv[3]
    varname = sys.argv[4]
    batools.metabuild.gen_flat_data_code(
        str(PROJROOT), inpath, outpath, varname
    )


def genchangelog() -> None:
    """Gen a pretty html changelog."""
    from batools.changelog import generate

    generate(projroot=str(PROJROOT))


def android_sdk_utils() -> None:
    """Wrangle android sdk stuff."""
    from batools.androidsdkutils import run

    run(projroot=str(PROJROOT), args=sys.argv[2:])


def gen_python_enums_module() -> None:
    """Update our procedurally generated python enums."""
    from batools.pythonenumsmodule import generate

    if len(sys.argv) != 4:
        raise RuntimeError('Expected infile and outfile args.')
    generate(
        projroot=str(PROJROOT), infilename=sys.argv[2], outfilename=sys.argv[3]
    )


def gen_dummy_modules() -> None:
    """Generate all dummy modules."""
    from efro.error import CleanError
    from batools.dummymodule import generate_dummy_modules

    if len(sys.argv) != 2:
        raise CleanError(f'Expected no args; got {len(sys.argv)-2}.')

    generate_dummy_modules(projroot=str(PROJROOT))


def version() -> None:
    """Check app versions."""
    from batools.version import run

    run(projroot=str(PROJROOT), args=sys.argv[2:])
