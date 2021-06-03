# Released under the MIT License. See LICENSE for details.
#
"""General functionality related to running builds."""
from __future__ import annotations

import os
import sys
from enum import Enum
import datetime
from dataclasses import dataclass
import subprocess
from pathlib import Path
from typing import TYPE_CHECKING

from efro.error import CleanError
from efro.terminal import Clr

if TYPE_CHECKING:
    from typing import List, Sequence, Optional, Any, Dict


# Python pip packages we require for this project.
@dataclass
class PipRequirement:
    """A pip package required by our project."""
    modulename: str
    minversion: Optional[List[int]] = None  # None implies no min version.
    pipname: Optional[str] = None  # None implies same as modulename.


PIP_REQUIREMENTS = [
    PipRequirement(modulename='pylint', minversion=[2, 8, 2]),
    PipRequirement(modulename='mypy', minversion=[0, 812]),
    PipRequirement(modulename='yapf', minversion=[0, 31, 0]),
    PipRequirement(modulename='cpplint', minversion=[1, 5, 5]),
    PipRequirement(modulename='pytest', minversion=[6, 2, 4]),
    PipRequirement(modulename='typing_extensions'),
    PipRequirement(modulename='pytz'),
    PipRequirement(modulename='ansiwrap'),
    PipRequirement(modulename='yaml', pipname='PyYAML'),
    PipRequirement(modulename='requests'),
]

# Parts of full-tests suite we only run on particular days.
# (This runs in listed order so should be randomized by hand to avoid
# clustering similar tests too much)
SPARSE_TEST_BUILDS: List[List[str]] = [
    ['ios.pylibs.debug', 'android.pylibs.arm'],
    ['linux.package', 'android.pylibs.arm64'],
    ['windows.package', 'mac.pylibs'],
    ['tvos.pylibs', 'android.pylibs.x86'],
    ['android.pylibs.arm.debug'],
    ['windows.package.server'],
    ['ios.pylibs', 'android.pylibs.arm64.debug'],
    ['linux.package.server'],
    ['android.pylibs.x86.debug', 'mac.package'],
    ['mac.package.server.arm64', 'android.pylibs.x86_64'],
    ['windows.package.oculus'],
    ['mac.package.server.x86_64', 'android.pylibs.x86_64.debug'],
    ['mac.pylibs.debug', 'android.package'],
]

# Currently only doing sparse-tests in core; not spinoffs.
# (whole word will get subbed out in spinoffs so this will be false)
DO_SPARSE_TEST_BUILDS = 'ballistica' + 'core' == 'ballisticacore'


class SourceCategory(Enum):
    """Types of sources."""
    RESOURCES = 'resources_src'
    CODE_GEN = 'code_gen_src'
    ASSETS = 'assets_src'
    CMAKE = 'cmake_src'
    WIN = 'win_src'


class PrefabTarget(Enum):
    """Types of prefab builds able to be run."""
    DEBUG = 'gui-debug'
    SERVER_DEBUG = 'server-debug'
    RELEASE = 'gui-release'
    SERVER_RELEASE = 'server-release'


