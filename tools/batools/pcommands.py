# Released under the MIT License. See LICENSE for details.
#
"""A nice collection of ready-to-use pcommands for this package."""
from __future__ import annotations

# Note: import as little as possible here at the module level to
# keep launch times fast for small snippets.
import sys

from efrotools import pcommand

# pylint: disable=too-many-lines


def prune_includes() -> None:
    """Check for unnecessary includes in C++ files.

    Pass --commit to actually modify files.
    """
    from batools.pruneincludes import Pruner

    pcommand.disallow_in_batch()

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

    pcommand.disallow_in_batch()

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

    import efrotools.pcommands

    pcommand.disallow_in_batch()

    ignorevar = 'BA_IGNORE_CLEAN_SAFETY_CHECK'
    if os.environ.get(ignorevar) == '1':
        return
    try:
        # First do standard checks.
        efrotools.pcommands.check_clean_safety()

        # Then also make sure there are no untracked changes to core files
        # (since we may be blowing core away here).
        spinoff_bin = os.path.join(str(pcommand.PROJROOT), 'tools', 'spinoff')
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

    pcommand.disallow_in_batch()

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
    from efrotools.util import get_files_hash
    from efrotools.code import get_code_filenames

    pcommand.disallow_in_batch()

    if sys.argv[2:] not in [[], ['--update-hash-only']]:
        raise CleanError('Invalid arguments')
    update_hash_only = '--update-hash-only' in sys.argv
    codefiles = get_code_filenames(pcommand.PROJROOT, include_generated=False)
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

    pcommand.disallow_in_batch()

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

    pcommand.disallow_in_batch()

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

    from efro.util import extract_arg
    import efrotools.ios

    pcommand.disallow_in_batch()

    args = sys.argv[2:]
    signing_config = extract_arg(args, '--signing-config')

    if len(args) != 1:
        raise RuntimeError('Expected 1 mode arg (debug or release).')
    modename = args[0].lower()
    efrotools.ios.push_ipa(
        pcommand.PROJROOT, modename, signing_config=signing_config
    )


def printcolors() -> None:
    """Print all colors available in efro.terminals.TerminalColor."""
    from efro.error import CleanError
    from efro.terminal import TerminalColor, Clr

    pcommand.disallow_in_batch()

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

    pcommand.disallow_in_batch()

    print(PY_VER_ANDROID, end='')


def python_version_android() -> None:
    """Print Android embedded Python version."""
    from efrotools.pybuild import PY_VER_EXACT_ANDROID

    pcommand.disallow_in_batch()

    print(PY_VER_EXACT_ANDROID, end='')


def python_version_apple() -> None:
    """Print Apple embedded Python version."""
    from efrotools.pybuild import PY_VER_EXACT_APPLE

    pcommand.disallow_in_batch()

    print(PY_VER_EXACT_APPLE, end='')


def python_build_apple() -> None:
    """Build an embeddable python for mac/ios/tvos."""

    pcommand.disallow_in_batch()

    _python_build_apple(debug=False)


def python_build_apple_debug() -> None:
    """Build embeddable python for mac/ios/tvos (dbg ver)."""

    pcommand.disallow_in_batch()

    _python_build_apple(debug=True)


def _python_build_apple(debug: bool) -> None:
    """Build an embeddable python for macOS/iOS/tvOS."""
    import os
    from efro.error import CleanError
    from efrotools import pybuild

    pcommand.disallow_in_batch()

    os.chdir(pcommand.PROJROOT)
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

    pcommand.disallow_in_batch()

    _python_build_android(debug=False)


def python_build_android_debug() -> None:
    """Build embeddable Android Python lib (debug ver)."""

    pcommand.disallow_in_batch()

    _python_build_android(debug=True)


def _python_build_android(debug: bool) -> None:
    import os
    from efro.error import CleanError
    from efrotools import pybuild

    pcommand.disallow_in_batch()

    os.chdir(pcommand.PROJROOT)
    archs = ('arm', 'arm64', 'x86', 'x86_64')
    if len(sys.argv) != 3:
        raise CleanError('Error: Expected one <ARCH> arg: ' + ', '.join(archs))
    arch = sys.argv[2]
    if arch not in archs:
        raise CleanError(
            'Error: invalid arch. valid values are: ' + ', '.join(archs)
        )
    pybuild.build_android(str(pcommand.PROJROOT), arch, debug=debug)


def python_android_patch() -> None:
    """Patches Python to prep for building for Android."""
    import os
    from efrotools import pybuild

    pcommand.disallow_in_batch()

    os.chdir(sys.argv[2])
    pybuild.android_patch()


