# Released under the MIT License. See LICENSE for details.
#
"""General functionality related to running builds."""

from __future__ import annotations

import os
import sys
import subprocess
from enum import Enum
from dataclasses import dataclass
from typing import TYPE_CHECKING, assert_never

from efro.error import CleanError
from efro.terminal import Clr
from efrotools.lazybuild import LazyBuildContext

if TYPE_CHECKING:
    from typing import Sequence, Any


@dataclass
class PyRequirement:
    """A Python package/module required by our project."""

    modulename: str | None = None
    minversion: list[int] | None = None  # None implies no min version.
    pipname: str | None = None  # None implies same as modulename.


# Note: we look directly for modules when possible instead of just pip
# entries; this accounts for manual installations or other nonstandard
# setups.

# Note 2: That is probably overkill. We can probably just replace this
# with a simple requirements.txt file, can't we? Feels like we're mostly
# reinventing the wheel here. We just need a clean way to check/list
# missing stuff without necessarily installing it. And as far as
# manually-installed bits, pip itself must have some way to allow for
# that, right?...
PY_REQUIREMENTS = [
    PyRequirement(modulename='pylint', minversion=[2, 17, 3]),
    PyRequirement(modulename='mypy', minversion=[1, 2, 0]),
    PyRequirement(modulename='cpplint', minversion=[1, 6, 1]),
    PyRequirement(modulename='pytest', minversion=[7, 3, 1]),
    PyRequirement(modulename='pytz'),
    PyRequirement(modulename='ansiwrap'),
    PyRequirement(modulename='yaml', pipname='PyYAML'),
    PyRequirement(modulename='requests'),
    PyRequirement(modulename='pdoc'),
    PyRequirement(pipname='black', minversion=[23, 3, 0]),
    PyRequirement(pipname='typing_extensions', minversion=[4, 5, 0]),
    PyRequirement(pipname='types-filelock', minversion=[3, 2, 7]),
    PyRequirement(pipname='types-requests', minversion=[2, 28, 11, 17]),
    PyRequirement(pipname='types-pytz', minversion=[2023, 3, 0, 0]),
    PyRequirement(pipname='types-PyYAML', minversion=[6, 0, 12, 9]),
    PyRequirement(pipname='certifi', minversion=[2022, 12, 7]),
    PyRequirement(pipname='types-certifi', minversion=[2021, 10, 8, 3]),
    PyRequirement(pipname='pbxproj', minversion=[3, 5, 0]),
    PyRequirement(pipname='filelock', minversion=[3, 12, 0]),
]


class PrefabTarget(Enum):
    """Types of prefab builds able to be run."""

    GUI_DEBUG = 'gui-debug'
    SERVER_DEBUG = 'server-debug'
    GUI_RELEASE = 'gui-release'
    SERVER_RELEASE = 'server-release'


class LazyBuildCategory(Enum):
    """Types of sources."""

    RESOURCES = 'resources_src'
    ASSETS = 'assets_src'
    META = 'meta_src'
    CMAKE = 'cmake_src'
    WIN = 'win_src'
    DUMMYMODULES = 'dummymodules_src'


