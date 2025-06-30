# Released under the MIT License. See LICENSE for details.
#
"""General functionality related to running builds."""

from __future__ import annotations

import os
import sys
import subprocess
from enum import Enum
from pathlib import Path
from dataclasses import dataclass
from typing import TYPE_CHECKING, assert_never

from efro.error import CleanError
from efro.terminal import Clr
from efrotools.lazybuild import LazyBuildContext

if TYPE_CHECKING:
    from typing import Sequence, Any


class PrefabTarget(Enum):
    """Types of prefab builds able to be run."""

    GUI_DEBUG = 'gui-debug'
    SERVER_DEBUG = 'server-debug'
    GUI_RELEASE = 'gui-release'
    SERVER_RELEASE = 'server-release'

    @property
    def buildtype(self) -> str:
        """Return the build type for this target."""
        return self.value.split('-')[0]

    @property
    def buildmode(self) -> str:
        """Return the build mode for this target."""
        return self.value.split('-')[1]


class PrefabPlatform(Enum):
    """Distinct os/cpu-arch/etc. combos we support for prefab builds."""

    MAC_X86_64 = 'mac_x86_64'
    MAC_ARM64 = 'mac_arm64'
    WINDOWS_X86 = 'windows_x86'
    WINDOWS_X86_64 = 'windows_x86_64'
    LINUX_X86_64 = 'linux_x86_64'
    LINUX_ARM64 = 'linux_arm64'

    @classmethod
    def get_current(
        cls, wsl_targets_windows: bool | None = None
    ) -> PrefabPlatform:
        """Get an identifier for the platform running this build.

        Pass a bool `wsl_targets_windows` value to cause WSL to target
        either native Windows (True) or Linux (False). If this value is
        not passed, the env var BA_WSL_TARGETS_WINDOWS is used, and if that
        is not set, the default is False (Linux builds).

        Throws a RuntimeError on unsupported platforms.
        """
        import platform

        if wsl_targets_windows is None:
            wsl_targets_windows = (
                os.environ.get('BA_WSL_TARGETS_WINDOWS', '0') == '1'
            )

        system = platform.system()
        machine = platform.machine()

        if system == 'Darwin':
            if machine == 'x86_64':
                # Had turned these off but flipping them back on for
                # now.
                if bool(False):
                    raise CleanError(
                        'Prefab builds now require an Apple Silicon mac.'
                    )
                return cls.MAC_X86_64
            if machine == 'arm64':
                return cls.MAC_ARM64
            raise RuntimeError(
                f'PrefabPlatform.get_current:'
                f' unsupported mac machine type:'
                f' {machine}.'
            )
        if system == 'Linux':
            # If it looks like we're in Windows Subsystem for Linux, we
            # may want to operate on Windows versions.
            if wsl_targets_windows:
                if 'microsoft' in platform.uname().release.lower():
                    if machine == 'x86_64':
                        # Currently always targeting 64 bit for prefab
                        # stuff.
                        return cls.WINDOWS_X86_64
                    # TODO: add support for arm windows
                    raise RuntimeError(
                        f'make_prefab: unsupported win machine type: {machine}.'
                    )

            if machine == 'x86_64':
                return cls.LINUX_X86_64
            if machine == 'aarch64':
                return cls.LINUX_ARM64
            raise RuntimeError(
                f'PrefabPlatform.get_current:'
                f' unsupported linux machine type:'
                f' {machine}.'
            )
        raise RuntimeError(
            f'PrefabPlatform.get_current:'
            f' unrecognized platform:'
            f' {platform.system()}.'
        )


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
                'src/ballistica/shared/ballistica.h',
                '.efrocachemap',
            ],
            # Our meta Makefile targets generally don't list tools
            # scripts that can affect their creation as sources, so
            # let's set up a catch-all here: when any of our tools stuff
            # changes we'll blow away all existing meta builds.
            #
            # Update: also including featureset-defs here; any time
            # we're mucking with those it's good to start things fresh
            # to be safe.
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
                '.efrocachemap',
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
                '.efrocachemap',
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
                '.efrocachemap',
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
            # buildlockname=category.value,
            srcpaths=[
                'Makefile',
                'tools',
                'src/assets',
                'src/external/python-apple',
                '.efrocachemap',
                # Needed to rebuild on asset-package changes.
                'config/projectconfig.json',
            ],
            # This file won't exist if we are using a dev asset-package,
            # in which case we want to always run so we can ask the
            # server for package updates each time.
            srcpaths_exist=[
                '.cache/asset_package_resolved',
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
                '.efrocachemap',
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


def _vstr(nums: Sequence[int]) -> str:
    return '.'.join(str(i) for i in nums)


def checkenv() -> None:
    """Check for tools necessary to build and run the app."""
    from efrotools.pyver import PYVER

    print(f'{Clr.BLD}Checking environment...{Clr.RST}', flush=True)

    # Make sure they've got cmake.
    #
    # UPDATE - don't want to do this since they might just be using
    # prefab builds, in which case they won't need cmake.
    if bool(False):
        if (
            subprocess.run(
                ['which', 'cmake'], check=False, capture_output=True
            ).returncode
            != 0
        ):
            raise CleanError(
                'cmake is required; please install it via apt, brew, etc.'
            )

    # Make sure they've got zstd (we're starting to use that for various
    # compression purposes).
    if (
        subprocess.run(
            ['which', 'zstd'], check=False, capture_output=True
        ).returncode
        != 0
    ):
        raise CleanError(
            'zstd is required; please install it via apt, brew, etc.'
        )

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

    # Disallow openrsync for now.
    if (
        not subprocess.run(
            ['rsync', '--version'], check=True, capture_output=True
        )
        .stdout.decode()
        .startswith('rsync ')
    ):
        raise CleanError(
            'non-standard rsync detected (openrsync, etc);'
            ' please install regular rsync via apt, brew, etc.'
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

    # Make sure we're running under the Python version the project
    # expects.
    cur_ver = f'{sys.version_info.major}.{sys.version_info.minor}'
    if cur_ver != PYVER:
        raise CleanError(
            f'We expect to be running under Python {PYVER},'
            f' but found {cur_ver}.'
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
            [sys.executable, '-m', 'pip', '--version'],
            check=False,
            capture_output=True,
        ).returncode
        != 0
    ):
        raise CleanError(
            f'pip (for {sys.executable}) is required; please install it.'
        )

    print(f'{Clr.BLD}Environment ok.{Clr.RST}', flush=True)


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


def _get_server_config_template_toml(projroot: str) -> str:
    from tomlkit import document, dumps
    from bacommon.servermanager import ServerConfig

    cfg = ServerConfig()

    # Override some defaults with dummy values we want to display
    # commented out instead.
    cfg.playlist_code = 12345
    cfg.stats_url = 'https://mystatssite.com/showstats?player=${ACCOUNT}'
    cfg.clean_exit_minutes = 60
    cfg.unclean_exit_minutes = 90
    cfg.idle_exit_minutes = 20
    cfg.admins = ['pb-yOuRAccOuNtIdHErE', 'pb-aNdMayBeAnotherHeRE']
    cfg.protocol_version = 35
    cfg.session_max_players_override = 8
    cfg.playlist_inline = []
    cfg.team_names = ('Red', 'Blue')
    cfg.team_colors = ((0.1, 0.25, 1.0), (1.0, 0.25, 0.2))
    cfg.public_ipv4_address = '123.123.123.123'
    cfg.public_ipv6_address = '123A::A123:23A1:A312:12A3:A213:2A13'
    cfg.log_levels = {'ba.lifecycle': 'INFO', 'ba.assets': 'INFO'}

    lines_in = _get_server_config_raw_contents(projroot).splitlines()

    # Convert to double quotes only (we'll convert back at the end).
    # UPDATE: No longer doing this. Turns out single quotes in toml have
    # special meaning (no escapes applied). So we'll stick with doubles.
    # assert all(('"' not in l) for l in lines_in)
    # lines_in = [l.replace("'", '"') for l in lines_in]

    lines_out: list[str] = []
    ignore_vars = {'stress_test_players'}
    for line in lines_in:

        # Replace attr declarations with commented out toml values.
        if line != '' and not line.startswith('#') and ':' in line:
            before_colon, _after_colon = line.split(':', 1)
            vname = before_colon.strip()
            if vname in ignore_vars:
                continue
            vval: Any = getattr(cfg, vname)

            doc = document()
            # Toml doesn't support None/null
            if vval is None:
                raise RuntimeError(
                    f"ServerManager value '{vname}' has value None."
                    f' This is not allowed in toml;'
                    f' please provide a dummy value.'
                )
            assert vval is not None
            doc[vname] = vval
            lines_out += ['#' + l for l in dumps(doc).strip().splitlines()]

        # Preserve blank lines, but only one in a row.
        elif line == '':
            if not lines_out or lines_out[-1] != '':
                lines_out.append(line)

        # Preserve comment lines.
        elif line.startswith('#'):
            # Convert comments referring to python bools to toml bools.
            line = line.replace('True', 'true').replace('False', 'false')

            if '(internal)' not in line:
                lines_out.append(line)

    out = '\n'.join(lines_out)

    # Convert back to single quotes only.
    # UPDATE: Not doing this. See above note.
    # assert "'" not in out
    # out = out.replace('"', "'")

    return out


def filter_server_config_toml(projroot: str, infilepath: str) -> str:
    """Add commented-out config options to a server config."""
    with open(infilepath, encoding='utf-8') as infile:
        cfg = infile.read()
    return cfg.replace(
        '# __CONFIG_TEMPLATE_VALUES__',
        _get_server_config_template_toml(projroot),
    )


def cmake_prep_dir(dirname: str, verbose: bool = False) -> None:
    """Create a dir, recreating it when cmake/python/etc. versions change.

    Useful to prevent builds from breaking when cmake or other components
    are updated.
    """
    # pylint: disable=too-many-locals
    import json

    from efrotools.pyver import PYVER

    @dataclass
    class Entry:
        """Item examined for presence/change."""

        name: str
        current_value: str

    # Start with an entry we can explicitly increment if we want to blow
    # away all cmake builds everywhere (to keep things clean if we
    # rename or move something in the build dir or if we change
    # something cmake doesn't properly handle without a fresh start).
    entries: list[Entry] = [Entry('explicit cmake rebuild', '4')]

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

    # ...or if Python's version changes.
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
    mac_xcode_sdks_dir = (
        '/Applications/Xcode.app/Contents/Developer/Platforms/MacOSX.platform/'
        'Developer/SDKs/'
    )
    mac_xcode_sdks = (
        ','.join(sorted(os.listdir(mac_xcode_sdks_dir)))
        if os.path.isdir(mac_xcode_sdks_dir)
        else ''
    )
    entries.append(Entry('mac_xcode_sdks', mac_xcode_sdks))

    # ...or if homebrew SDL.h resolved path changes (happens for updates)
    sdl_h_path = Path('/opt/homebrew/include/SDL2/SDL.h')
    homebrew_sdl_h_resolved: str = (
        str(sdl_h_path.resolve()) if sdl_h_path.exists() else ''
    )
    entries.append(Entry('homebrew_sdl_h_resolved', homebrew_sdl_h_resolved))

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
