# Copyright (c) 2011-2020 Eric Froemling
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
# -----------------------------------------------------------------------------
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

if TYPE_CHECKING:
    from typing import List, Sequence, Optional

CLRBLU = '\033[94m'  # Blue.
CLRHDR = '\033[95m'  # Header.
CLREND = '\033[0m'  # End.


# Python pip packages we require for this project.
@dataclass
class PipRequirement:
    """A pip package required by our project."""
    modulename: str
    minversion: Optional[List[int]] = None  # None implies no min version.
    pipname: Optional[str] = None  # None implies same as modulename.


PIP_REQUIREMENTS = [
    PipRequirement(modulename='pylint', minversion=[2, 5, 0]),
    PipRequirement(modulename='mypy', minversion=[0, 770]),
    PipRequirement(modulename='yapf', minversion=[0, 30, 0]),
    PipRequirement(modulename='typing_extensions'),
    PipRequirement(modulename='pytz'),
    PipRequirement(modulename='yaml', pipname='PyYAML'),
    PipRequirement(modulename='requests'),
    PipRequirement(modulename='pytest'),
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
    ['mac.package.server', 'android.pylibs.x86_64'],
    ['windows.package.oculus'],
    ['android.pylibs.x86_64.debug'],
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
    DEBUG = 'debug'
    SERVER_DEBUG = 'server-debug'
    RELEASE = 'release'
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
            print(f'{CLRHDR}Build of {tnamepretty} triggered by'
                  f' {path}{CLREND}')
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
    print(f'{CLRBLU}Lazybuild: skipping "{tnamepretty}"'
          f' ({unchanged_count} inputs unchanged).{CLREND}')
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
        paths = ['Makefile', 'tools/generate_code', 'src/generated_src']

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
            'Makefile', 'tools/snippets', 'resources/src', 'resources/Makefile'
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

    # Would be faster to package this into a single command but
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

    lines = []
    for i, flavor in enumerate(
            sorted(os.listdir('ballisticacore-android/BallisticaCore/src'))):
        if flavor == 'main' or flavor.startswith('.'):
            continue
        mode = modes[(dayoffset + i) % len(modes)]
        lines.append('ANDROID_PLATFORM=' + flavor + ' ANDROID_MODE=' + mode +
                     ' nice -n 15 make android-build')

    # Now add sparse tests that land on today.
    if DO_SPARSE_TEST_BUILDS:
        extras = SPARSE_TEST_BUILDS[dayoffset % len(SPARSE_TEST_BUILDS)]
        extras = [e for e in extras if e.startswith('android.')]
        for extra in extras:
            if extra == 'android.pylibs.arm':
                lines.append('tools/snippets python_build_android arm')
            elif extra == 'android.pylibs.arm.debug':
                lines.append('tools/snippets python_build_android_debug arm')
            elif extra == 'android.pylibs.arm64':
                lines.append('tools/snippets python_build_android arm64')
            elif extra == 'android.pylibs.arm64.debug':
                lines.append('tools/snippets python_build_android_debug arm64')
            elif extra == 'android.pylibs.x86':
                lines.append('tools/snippets python_build_android x86')
            elif extra == 'android.pylibs.x86.debug':
                lines.append('tools/snippets python_build_android_debug x86')
            elif extra == 'android.pylibs.x86_64':
                lines.append('tools/snippets python_build_android x86_64')
            elif extra == 'android.pylibs.x86_64.debug':
                lines.append(
                    'tools/snippets python_build_android_debug x86_64')
            elif extra == 'android.package':
                lines.append('make android-package')
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

    lines.append(f'WINDOWS_PROJECT= WINDOWS_PLATFORM={pval1} '
                 f'WINDOWS_CONFIGURATION={cfg1} make windows-build')
    lines.append(f'WINDOWS_PROJECT=Headless WINDOWS_PLATFORM={pval2} '
                 f'WINDOWS_CONFIGURATION={cfg2} make windows-build')
    lines.append(f'WINDOWS_PROJECT=Oculus WINDOWS_PLATFORM={pval3} '
                 f'WINDOWS_CONFIGURATION={cfg3} make windows-build')

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
    lines.append('nice -n 18 make ios-build')
    lines.append('nice -n 18 make ios-new-build')
    if DO_SPARSE_TEST_BUILDS:
        extras = SPARSE_TEST_BUILDS[dayoffset % len(SPARSE_TEST_BUILDS)]
        extras = [e for e in extras if e.startswith('ios.')]
        for extra in extras:
            if extra == 'ios.pylibs':
                lines.append('tools/snippets python_build_apple ios')
            elif extra == 'ios.pylibs.debug':
                lines.append('tools/snippets python_build_apple_debug ios')
            else:
                raise RuntimeError(f'Unknown extra: {extra}')

    # tvOS stuff
    lines.append('nice -n 18 make tvos-build')
    if DO_SPARSE_TEST_BUILDS:
        extras = SPARSE_TEST_BUILDS[dayoffset % len(SPARSE_TEST_BUILDS)]
        extras = [e for e in extras if e.startswith('tvos.')]
        for extra in extras:
            if extra == 'tvos.pylibs':
                lines.append('tools/snippets python_build_apple tvos')
            elif extra == 'tvos.pylibs.debug':
                lines.append('tools/snippets python_build_apple_debug tvos')
            else:
                raise RuntimeError(f'Unknown extra: {extra}')

    # macOS stuff
    lines.append('nice -n 18 make mac-build')
    # (throw release build in the mix to hopefully catch opt-mode-only errors).
    lines.append('nice -n 18 make mac-appstore-release-build')
    lines.append('nice -n 18 make mac-new-build')
    lines.append('nice -n 18 make mac-server-build')
    lines.append('nice -n 18 make cmake-build')
    if DO_SPARSE_TEST_BUILDS:
        extras = SPARSE_TEST_BUILDS[dayoffset % len(SPARSE_TEST_BUILDS)]
        extras = [e for e in extras if e.startswith('mac.')]
        for extra in extras:
            if extra == 'mac.package':
                lines.append('make mac-package')
            elif extra == 'mac.package.server':
                lines.append('make mac-server-package')
            elif extra == 'mac.pylibs':
                lines.append('tools/snippets python_build_apple mac')
            elif extra == 'mac.pylibs.debug':
                lines.append('tools/snippets python_build_apple_debug mac')
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
    linflav = 'LINUX_FLAVOR=u18s'
    lines = []
    for target in targets:
        lines.append(f'{linflav} make linux-{target}')

    if DO_SPARSE_TEST_BUILDS:
        extras = SPARSE_TEST_BUILDS[dayoffset % len(SPARSE_TEST_BUILDS)]
        extras = [e for e in extras if e.startswith('linux.')]
        for extra in extras:
            if extra == 'linux.package':
                lines.append(f'{linflav} make linux-package')
            elif extra == 'linux.package.server':
                lines.append(f'{linflav} make linux-server-package')
            else:
                raise RuntimeError(f'Unknown extra: {extra}')

    with open('_fulltest_buildfile_linux', 'w') as outfile:
        outfile.write('\n'.join(lines))


def get_current_prefab_platform() -> str:
    """Get the name of the running platform.

    Throws a RuntimeError on unsupported platforms.
    """
    import platform
    system = platform.system()
    machine = platform.machine()
    if system == 'Darwin':
        # Currently there's just x86_64 on mac;
        # will need to revisit when arm
        # cpus happen.
        return 'mac'
    if system == 'Linux':
        # If it looks like we're in Windows Subsystem for Linux,
        # go with the Windows version.
        if 'microsoft' in platform.uname()[3].lower():
            return 'windows'

        # We currently only support x86_64 linux.
        if machine == 'x86_64':
            return 'linux'
        raise RuntimeError(f'make_prefab: unsupported linux machine type:'
                           f' {machine}.')
    raise RuntimeError(f'make_prefab: unrecognized platform:'
                       f' {platform.system()}.')


def _vstr(nums: Sequence[int]) -> str:
    return '.'.join(str(i) for i in nums)


def checkenv() -> None:
    """Check for tools necessary to build and run the app."""
    from efrotools import PYTHON_BIN
    print('Checking environment...', flush=True)

    # Make sure they've got curl.
    if subprocess.run(['which', 'curl'], check=False,
                      capture_output=True).returncode != 0:
        raise RuntimeError('curl is required; please install it.')

    # Make sure they've got our target python version.
    if subprocess.run(['which', PYTHON_BIN], check=False,
                      capture_output=True).returncode != 0:
        raise RuntimeError(f'{PYTHON_BIN} is required; please install it.')

    # Make sure they've got pip for that python version.
    if subprocess.run(f'{PYTHON_BIN} -m pip --version',
                      shell=True,
                      check=False,
                      capture_output=True).returncode != 0:
        raise RuntimeError(
            'pip (for {PYTHON_BIN}) is required; please install it.')

    # Check for some required python modules.
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
            raise RuntimeError(
                f'{packagename} (for {PYTHON_BIN}) is required.\n'
                f'To install it, try: "{PYTHON_BIN}'
                f' -m pip install {packagename}"')
        if minver is not None:
            ver_line = results.stdout.decode().splitlines()[0]
            assert modname in ver_line
            vnums = [int(x) for x in ver_line.split()[-1].split('.')]
            assert len(vnums) == len(minver)
            if vnums < minver:
                raise RuntimeError(
                    f'{packagename} ver. {_vstr(minver)} or newer is required;'
                    f' found {_vstr(vnums)}.\n'
                    f'To upgrade it, try: "{PYTHON_BIN}'
                    f' -m pip install --upgrade {packagename}".\n'
                    'Alternately, "tools/snippets intall_pip_reqs"'
                    ' will update all pip requirements.')

    print('Environment ok.', flush=True)


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
            'cp', '-v', 'ballisticacore-cmake/build/release/make_bob',
            'tools/make_bob/mac_x86_64/'
        ],
        check=True,
    )
    print('Building linux_x86_64...', flush=True)
    subprocess.run(['make', 'linux-build'], check=True, env=env)
    subprocess.run(
        [
            'cp', '-v', 'build/linux-release/make_bob',
            'tools/make_bob/linux_x86_64/'
        ],
        check=True,
    )
    print('All builds complete!', flush=True)


def _get_server_config_raw_contents() -> str:
    import textwrap
    with open('tools/bacommon/servermanager.py') as infile:
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


def _get_server_config_template_yaml() -> str:
    import yaml
    lines_in = _get_server_config_raw_contents().splitlines()
    lines_out: List[str] = []
    for line in lines_in:
        if line != '' and not line.startswith('#'):
            vname, _vtype, veq, vval_raw = line.split()
            assert vname.endswith(':')
            vname = vname[:-1]
            assert veq == '='
            vval = eval(vval_raw)  # pylint: disable=eval-used

            # Override a few specifics:
            if vname == 'playlist_code':
                vval = 12345
            lines_out.append('#' + yaml.dump({vname: vval}).strip())
        else:
            lines_out.append(line)
    return '\n'.join(lines_out)


def filter_server_config(infilename: str, outfilename: str) -> None:
    """Add commented-out config options to a server config."""
    with open(infilename) as infile:
        cfg = infile.read()
    cfg = cfg.replace('#__CONFIG_TEMPLATE_VALUES__',
                      _get_server_config_template_yaml())
    with open(outfilename, 'w') as outfile:
        outfile.write(cfg)