def lazybuild(target: str, category: LazyBuildCategory, command: str) -> None:
    """Run some lazybuild presets."""

    # Meta builds.
    if category is LazyBuildCategory.META:
        LazyBuildContext(
            target=target,
            command=command,
            # Since this category can kick off cleans and blow things
            # away, its not safe to have multiple builds going with it
            # at once.
            buildlockname=category.value,
            # Regular paths; changes to these will trigger meta build.
            srcpaths=[
                'Makefile',
                'src/meta',
                'src/ballistica/shared/foundation/types.h',
            ],
            # Our meta Makefile targets generally don't list tools
            # scripts that can affect their creation as sources, so
            # let's set up a catch-all here: when any of our tools stuff
            # changes we'll blow away all existing meta builds.
            #
            # Update: also including featureset-defs here; any time
            # we're mucking with those it's good to start fresh to be
            # sure.
            srcpaths_fullclean=[
                'tools/efrotools',
                'tools/efrotoolsinternal',
                'tools/batools',
                'tools/batoolsinternal',
                'config/featuresets',
            ],
            # Maintain a hash of all srcpaths and do a full-clean
            # whenever that changes. Takes care of orphaned files if a
            # featureset is removed/etc.
            manifest_file=f'.cache/lazybuild/manifest_{category.value}',
            command_fullclean='make meta-clean',
        ).run()

    # CMake builds.
    elif category is LazyBuildCategory.CMAKE:
        LazyBuildContext(
            target=target,
            # It should be safe to have multiple cmake build going at
            # once I think; different targets should never stomp on each
            # other. Actually if anything maybe we'd want to plug target
            # path into this to watch for the same target getting built
            # redundantly?
            buildlockname=None,
            srcpaths=[
                'Makefile',
                'src',
                'ballisticakit-cmake/CMakeLists.txt',
            ],
            dirfilter=(
                lambda root, dirname: not (
                    root == 'src' and dirname in {'meta', 'tools', 'external'}
                )
            ),
            command=command,
        ).run()

    # Windows binary builds.
    elif category is LazyBuildCategory.WIN:

        def _win_dirfilter(root: str, dirname: str) -> bool:
            if root == 'src' and dirname in {'meta', 'tools'}:
                return False
            if root == 'src/external' and dirname != 'windows':
                return False
            return True

        LazyBuildContext(
            target=target,
            # It should be safe to have multiple of these build going at
            # once I think; different targets should never stomp on each
            # other. Actually if anything maybe we'd want to plug target
            # path into this to watch for the same target getting built
            # redundantly?
            buildlockname=None,
            srcpaths=[
                'Makefile',
                'src',
                'ballisticakit-windows',
            ],
            dirfilter=_win_dirfilter,
            command=command,
        ).run()

    # Resource builds.
    elif category is LazyBuildCategory.RESOURCES:
        LazyBuildContext(
            target=target,
            # Even though this category currently doesn't run any clean
            # commands, going to restrict to one use at a time for now
            # in case we want to add that.
            buildlockname=category.value,
            srcpaths=[
                'Makefile',
                'tools/pcommand',
                'src/resources',
            ],
            command=command,
        ).run()

    # Asset builds.
    elif category is LazyBuildCategory.ASSETS:

        def _filefilter(root: str, filename: str) -> bool:
            # Exclude tools/spinoff; it doesn't affect asset builds and
            # we don't want to break if it is a symlink pointing to a
            # not-present parent repo.
            if root == 'tools' and filename == 'spinoff':
                return False
            return True

        LazyBuildContext(
            target=target,
            # Even though this category currently doesn't run any clean
            # commands, going to restrict to one use at a time for now
            # in case we want to add that.
            buildlockname=category.value,
            srcpaths=[
                'Makefile',
                'tools',
                'src/assets',
            ],
            command=command,
            filefilter=_filefilter,
        ).run()

    # Dummymodule builds.
    elif category is LazyBuildCategory.DUMMYMODULES:

        def _filefilter(root: str, filename: str) -> bool:
            # In our C++ sources, only look at stuff with 'python' in
            # the name.
            if root.startswith('ballistica'):
                return 'python' in filename

            # In other srcpaths use everything.
            return True

        LazyBuildContext(
            target=target,
            # This category builds binaries and other crazy stuff so we
            # definitely want to restrict to one at a time.
            buildlockname=category.value,
            srcpaths=[
                'config/featuresets',
                'tools/batools/dummymodule.py',
                'src/ballistica',
            ],
            command=command,
            filefilter=_filefilter,
            # Maintain a hash of all srcpaths and do a full-clean
            # whenever that changes. Takes care of orphaned files if a
            # featureset is removed/etc.
            manifest_file=f'.cache/lazybuild/manifest_{category.value}',
            command_fullclean='make dummymodules-clean',
        ).run()

    else:
        assert_never(category)


def archive_old_builds(
    ssh_server: str, builds_dir: str, ssh_args: list[str]
) -> None:
    """Stuff our old public builds into the 'old' dir.

    (called after we push newer ones)
    """

    def ssh_run(cmd: str) -> str:
        val: str = subprocess.check_output(
            ['ssh'] + ssh_args + [ssh_server, cmd]
        ).decode()
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
        ssh_run(
            'mv "' + builds_dir + '/' + fname + '" "' + builds_dir + '/old/"'
        )