def _lazybuild_check_paths(inpaths: List[str], category: SourceCategory,
                           target: str) -> bool:
    # pylint: disable=too-many-branches

    mtime = None if not os.path.exists(target) else os.path.getmtime(target)

    if target.startswith('.cache/lazybuild/'):
        tnamepretty = target[len('.cache/lazybuild/'):]
    else:
        tnamepretty = target

    def _testpath(path: str) -> bool:
        # Now see this path is newer than our target..
        if mtime is None or os.path.getmtime(path) >= mtime:
            print(f'{Clr.SMAG}Build of {tnamepretty} triggered by change in'
                  f" '{path}'{Clr.RST}")
            return True
        return False

    unchanged_count = 0
    for inpath in inpaths:
        # Add files verbatim; recurse through dirs.
        if os.path.isfile(inpath):
            if _testpath(inpath):
                return True
            unchanged_count += 1
            continue
        for root, _dnames, fnames in os.walk(inpath):

            # Only gen category uses gen src.
            if (root.startswith('src/generated_src')
                    and category is not SourceCategory.CODE_GEN):
                continue

            # None of our targets use tools-src.
            if root.startswith('src/tools'):
                continue

            # Skip most of external except for key cases.
            if root.startswith('src/external'):
                if category is SourceCategory.WIN and root.startswith(
                        'src/external/windows'):
                    pass
                else:
                    continue

            # Ignore python cache files.
            if '__pycache__' in root:
                continue
            for fname in fnames:
                # Ignore dot files
                if fname.startswith('.'):
                    continue
                fpath = os.path.join(root, fname)
                if ' ' in fpath:
                    raise RuntimeError(f'Invalid path with space: {fpath}')

                if _testpath(fpath):
                    return True
                unchanged_count += 1
    print(f'{Clr.BLU}Lazybuild: skipping "{tnamepretty}"'
          f' ({unchanged_count} inputs unchanged).{Clr.RST}')
    return False


def lazybuild(target: str, category: SourceCategory, command: str) -> None:
    """Run a build if anything in some category is newer than a target.

    This can be used as an optimization for build targets that *always* run.
    As an example, a target that spins up a VM and runs a build can be
    expensive even if the VM build process determines that nothing has changed
    and does no work. We can use this to examine a broad swath of source files
    and skip firing up the VM if nothing has changed. We can be overly broad
    in the sources we look at since the worst result of a false positive change
    is the VM spinning up and determining that no actual inputs have changed.
    We could recreate this mechanism purely in the Makefile, but large numbers
    of target sources can add significant overhead each time the Makefile is
    invoked; in our case the cost is only incurred when a build is triggered.

    Note that target's mod-time will *always* be updated to match the newest
    source regardless of whether the build itself was triggered.
    """
    paths: List[str]

    # Everything possibly affecting generated code.
    if category is SourceCategory.CODE_GEN:
        paths = [
            'Makefile', 'tools/generate_code', 'tools/batools/codegen.py',
            'src/generated_src'
        ]

    # Everything possibly affecting asset builds.
    elif category is SourceCategory.ASSETS:
        paths = ['Makefile', 'tools/convert_util', 'assets/src']

    # Everything possibly affecting CMake builds.
    elif category is SourceCategory.CMAKE:
        paths = ['Makefile', 'src', 'ballisticacore-cmake/CMakeLists.txt']

    # Everything possibly affecting Windows binary builds.
    elif category is SourceCategory.WIN:
        paths = ['Makefile', 'src', 'resources/src']

    # Everything possibly affecting resource builds.
    elif category is SourceCategory.RESOURCES:
        paths = [
            'Makefile', 'tools/pcommand', 'resources/src', 'resources/Makefile'
        ]
    else:
        raise ValueError(f'Invalid source category: {category}')

    # Now do the thing if any our our input mod times changed.
    if _lazybuild_check_paths(paths, category, target):
        subprocess.run(command, shell=True, check=True)

        # We also explicitly update the mod-time of the target;
        # the command we (such as a VM build) may not have actually
        # done anything but we still want to update our target to
        # be newer than all the lazy sources.
        os.makedirs(os.path.dirname(target), exist_ok=True)
        Path(target).touch()


def archive_old_builds(ssh_server: str, builds_dir: str,
                       ssh_args: List[str]) -> None:
    """Stuff our old public builds into the 'old' dir.

    (called after we push newer ones)
    """

    def ssh_run(cmd: str) -> str:
        val: str = subprocess.check_output(['ssh'] + ssh_args +
                                           [ssh_server, cmd]).decode()
        return val

    files = ssh_run('ls -1t "' + builds_dir + '"').splitlines()

    # For every file we find, gather all the ones with the same prefix;
    # we'll want to archive all but the first one.
    files_to_archive = set()
    for fname in files:
        if '_' not in fname:
            continue
        prefix = '_'.join(fname.split('_')[:-1])
        for old_file in [f for f in files if f.startswith(prefix)][1:]:
            files_to_archive.add(old_file)

    # Would be more efficient to package this into a single command but
    # this works.
    for fname in sorted(files_to_archive):
        print('Archiving ' + fname, file=sys.stderr)
        ssh_run('mv "' + builds_dir + '/' + fname + '" "' + builds_dir +
                '/old/"')