def python_android_patch_ssl() -> None:
    """Patches Python ssl to prep for building for Android."""
    from efrotools import pybuild

    pcommand.disallow_in_batch()

    pybuild.android_patch_ssl()


def python_apple_patch() -> None:
    """Patches Python to prep for building for Apple platforms."""
    from efro.error import CleanError
    from efrotools import pybuild

    pcommand.disallow_in_batch()

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

    pcommand.disallow_in_batch()

    os.chdir(pcommand.PROJROOT)
    pybuild.gather(do_android=True, do_apple=True)


def python_gather_android() -> None:
    """python_gather but only android bits."""
    import os
    from efrotools import pybuild

    pcommand.disallow_in_batch()

    os.chdir(pcommand.PROJROOT)
    pybuild.gather(do_android=True, do_apple=False)


def python_gather_apple() -> None:
    """python_gather but only apple bits."""
    import os
    from efrotools import pybuild

    pcommand.disallow_in_batch()

    os.chdir(pcommand.PROJROOT)
    pybuild.gather(do_android=False, do_apple=True)


def python_winprune() -> None:
    """Prune unneeded files from windows python."""
    import os
    from efrotools import pybuild

    pcommand.disallow_in_batch()

    os.chdir(pcommand.PROJROOT)
    pybuild.winprune()


def capitalize() -> None:
    """Print args capitalized."""

    pcommand.disallow_in_batch()

    print(' '.join(w.capitalize() for w in sys.argv[2:]), end='')


def upper() -> None:
    """Print args uppercased."""

    pcommand.clientprint(
        ' '.join(w.upper() for w in pcommand.get_args()), end=''
    )


def efrocache_update() -> None:
    """Build & push files to efrocache for public access."""
    from efrotools.efrocache import update_cache

    pcommand.disallow_in_batch()

    makefile_dirs = ['', 'src/assets', 'src/resources', 'src/meta']
    update_cache(makefile_dirs)


def efrocache_get() -> None:
    """Get a file from efrocache."""
    from efrotools.efrocache import get_target

    args = pcommand.get_args()
    if len(args) != 1:
        raise RuntimeError('Expected exactly 1 arg')

    output = get_target(args[0], batch=pcommand.is_batch(), clr=pcommand.clr())
    if pcommand.is_batch():
        pcommand.clientprint(output)


def warm_start_asset_build() -> None:
    """Prep asset builds to run faster."""
    import os
    import subprocess
    from pathlib import Path

    from efrotools.project import getprojectconfig
    from efro.error import CleanError

    pcommand.disallow_in_batch()

    args = pcommand.get_args()
    if len(args) != 1:
        raise CleanError('Expected a single "gui" or "server" arg.')
    cachetype = args[0]

    public: bool = getprojectconfig(pcommand.PROJROOT)['public']

    if public:
        from efrotools.efrocache import warm_start_cache

        os.chdir(pcommand.PROJROOT)
        warm_start_cache(cachetype)
    else:
        # For internal builds we don't use efrocache but we do use an
        # internal build cache. Download an initial cache/etc. if need be.
        subprocess.run(
            [
                str(Path(pcommand.PROJROOT, 'tools/pcommand')),
                'convert_util',
                '--init-asset-cache',
            ],
            check=True,
        )


def gen_docs_sphinx() -> None:
    """Generate sphinx documentation."""
    import batools.docs

    batools.docs.generate_sphinx_docs()


def checkenv() -> None:
    """Check for tools necessary to build and run the app."""
    import batools.build

    pcommand.disallow_in_batch()

    batools.build.checkenv()


def prefab_platform() -> None:
    """Print the current prefab-platform value."""
    from efro.error import CleanError

    from batools.build import PrefabPlatform

    # Platform determination uses env vars; won't work in batch.
    pcommand.disallow_in_batch()

    args = pcommand.get_args()
    if len(args) != 0:
        raise CleanError('No arguments expected.')

    current = PrefabPlatform.get_current()

    print(current.value, end='')


def ensure_prefab_platform() -> None:
    """Ensure we are running on a particular prefab platform.

    Note that prefab platform may not exactly match hardware/os.
    For example, when running in Linux under a WSL environment,
    the prefab platform may be Windows; not Linux. Also, a 64-bit
    os may be targeting a 32-bit platform.
    """
    from efro.error import CleanError

    from batools.build import PrefabPlatform

    # Platform determination uses env vars; won't work in batch.
    pcommand.disallow_in_batch()

    args = pcommand.get_args()
    if len(args) != 1:
        options = ', '.join(t.value for t in PrefabPlatform)
        raise CleanError(
            f'Expected 1 PrefabPlatform arg. Options are {options}.'
        )
    needed = PrefabPlatform(args[0])
    current = PrefabPlatform.get_current()
    if current is not needed:
        raise CleanError(
            f'Incorrect platform: we are {current.value},'
            f' this requires {needed.value}.'
        )