def get_current_prefab_platform(wsl_gives_windows: bool = True) -> str:
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
        raise RuntimeError(
            f'make_prefab: unsupported mac machine type:' f' {machine}.'
        )
    if system == 'Linux':
        # If it looks like we're in Windows Subsystem for Linux,
        # we may want to operate on Windows versions.
        if wsl_gives_windows:
            if 'microsoft' in platform.uname().release.lower():
                if machine == 'x86_64':
                    # Currently always targeting 32 bit for prefab stuff.
                    return 'windows_x86'
                # TODO: add support for arm windows
                raise RuntimeError(
                    f'make_prefab: unsupported win machine type: {machine}.'
                )

        if machine == 'x86_64':
            return 'linux_x86_64'
        if machine == 'aarch64':
            return 'linux_arm64'
        raise RuntimeError(
            f'make_prefab: unsupported linux machine type:' f' {machine}.'
        )
    raise RuntimeError(
        f'make_prefab: unrecognized platform:' f' {platform.system()}.'
    )


def _vstr(nums: Sequence[int]) -> str:
    return '.'.join(str(i) for i in nums)


def checkenv() -> None:
    """Check for tools necessary to build and run the app."""
    # pylint: disable=too-many-branches
    # pylint: disable=too-many-statements
    # pylint: disable=too-many-locals

    from efrotools import PYTHON_BIN

    print(f'{Clr.BLD}Checking environment...{Clr.RST}', flush=True)

    # Make sure they've got curl.
    if (
        subprocess.run(
            ['which', 'curl'], check=False, capture_output=True
        ).returncode
        != 0
    ):
        raise CleanError(
            'curl is required; please install it via apt, brew, etc.'
        )

    # Make sure they've got rsync.
    if (
        subprocess.run(
            ['which', 'rsync'], check=False, capture_output=True
        ).returncode
        != 0
    ):
        raise CleanError(
            'rsync is required; please install it via apt, brew, etc.'
        )

    # Make sure rsync is version 3.1.0 or newer.
    #
    # Macs come with ancient rsync versions with significant downsides
    # such as single second file mod time resolution which has started
    # to cause problems with build setups. So now am trying to make sure
    # my Macs have an up-to-date one installed (via homebrew).
    rsyncver = tuple(
        int(s)
        for s in subprocess.run(
            ['rsync', '--version'], check=True, capture_output=True
        )
        .stdout.decode()
        .splitlines()[0]
        .split()[2]
        .split('.')[:2]
    )
    if rsyncver < (3, 1):
        raise CleanError(
            'rsync version 3.1 or greater not found;'
            ' please install it via apt, brew, etc.'
        )

    # Make sure they've got our target Python version.
    if (
        subprocess.run(
            ['which', PYTHON_BIN], check=False, capture_output=True
        ).returncode
        != 0
    ):
        raise CleanError(
            f'{PYTHON_BIN} is required; please install it' 'via apt, brew, etc.'
        )

    # Make sure they've got clang-format.
    if (
        subprocess.run(
            ['which', 'clang-format'], check=False, capture_output=True
        ).returncode
        != 0
    ):
        raise CleanError(
            'clang-format is required; please install it via apt, brew, etc.'
        )

    # Make sure they've got pip for that python version.
    if (
        subprocess.run(
            [PYTHON_BIN, '-m', 'pip', '--version'],
            check=False,
            capture_output=True,
        ).returncode
        != 0
    ):
        raise CleanError(
            f'pip (for {PYTHON_BIN}) is required; please install it.'
        )

    # Parse package names and versions from pip.
    piplist = (
        subprocess.run(
            [PYTHON_BIN, '-m', 'pip', 'list'], check=True, capture_output=True
        )
        .stdout.decode()
        .strip()
        .splitlines()
    )
    assert 'Package' in piplist[0] and 'Version' in piplist[0]
    assert '--------' in piplist[1]
    piplist = piplist[2:]
    pipvers: dict[str, list[int]] = {}
    for i, line in enumerate(piplist):
        try:
            pname, pverraw = line.split()[:2]
            pver = [int(x) if x.isdigit() else 0 for x in pverraw.split('.')]
            pipvers[pname] = pver
        except Exception as exc:
            raise RuntimeError(
                f'Error parsing version info from line {i} of:'
                f'\nBEGIN\n{piplist}\nEND'
            ) from exc

    # Check for some required python modules.
    #
    # FIXME: since all of these come from pip now, we should just use
    #  pip --list to check versions on everything instead of doing it
    #  ad-hoc.
    for req in PY_REQUIREMENTS:
        try:
            modname = req.modulename
            minver = req.minversion
            pipname = req.pipname
            if modname is None:
                assert pipname is not None
                if pipname not in pipvers:
                    raise CleanError(
                        f'{pipname} (for {PYTHON_BIN}) is required.\n'
                        f'To install it, try: "{PYTHON_BIN}'
                        f' -m pip install {pipname}"\n'
                        f'Alternately, "tools/pcommand install_pip_reqs"'
                        f' will update all pip requirements.'
                    )
                if minver is not None:
                    vnums = pipvers[pipname]
                    # Seeing a decent number of version lengths fluctuating
                    # (one day [a,b,c,d] and the next [a,b,c])
                    # So let's pad with zeros to match lengths.
                    while len(vnums) < len(minver):
                        vnums.append(0)
                    while len(minver) < len(vnums):
                        minver.append(0)
                    assert len(vnums) == len(
                        minver
                    ), f'unexpected version format for {pipname}: {vnums}'
                    if vnums < minver:
                        raise CleanError(
                            f'{pipname} ver. {_vstr(minver)} or newer'
                            f' is required; found {_vstr(vnums)}.\n'
                            f'To upgrade it, try: "{PYTHON_BIN}'
                            f' -m pip install --upgrade {pipname}".\n'
                            'Alternately, "tools/pcommand install_pip_reqs"'
                            ' will update all pip requirements.'
                        )
            else:
                if pipname is None:
                    pipname = modname
                if minver is not None:
                    results = subprocess.run(
                        f'{PYTHON_BIN} -m {modname} --version',
                        shell=True,
                        check=False,
                        capture_output=True,
                    )
                else:
                    results = subprocess.run(
                        f'{PYTHON_BIN} -c "import {modname}"',
                        shell=True,
                        check=False,
                        capture_output=True,
                    )
                if results.returncode != 0:
                    raise CleanError(
                        f'{pipname} (for {PYTHON_BIN}) is required.\n'
                        f'To install it, try: "{PYTHON_BIN}'
                        f' -m pip install {pipname}"\n'
                        f'Alternately, "tools/pcommand install_pip_reqs"'
                        f' will update all pip requirements.'
                    )
                if minver is not None:
                    # Note: some modules such as pytest print
                    # their version to stderr, so grab both.
                    verlines = (
                        (results.stdout + results.stderr).decode().splitlines()
                    )
                    if verlines[0].startswith('Cpplint fork'):
                        verlines = verlines[1:]
                    ver_line = verlines[0]
                    assert modname in ver_line

                    # Choking on 'mypy 0.xx (compiled: yes)'
                    if '(compiled: ' in ver_line:
                        ver_line = ' '.join(ver_line.split()[:2])
                    try:
                        vnums = [
                            int(x) for x in ver_line.split()[-1].split('.')
                        ]
                    except Exception:
                        print(
                            f'ERROR PARSING VER LINE for {req}:'
                            f' \'{ver_line}\''
                        )
                        raise
                    assert len(vnums) == len(minver)
                    if vnums < minver:
                        raise CleanError(
                            f'{pipname} ver. {_vstr(minver)} or newer'
                            f' is required; found {_vstr(vnums)}.\n'
                            f'To upgrade it, try: "{PYTHON_BIN}'
                            f' -m pip install --upgrade {pipname}".\n'
                            'Alternately, "tools/pcommand install_pip_reqs"'
                            ' will update all pip requirements.'
                        )
        except Exception:
            print(f'ERROR CHECKING PIP REQ \'{req}\'')
            raise

    print(f'{Clr.BLD}Environment ok.{Clr.RST}', flush=True)