def gen_fulltest_buildfile_android() -> None:
    """Generate fulltest command list for jenkins.

    (so we see nice pretty split-up build trees)
    """
    # pylint: disable=too-many-branches

    # Its a pretty big time-suck building all architectures for
    # all of our subplatforms, so lets usually just build a single one.
    # We'll rotate it though and occasionally do all 4 at once just to
    # be safe.
    dayoffset = datetime.datetime.now().timetuple().tm_yday

    # Let's only do a full 'prod' once every two times through the loop.
    # (it really should never catch anything that individual platforms don't)
    modes = ['arm', 'arm64', 'x86', 'x86_64']
    modes += modes
    modes.append('prod')

    # By default we cycle through build architectures for each flavor.
    # However, for minor flavor with low risk of platform-dependent breakage
    # we stick to a single one to keep disk space costs lower. (build files
    # amount to several gigs per mode per flavor)
    # UPDATE: Now that we have CPU time to spare, we simply always do 'arm64'
    # or 'prod' depending on build type; this results in 1 or 4 architectures
    # worth of build files per flavor instead of 8 (prod + 4 singles) and
    # keeps our daily runs identical.
    lightweight_flavors = {'template', 'arcade', 'demo', 'iircade'}

    lines = []
    for _i, flavor in enumerate(
            sorted(os.listdir('ballisticacore-android/BallisticaCore/src'))):
        if flavor == 'main' or flavor.startswith('.'):
            continue

        if flavor in lightweight_flavors:
            mode = 'arm64'
        else:
            # mode = modes[(dayoffset + i) % len(modes)]
            mode = 'prod'
        lines.append('ANDROID_PLATFORM=' + flavor + ' ANDROID_MODE=' + mode +
                     ' make android-cloud-build')

    # Now add sparse tests that land on today.
    if DO_SPARSE_TEST_BUILDS:
        extras = SPARSE_TEST_BUILDS[dayoffset % len(SPARSE_TEST_BUILDS)]
        extras = [e for e in extras if e.startswith('android.')]
        cspre = 'tools/cloudshell linbeast --env android --'
        for extra in extras:
            if extra == 'android.pylibs.arm':
                lines.append(f'{cspre} tools/pcommand'
                             f' python_build_android arm')
            elif extra == 'android.pylibs.arm.debug':
                lines.append(f'{cspre} tools/pcommand'
                             f' python_build_android_debug arm')
            elif extra == 'android.pylibs.arm64':
                lines.append(f'{cspre} tools/pcommand'
                             f' python_build_android arm64')
            elif extra == 'android.pylibs.arm64.debug':
                lines.append(f'{cspre} tools/pcommand'
                             f' python_build_android_debug arm64')
            elif extra == 'android.pylibs.x86':
                lines.append(f'{cspre} tools/pcommand'
                             f' python_build_android x86')
            elif extra == 'android.pylibs.x86.debug':
                lines.append(f'{cspre} tools/pcommand'
                             f' python_build_android_debug x86')
            elif extra == 'android.pylibs.x86_64':
                lines.append(f'{cspre} tools/pcommand'
                             f' python_build_android x86_64')
            elif extra == 'android.pylibs.x86_64.debug':
                lines.append(f'{cspre} tools/pcommand'
                             f' python_build_android_debug x86_64')
            elif extra == 'android.package':
                lines.append('make android-cloud-package')
            else:
                raise RuntimeError(f'Unknown extra: {extra}')

    with open('_fulltest_buildfile_android', 'w') as outfile:
        outfile.write('\n'.join(lines))