def prefab_run_var() -> None:
    """Print the current platform prefab run target var."""
    from batools.build import PrefabPlatform

    # Platform determination uses env vars; won't work in batch.
    pcommand.disallow_in_batch()

    args = pcommand.get_args()
    if len(args) != 1:
        raise RuntimeError('Expected 1 arg.')
    base = args[0].replace('-', '_').upper()
    platform = PrefabPlatform.get_current().value.upper()
    pcommand.clientprint(f'RUN_PREFAB_{platform}_{base}', end='')


def prefab_binary_path() -> None:
    """Print the path to the current prefab binary."""
    from typing import assert_never

    from efro.error import CleanError

    from batools.build import PrefabPlatform, PrefabTarget

    # Platform determination uses env vars; won't work in batch.
    pcommand.disallow_in_batch()

    if len(sys.argv) != 3:
        options = ', '.join(t.value for t in PrefabTarget)
        raise CleanError(f'Expected 1 PrefabTarget arg. Options are {options}.')

    target = PrefabTarget(sys.argv[2])

    buildtype = target.buildtype
    buildmode = target.buildmode

    platform = PrefabPlatform.get_current()

    binpath = None

    if (
        platform is PrefabPlatform.WINDOWS_X86
        or platform is PrefabPlatform.WINDOWS_X86_64
    ):
        if buildtype == 'gui':
            binpath = 'BallisticaKit.exe'
        elif buildtype == 'server':
            binpath = 'dist/BallisticaKitHeadless.exe'
        else:
            raise ValueError(f"Invalid buildtype '{buildtype}'.")
    elif (
        platform is PrefabPlatform.MAC_ARM64
        or platform is PrefabPlatform.MAC_X86_64
        or platform is PrefabPlatform.LINUX_ARM64
        or platform is PrefabPlatform.LINUX_X86_64
    ):
        if buildtype == 'gui':
            binpath = 'ballisticakit'
        elif buildtype == 'server':
            binpath = 'dist/ballisticakit_headless'
        else:
            raise ValueError(f"Invalid buildtype '{buildtype}'.")
    else:
        # Make sure we're covering all options.
        assert_never(platform)

    assert binpath is not None
    print(
        f'build/prefab/full/{platform.value}_{buildtype}/{buildmode}/{binpath}',
        end='',
    )


def compose_docker_gui_release() -> None:
    """Build the docker image with bombsquad cmake gui."""
    import batools.docker

    batools.docker.docker_compose(headless_build=False)


def compose_docker_gui_debug() -> None:
    """Build the docker image with bombsquad debug cmake gui."""
    import batools.docker

    batools.docker.docker_compose(headless_build=False, build_type='Debug')


def compose_docker_server_release() -> None:
    """Build the docker image with bombsquad cmake server."""
    import batools.docker

    batools.docker.docker_compose()


def compose_docker_server_debug() -> None:
    """Build the docker image with bombsquad debug cmake server."""
    import batools.docker

    batools.docker.docker_compose(build_type='Debug')


def compose_docker_arm64_gui_release() -> None:
    """Build the docker image with bombsquad cmake for arm64."""
    import batools.docker

    batools.docker.docker_compose(headless_build=False, platform='linux/arm64')


def compose_docker_arm64_gui_debug() -> None:
    """Build the docker image with bombsquad cmake for arm64."""
    import batools.docker

    batools.docker.docker_compose(
        headless_build=False, platform='linux/arm64', build_type='Debug'
    )


def compose_docker_arm64_server_release() -> None:
    """Build the docker image with bombsquad cmake server for arm64."""
    import batools.docker

    batools.docker.docker_compose(platform='linux/arm64')


def compose_docker_arm64_server_debug() -> None:
    """Build the docker image with bombsquad cmake server for arm64."""
    import batools.docker

    batools.docker.docker_compose(platform='linux/arm64', build_type='Debug')


def save_docker_images() -> None:
    """Saves bombsquad images loaded into docker."""
    import batools.docker

    batools.docker.docker_save_images()


def remove_docker_images() -> None:
    """Remove the bombsquad images loaded in docker."""
    import batools.docker

    batools.docker.docker_remove_images()