def get_pip_reqs() -> list[str]:
    """Return the pip requirements needed to build/run stuff."""
    out: list[str] = []
    for req in PY_REQUIREMENTS:
        name = req.modulename if req.pipname is None else req.pipname
        assert isinstance(name, str)
        out.append(name)
    return out


def _get_server_config_raw_contents(projroot: str) -> str:
    import textwrap

    with open(
        os.path.join(projroot, 'tools/bacommon/servermanager.py'),
        encoding='utf-8',
    ) as infile:
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

    return textwrap.dedent('\n'.join(lines[firstline : lastline + 1]))


def _get_server_config_template_yaml(projroot: str) -> str:
    # pylint: disable=too-many-branches
    import yaml

    lines_in = _get_server_config_raw_contents(projroot).splitlines()
    lines_out: list[str] = []
    ignore_vars = {'stress_test_players'}
    for line in lines_in:
        if any(line.startswith(f'{var}:') for var in ignore_vars):
            continue
        if line.startswith(' '):
            # Ignore indented lines (our few multi-line special cases).
            continue

        if line.startswith(']'):
            # Ignore closing lines (our few multi-line special cases).
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
            before_equal_sign, vval_raw = line.split('=', 1)
            before_equal_sign = before_equal_sign.strip()
            vval_raw = vval_raw.strip()
            vname = before_equal_sign.split()[0]
            assert vname.endswith(':')
            vname = vname[:-1]
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
                vval = 'https://mystatssite.com/showstats?player=${ACCOUNT}'
            elif vname == 'admins':
                vval = ['pb-yOuRAccOuNtIdHErE', 'pb-aNdMayBeAnotherHeRE']
            lines_out += [
                '#' + l for l in yaml.dump({vname: vval}).strip().splitlines()
            ]
        else:
            # Convert comments referring to python bools to yaml bools.
            line = line.replace('True', 'true').replace('False', 'false')
            if '(internal)' not in line:
                lines_out.append(line)
    return '\n'.join(lines_out)