def gen_fulltest_buildfile_windows() -> None:
    """Generate fulltest command list for jenkins.

    (so we see nice pretty split-up build trees)
    """

    dayoffset = datetime.datetime.now().timetuple().tm_yday

    lines: List[str] = []

    # We want to do one regular, one headless, and one oculus build,
    # but let's switch up 32 or 64 bit based on the day.
    # Also occasionally throw a release build in but stick to
    # mostly debug builds to keep build times speedier.
    pval1 = 'Win32' if dayoffset % 2 == 0 else 'x64'
    pval2 = 'Win32' if (dayoffset + 1) % 2 == 0 else 'x64'
    pval3 = 'Win32' if (dayoffset + 2) % 2 == 0 else 'x64'
    cfg1 = 'Release' if dayoffset % 7 == 0 else 'Debug'
    cfg2 = 'Release' if (dayoffset + 1) % 7 == 0 else 'Debug'
    cfg3 = 'Release' if (dayoffset + 2) % 7 == 0 else 'Debug'

    lines.append(f'WINDOWS_PROJECT=Generic WINDOWS_PLATFORM={pval1} '
                 f'WINDOWS_CONFIGURATION={cfg1} make windows-cloud-build')
    lines.append(f'WINDOWS_PROJECT=Headless WINDOWS_PLATFORM={pval2} '
                 f'WINDOWS_CONFIGURATION={cfg2} make windows-cloud-build')
    lines.append(f'WINDOWS_PROJECT=Oculus WINDOWS_PLATFORM={pval3} '
                 f'WINDOWS_CONFIGURATION={cfg3} make windows-cloud-build')

    # Now add sparse tests that land on today.
    if DO_SPARSE_TEST_BUILDS:
        extras = SPARSE_TEST_BUILDS[dayoffset % len(SPARSE_TEST_BUILDS)]
        extras = [e for e in extras if e.startswith('windows.')]
        for extra in extras:
            if extra == 'windows.package':
                lines.append('make windows-package')
            elif extra == 'windows.package.server':
                lines.append('make windows-server-package')
            elif extra == 'windows.package.oculus':
                lines.append('make windows-oculus-package')
            else:
                raise RuntimeError(f'Unknown extra: {extra}')

    with open('_fulltest_buildfile_windows', 'w') as outfile:
        outfile.write('\n'.join(lines))


def gen_fulltest_buildfile_apple() -> None:
    """Generate fulltest command list for jenkins.

    (so we see nice pretty split-up build trees)
    """
    # pylint: disable=too-many-branches

    dayoffset = datetime.datetime.now().timetuple().tm_yday

    # noinspection PyListCreation
    lines = []

    # iOS stuff
    lines.append('make ios-build')
    lines.append('make ios-new-build')
    if DO_SPARSE_TEST_BUILDS:
        extras = SPARSE_TEST_BUILDS[dayoffset % len(SPARSE_TEST_BUILDS)]
        extras = [e for e in extras if e.startswith('ios.')]
        for extra in extras:
            if extra == 'ios.pylibs':
                lines.append('tools/pcommand python_build_apple ios')
            elif extra == 'ios.pylibs.debug':
                lines.append('tools/pcommand python_build_apple_debug ios')
            else:
                raise RuntimeError(f'Unknown extra: {extra}')

    # tvOS stuff
    lines.append('make tvos-build')
    if DO_SPARSE_TEST_BUILDS:
        extras = SPARSE_TEST_BUILDS[dayoffset % len(SPARSE_TEST_BUILDS)]
        extras = [e for e in extras if e.startswith('tvos.')]
        for extra in extras:
            if extra == 'tvos.pylibs':
                lines.append('tools/pcommand python_build_apple tvos')
            elif extra == 'tvos.pylibs.debug':
                lines.append('tools/pcommand python_build_apple_debug tvos')
            else:
                raise RuntimeError(f'Unknown extra: {extra}')

    # macOS stuff
    lines.append('make mac-build')
    # (throw release build in the mix to hopefully catch opt-mode-only errors).
    lines.append('make mac-appstore-release-build')
    lines.append('make mac-new-build')
    lines.append('make cmake-server-build')
    lines.append('make cmake-build')
    if DO_SPARSE_TEST_BUILDS:
        extras = SPARSE_TEST_BUILDS[dayoffset % len(SPARSE_TEST_BUILDS)]
        extras = [e for e in extras if e.startswith('mac.')]
        for extra in extras:
            if extra == 'mac.package':
                lines.append('make mac-package')
            elif extra == 'mac.package.server.x86_64':
                lines.append('make mac-cloud-server-package-x86-64')
            elif extra == 'mac.package.server.arm64':
                lines.append('make mac-cloud-server-package-arm64')
            elif extra == 'mac.pylibs':
                lines.append('tools/pcommand python_build_apple mac')
            elif extra == 'mac.pylibs.debug':
                lines.append('tools/pcommand python_build_apple_debug mac')
            else:
                raise RuntimeError(f'Unknown extra: {extra}')

    with open('_fulltest_buildfile_apple', 'w') as outfile:
        outfile.write('\n'.join(lines))