def make_prefab() -> None:
    """Run prefab builds for the current platform."""
    import subprocess
    from batools.build import PrefabPlatform, PrefabTarget

    # Platform determination uses env vars; won't work in batch.
    pcommand.disallow_in_batch()

    if len(sys.argv) != 3:
        raise RuntimeError('Expected one argument')

    targetstr = PrefabTarget(sys.argv[2]).value
    platformstr = PrefabPlatform.get_current().value

    # We use dashes instead of underscores in target names.
    platformstr = platformstr.replace('_', '-')
    try:
        subprocess.run(
            ['make', f'prefab-{platformstr}-{targetstr}-build'], check=True
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

    # This command is not a good candidate for batch since it can be
    # long running and prints various stuff throughout the process.
    pcommand.disallow_in_batch()

    args = pcommand.get_args()

    if len(args) < 3:
        raise CleanError('Expected at least 3 args')
    try:
        category = batools.build.LazyBuildCategory(args[0])
    except ValueError as exc:
        raise CleanError(exc) from exc
    target = args[1]
    command = ' '.join(args[2:])
    try:
        batools.build.lazybuild(target, category, command)
    except subprocess.CalledProcessError as exc:
        raise CleanError(exc) from exc


def logcat() -> None:
    """Get logcat command for filtering."""
    import subprocess
    from efro.terminal import Clr
    from efro.error import CleanError

    pcommand.disallow_in_batch()

    if len(sys.argv) != 4:
        raise CleanError('Expected 2 args')
    adb = sys.argv[2]
    _plat = sys.argv[3]

    # My amazon tablet chokes on the color format.
    # if plat == 'amazon':
    #     format_args = ''
    # else:
    format_args = '-v color '
    cmd = (
        f'{adb} logcat {format_args}BallisticaKit:V CrashAnrDetector:V \'*:S\''
    )
    print(f'{Clr.BLU}Running logcat command: {Clr.BLD}{cmd}{Clr.RST}')
    subprocess.run(cmd, shell=True, check=True)


def _camel_case_split(string: str) -> list[str]:
    pcommand.disallow_in_batch()

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

    pcommand.disallow_in_batch()

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


def stage_build() -> None:
    """Stage assets for a build."""
    import batools.staging
    from efro.error import CleanError

    pcommand.disallow_in_batch()

    try:
        batools.staging.stage_build(
            projroot=str(pcommand.PROJROOT), args=pcommand.get_args()
        )
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

    pcommand.disallow_in_batch()

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

    pcommand.disallow_in_batch()

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

    pcommand.disallow_in_batch()

    if len(sys.argv) != 4:
        raise CleanError('Expected 2 args (srcfile, dstfile)')
    inpath = sys.argv[2]
    outpath = sys.argv[3]
    batools.metabuild.gen_binding_code(str(pcommand.PROJROOT), inpath, outpath)


def gen_flat_data_code() -> None:
    """Generate a C++ include file from a Python file."""
    from efro.error import CleanError
    import batools.metabuild

    pcommand.disallow_in_batch()

    if len(sys.argv) != 5:
        raise CleanError('Expected 3 args (srcfile, dstfile, varname)')
    inpath = sys.argv[2]
    outpath = sys.argv[3]
    varname = sys.argv[4]
    batools.metabuild.gen_flat_data_code(
        str(pcommand.PROJROOT), inpath, outpath, varname
    )


def genchangelog() -> None:
    """Gen a pretty html changelog."""
    from batools.changelog import generate

    pcommand.disallow_in_batch()

    generate(projroot=str(pcommand.PROJROOT))


def android_sdk_utils() -> None:
    """Wrangle android sdk stuff."""
    from batools.androidsdkutils import run

    pcommand.disallow_in_batch()

    run(projroot=str(pcommand.PROJROOT), args=sys.argv[2:])


def gen_python_enums_module() -> None:
    """Update our procedurally generated python enums."""
    from batools.enumspython import generate

    pcommand.disallow_in_batch()

    if len(sys.argv) != 4:
        raise RuntimeError('Expected infile and outfile args.')
    generate(
        projroot=str(pcommand.PROJROOT),
        infilename=sys.argv[2],
        outfilename=sys.argv[3],
    )


def gen_dummy_modules() -> None:
    """Generate all dummy modules."""
    from efro.error import CleanError
    from batools.dummymodule import generate_dummy_modules

    pcommand.disallow_in_batch()

    if len(sys.argv) != 2:
        raise CleanError(f'Expected no args; got {len(sys.argv)-2}.')

    generate_dummy_modules(projroot=str(pcommand.PROJROOT))


def version() -> None:
    """Check app versions."""
    from batools.version import run

    pcommand.disallow_in_batch()

    run(projroot=str(pcommand.PROJROOT), args=sys.argv[2:])