def filter_server_config(projroot: str, infilepath: str) -> str:
    """Add commented-out config options to a server config."""
    with open(infilepath, encoding='utf-8') as infile:
        cfg = infile.read()
    return cfg.replace(
        '# __CONFIG_TEMPLATE_VALUES__',
        _get_server_config_template_yaml(projroot),
    )


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

    entries: list[Entry] = []

    # Start fresh if cmake version changes.
    cmake_ver_output = subprocess.run(
        ['cmake', '--version'], check=True, capture_output=True
    ).stdout.decode()
    cmake_ver = cmake_ver_output.splitlines()[0].split('cmake version ')[1]
    entries.append(Entry('cmake version', cmake_ver))

    # ...or if the actual location of cmake on disk changes.
    cmake_path = os.path.realpath(
        subprocess.run(['which', 'cmake'], check=True, capture_output=True)
        .stdout.decode()
        .strip()
    )
    entries.append(Entry('cmake path', cmake_path))

    # ...or if python's version changes.
    python_ver_output = (
        subprocess.run(
            [f'python{PYVER}', '--version'], check=True, capture_output=True
        )
        .stdout.decode()
        .strip()
    )
    python_ver = python_ver_output.splitlines()[0].split('Python ')[1]
    entries.append(Entry('python_version', python_ver))

    # ...or if the actual location of python on disk changes.
    python_path = os.path.realpath(
        subprocess.run(
            ['which', f'python{PYVER}'], check=True, capture_output=True
        ).stdout.decode()
    )
    entries.append(Entry('python_path', python_path))

    # ...or if mac xcode sdk paths change
    mac_xcode_sdks = (
        ','.join(
            sorted(
                os.listdir(
                    '/Applications/Xcode.app/Contents/'
                    'Developer/Platforms/MacOSX.platform/'
                    'Developer/SDKs/'
                )
            )
        )
        if platform.system() == 'Darwin'
        else ''
    )
    entries.append(Entry('mac_xcode_sdks', mac_xcode_sdks))

    # Ok; do the thing.
    verfilename = os.path.join(dirname, '.ba_cmake_env')
    title = 'cmake_prep_dir'

    versions: dict[str, str]
    if os.path.isfile(verfilename):
        with open(verfilename, encoding='utf-8') as infile:
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
            print(
                f'{Clr.BLU}{entry.name} changed from {previous_value}'
                f' to {entry.current_value}; clearing any existing build at'
                f' "{dirname}".{Clr.RST}'
            )
            changed = True
            break

    if changed:
        if verbose:
            print(
                f'{Clr.BLD}{title}:{Clr.RST} Blowing away existing build dir.'
            )
        subprocess.run(['rm', '-rf', dirname], check=True)
        os.makedirs(dirname, exist_ok=True)
        with open(verfilename, 'w', encoding='utf-8') as outfile:
            outfile.write(
                json.dumps(
                    {entry.name: entry.current_value for entry in entries}
                )
            )
    else:
        if verbose:
            print(f'{Clr.BLD}{title}:{Clr.RST} Keeping existing build dir.')