def gen_fulltest_buildfile_linux() -> None:
    """Generate fulltest command list for jenkins.

    (so we see nice pretty split-up build trees)
    """

    dayoffset = datetime.datetime.now().timetuple().tm_yday

    targets = ['build', 'server-build']
    lines = []
    for target in targets:
        lines.append(f'make cmake-cloud-{target}')

    if DO_SPARSE_TEST_BUILDS:
        extras = SPARSE_TEST_BUILDS[dayoffset % len(SPARSE_TEST_BUILDS)]
        extras = [e for e in extras if e.startswith('linux.')]
        for extra in extras:
            if extra == 'linux.package':
                lines.append('make linux-package')
            elif extra == 'linux.package.server':
                lines.append('make linux-server-package')
            else:
                raise RuntimeError(f'Unknown extra: {extra}')

    with open('_fulltest_buildfile_linux', 'w') as outfile:
        outfile.write('\n'.join(lines))


def get_current_build_platform(wsl_gives_windows: bool = True) -> str:
    """Get an identifier for the platform running this build.

    Throws a RuntimeError on unsupported platforms.
    """
    import platform
    system = platform.system()
    machine = platform.machine()

    if system == 'Darwin':
        if machine == 'x86_64':
            return 'mac_x86_64'
        if machine == 'arm64':
            return 'mac_arm64'
        # TODO: add support for arm macs.
        raise RuntimeError(f'make_prefab: unsupported mac machine type:'
                           f' {machine}.')
    if system == 'Linux':
        # If it looks like we're in Windows Subsystem for Linux,
        # we may want to operate on Windows versions.
        if wsl_gives_windows:
            if 'microsoft' in platform.uname().release.lower():
                # TODO: add support for arm windows
                if machine == 'x86_64':
                    return 'windows_x86'
                raise RuntimeError(
                    f'make_prefab: unsupported win machine type:'
                    f' {machine}.')

        if machine == 'x86_64':
            return 'linux_x86_64'
        if machine == 'aarch64':
            return 'linux_arm64'
        raise RuntimeError(f'make_prefab: unsupported linux machine type:'
                           f' {machine}.')
    raise RuntimeError(f'make_prefab: unrecognized platform:'
                       f' {platform.system()}.')


def _vstr(nums: Sequence[int]) -> str:
    return '.'.join(str(i) for i in nums)


def checkenv() -> None:
    """Check for tools necessary to build and run the app."""
    # pylint: disable=too-many-branches

    from efrotools import PYTHON_BIN
    print(f'{Clr.BLD}Checking environment...{Clr.RST}', flush=True)

    # Make sure they've got curl.
    if subprocess.run(['which', 'curl'], check=False,
                      capture_output=True).returncode != 0:
        raise CleanError('curl is required; please install it via apt,'
                         ' brew, etc.')

    # Make sure they've got rsync.
    if subprocess.run(['which', 'rsync'], check=False,
                      capture_output=True).returncode != 0:
        raise CleanError('rsync is required; please install it via apt,'
                         ' brew, etc.')

    # Make sure they've got our target python version.
    if subprocess.run(['which', PYTHON_BIN], check=False,
                      capture_output=True).returncode != 0:
        raise CleanError(f'{PYTHON_BIN} is required; please install it'
                         'via apt, brew, etc.')

    # Make sure they've got clang-format.
    if subprocess.run(['which', 'clang-format'],
                      check=False,
                      capture_output=True).returncode != 0:
        raise CleanError('clang-format is required; please install '
                         'it via apt, brew, etc.')

    # Make sure they've got pip for that python version.
    if subprocess.run(f'{PYTHON_BIN} -m pip --version',
                      shell=True,
                      check=False,
                      capture_output=True).returncode != 0:
        raise CleanError(
            f'pip (for {PYTHON_BIN}) is required; please install it.')

    # Check for some required python modules.
    # FIXME: since all of these come from pip now, we should just use
    # pip --list to check versions on everything instead of doing it ad-hoc.
    for req in PIP_REQUIREMENTS:
        modname = req.modulename
        minver = req.minversion
        packagename = req.pipname
        if packagename is None:
            packagename = modname
        if minver is not None:
            results = subprocess.run(f'{PYTHON_BIN} -m {modname} --version',
                                     shell=True,
                                     check=False,
                                     capture_output=True)
        else:
            results = subprocess.run(f'{PYTHON_BIN} -c "import {modname}"',
                                     shell=True,
                                     check=False,
                                     capture_output=True)
        if results.returncode != 0:
            raise CleanError(f'{packagename} (for {PYTHON_BIN}) is required.\n'
                             f'To install it, try: "{PYTHON_BIN}'
                             f' -m pip install {packagename}"\n'
                             f'Alternately, "tools/pcommand install_pip_reqs"'
                             f' will update all pip requirements.')
        if minver is not None:
            # Note: some modules such as pytest print their version to stderr,
            # so grab both.
            verlines = (results.stdout + results.stderr).decode().splitlines()
            if verlines[0].startswith('Cpplint fork'):
                verlines = verlines[1:]
            ver_line = verlines[0]
            assert modname in ver_line
            vnums = [int(x) for x in ver_line.split()[-1].split('.')]
            assert len(vnums) == len(minver)
            if vnums < minver:
                raise CleanError(
                    f'{packagename} ver. {_vstr(minver)} or newer is required;'
                    f' found {_vstr(vnums)}.\n'
                    f'To upgrade it, try: "{PYTHON_BIN}'
                    f' -m pip install --upgrade {packagename}".\n'
                    'Alternately, "tools/pcommand install_pip_reqs"'
                    ' will update all pip requirements.')

    print(f'{Clr.BLD}Environment ok.{Clr.RST}', flush=True)


def get_pip_reqs() -> List[str]:
    """Return the pip requirements needed to build/run stuff."""
    out: List[str] = []
    for req in PIP_REQUIREMENTS:
        name = req.modulename if req.pipname is None else req.pipname
        assert isinstance(name, str)
        out.append(name)
    return out


def update_makebob() -> None:
    """Build fresh make_bob binaries for all relevant platforms."""
    print('Building mac_x86_64...', flush=True)
    env = dict(os.environ)
    env['CMAKE_BUILD_TYPE'] = 'Release'
    subprocess.run(['make', 'cmake-build'], check=True, env=env)
    subprocess.run(
        [
            'cp', '-v', 'build/cmake/release/make_bob',
            'tools/make_bob/mac_x86_64/'
        ],
        check=True,
    )
    print('Building linux_x86_64...', flush=True)
    subprocess.run(['make', 'linux-vm-build'], check=True, env=env)
    subprocess.run(
        [
            'cp', '-v', 'build/linux-release/make_bob',
            'tools/make_bob/linux_x86_64/'
        ],
        check=True,
    )
    print('All builds complete!', flush=True)


def _get_server_config_raw_contents(projroot: str) -> str:
    import textwrap
    with open(os.path.join(projroot,
                           'tools/bacommon/servermanager.py')) as infile:
        lines = infile.read().splitlines()
    firstline = lines.index('class ServerConfig:') + 1
    lastline = firstline + 1
    while True:
        line = lines[lastline]
        if line != '' and not line.startswith('    '):
            break
        lastline += 1

    # Move first line past doc-string to the first comment.
    while not lines[firstline].startswith('    #'):
        firstline += 1

    # Back last line up to before last empty lines.
    lastline -= 1
    while lines[lastline] == '':
        lastline -= 1

    return textwrap.dedent('\n'.join(lines[firstline:lastline + 1]))


def _get_server_config_template_yaml(projroot: str) -> str:
    # pylint: disable=too-many-branches
    import yaml
    lines_in = _get_server_config_raw_contents(projroot).splitlines()
    lines_out: List[str] = []
    ignore_vars = {'stress_test_players'}
    for line in lines_in:
        if any(line.startswith(f'{var}:') for var in ignore_vars):
            continue
        if line.startswith(' '):
            # Ignore indented lines (our few multi-line special cases).
            continue

        if line.startswith('team_names:'):
            lines_out += [
                '#team_names:',
                '#- Blue',
                '#- Red',
            ]
            continue

        if line.startswith('team_colors:'):
            lines_out += [
                '#team_colors:',
                '#- [0.1, 0.25, 1.0]',
                '#- [1.0, 0.25, 0.2]',
            ]
            continue

        if line.startswith('playlist_inline:'):
            lines_out += ['#playlist_inline: []']
            continue

        if line != '' and not line.startswith('#'):
            vname, _vtype, veq, vval_raw = line.split()
            assert vname.endswith(':')
            vname = vname[:-1]
            assert veq == '='
            vval: Any
            if vval_raw == 'field(default_factory=list)':
                vval = []
            else:
                vval = eval(vval_raw)  # pylint: disable=eval-used

            # Filter/override a few things.
            if vname == 'playlist_code':
                # User wouldn't want to pass the default of None here.
                vval = 12345
            elif vname == 'clean_exit_minutes':
                vval = 60
            elif vname == 'unclean_exit_minutes':
                vval = 90
            elif vname == 'idle_exit_minutes':
                vval = 20
            elif vname == 'stats_url':
                vval = ('https://mystatssite.com/'
                        'showstats?player=${ACCOUNT}')
            elif vname == 'admins':
                vval = ['pb-yOuRAccOuNtIdHErE', 'pb-aNdMayBeAnotherHeRE']
            lines_out += [
                '#' + l for l in yaml.dump({
                    vname: vval
                }).strip().splitlines()
            ]
        else:
            # Convert comments referring to python bools to yaml bools.
            line = line.replace('True', 'true').replace('False', 'false')
            if '(internal)' not in line:
                lines_out.append(line)
    return '\n'.join(lines_out)


def filter_server_config(projroot: str, infilepath: str) -> str:
    """Add commented-out config options to a server config."""
    with open(infilepath) as infile:
        cfg = infile.read()
    return cfg.replace('#__CONFIG_TEMPLATE_VALUES__',
                       _get_server_config_template_yaml(projroot))


def update_docs_md(check: bool) -> None:
    """Updates docs markdown files if necessary."""
    # pylint: disable=too-many-locals
    from efrotools import get_files_hash, run

    docs_path = 'docs/ba_module.md'

    # We store the hash in a separate file that only exists on private
    # so public isn't full of constant hash change commits.
    # (don't care so much on private)
    docs_hash_path = 'docs/ba_module_hash'

    # Generate a hash from all c/c++ sources under the python subdir
    # as well as all python scripts.
    pysources = []
    exts = ['.cc', '.c', '.h', '.py']
    for basedir in [
            'src/ballistica/python',
            'tools/efro',
            'tools/bacommon',
            'assets/src/ba_data/python/ba',
    ]:
        assert os.path.isdir(basedir), f'{basedir} is not a dir.'
        for root, _dirs, files in os.walk(basedir):
            for fname in files:
                if any(fname.endswith(ext) for ext in exts):
                    pysources.append(os.path.join(root, fname))
    pysources.sort()
    curhash = get_files_hash(pysources)

    # Extract the current embedded hash.
    with open(docs_hash_path) as infile:
        storedhash = infile.read()

    if curhash != storedhash or not os.path.exists(docs_path):
        if check:
            raise RuntimeError('Docs markdown is out of date.')

        print(f'Updating {docs_path}...', flush=True)
        run('make docs')

        # Our docs markdown is just the docs html with a few added
        # bits at the top.
        with open('build/docs.html') as infile:
            docs = infile.read()
        docs = ('<!-- THIS FILE IS AUTO GENERATED; DO NOT EDIT BY HAND -->\n'
                ) + docs
        with open(docs_path, 'w') as outfile:
            outfile.write(docs)
        with open(docs_hash_path, 'w') as outfile:
            outfile.write(curhash)
    print(f'{docs_path} is up to date.')


def cmake_prep_dir(dirname: str, verbose: bool = False) -> None:
    """Create a dir, recreating it when cmake/python/etc. versions change.

    Useful to prevent builds from breaking when cmake or other components
    are updated.
    """
    # pylint: disable=too-many-locals
    import json
    import platform
    from efrotools import PYVER

    @dataclass
    class Entry:
        """Item examined for presence/change."""
        name: str
        current_value: str

    entries: List[Entry] = []

    # Start fresh if cmake version changes.
    cmake_ver_output = subprocess.run(['cmake', '--version'],
                                      check=True,
                                      capture_output=True).stdout.decode()
    cmake_ver = cmake_ver_output.splitlines()[0].split('cmake version ')[1]
    entries.append(Entry('cmake version', cmake_ver))

    # ...or if the actual location of cmake on disk changes.
    cmake_path = os.path.realpath(
        subprocess.run(['which', 'cmake'], check=True,
                       capture_output=True).stdout.decode().strip())
    entries.append(Entry('cmake path', cmake_path))

    # ...or if python's version changes.
    python_ver_output = subprocess.run(
        [f'python{PYVER}', '--version'], check=True,
        capture_output=True).stdout.decode().strip()
    python_ver = python_ver_output.splitlines()[0].split('Python ')[1]
    entries.append(Entry('python_version', python_ver))

    # ...or if the actual location of python on disk changes.
    python_path = os.path.realpath(
        subprocess.run(['which', f'python{PYVER}'],
                       check=True,
                       capture_output=True).stdout.decode())
    entries.append(Entry('python_path', python_path))

    # ...or if mac xcode sdk paths change
    mac_xcode_sdks = (','.join(
        sorted(
            os.listdir('/Applications/Xcode.app/Contents/'
                       'Developer/Platforms/MacOSX.platform/'
                       'Developer/SDKs/')))
                      if platform.system() == 'Darwin' else '')
    entries.append(Entry('mac_xcode_sdks', mac_xcode_sdks))

    # Ok; do the thing.
    verfilename = os.path.join(dirname, '.ba_cmake_env')
    title = 'cmake_prep_dir'

    versions: Dict[str, str]
    if os.path.isfile(verfilename):
        with open(verfilename) as infile:
            versions = json.loads(infile.read())
            assert isinstance(versions, dict)
            assert all(isinstance(x, str) for x in versions.keys())
            assert all(isinstance(x, str) for x in versions.values())
    else:
        versions = {}
    changed = False
    for entry in entries:
        previous_value = versions.get(entry.name)
        if entry.current_value != previous_value:
            print(f'{Clr.BLU}{entry.name} changed from {previous_value}'
                  f' to {entry.current_value}; clearing existing build at'
                  f' "{dirname}".{Clr.RST}')
            changed = True
            break

    if changed:
        if verbose:
            print(
                f'{Clr.BLD}{title}:{Clr.RST} Blowing away existing build dir.')
        subprocess.run(['rm', '-rf', dirname], check=True)
        os.makedirs(dirname, exist_ok=True)
        with open(verfilename, 'w') as outfile:
            outfile.write(
                json.dumps(
                    {entry.name: entry.current_value
                     for entry in entries}))
    else:
        if verbose:
            print(f'{Clr.BLD}{title}:{Clr.RST} Keeping existing build dir.')
