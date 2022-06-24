# Released under the MIT License. See LICENSE for details.
#
"""Functionality related to Xcode on Apple platforms."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
import shlex
from enum import Enum
from typing import TYPE_CHECKING

from efro.terminal import Clr
from efro.error import CleanError
from efro.util import assert_never

if TYPE_CHECKING:
    from typing import Any


class _Section(Enum):
    COMPILEC = 'CompileC'
    MKDIR = 'MkDir'
    LD = 'Ld'
    COMPILEASSETCATALOG = 'CompileAssetCatalog'
    CODESIGN = 'CodeSign'
    COMPILESTORYBOARD = 'CompileStoryboard'
    LINKSTORYBOARDS = 'LinkStoryboards'
    PROCESSINFOPLISTFILE = 'ProcessInfoPlistFile'
    COPYSWIFTLIBS = 'CopySwiftLibs'
    REGISTEREXECUTIONPOLICYEXCEPTION = 'RegisterExecutionPolicyException'
    VALIDATE = 'Validate'
    TOUCH = 'Touch'
    REGISTERWITHLAUNCHSERVICES = 'RegisterWithLaunchServices'
    METALLINK = 'MetalLink'
    COMPILESWIFT = 'CompileSwift'
    CREATEBUILDDIRECTORY = 'CreateBuildDirectory'
    COMPILEMETALFILE = 'CompileMetalFile'
    COPY = 'Copy'
    COPYSTRINGSFILE = 'CopyStringsFile'
    WRITEAUXILIARYFILE = 'WriteAuxiliaryFile'
    COMPILESWIFTSOURCES = 'CompileSwiftSources'
    PROCESSPCH = 'ProcessPCH'
    PROCESSPCHPLUSPLUS = 'ProcessPCH++'
    PHASESCRIPTEXECUTION = 'PhaseScriptExecution'


class XCodeBuild:
    """xcodebuild wrapper with extra bells and whistles."""

    def __init__(self, projroot: str, args: list[str]):
        self._projroot = projroot
        self._args = args
        self._output: list[str] = []
        self._verbose = os.environ.get('XCODEBUILDVERBOSE', '0') == '1'
        self._section: _Section | None = None
        self._section_line_count = 0
        self._returncode: int | None = None
        self._project: str = self._argstr(args, '-project')
        self._scheme: str = self._argstr(args, '-scheme')
        self._configuration: str = self._argstr(args, '-configuration')

    def run(self) -> None:
        """Do the thing."""
        self._run_cmd(self._build_cmd_args())
        assert self._returncode is not None

        # In some failure cases we may want to run a clean and try again.
        if self._returncode != 0:

            # Getting this error sometimes after xcode updates.
            if 'error: PCH file built from a different branch' in '\n'.join(
                    self._output):
                print(f'{Clr.MAG}WILL CLEAN AND'
                      f' RE-ATTEMPT XCODE BUILD{Clr.RST}')
                self._run_cmd([
                    'xcodebuild', '-project', self._project, '-scheme',
                    self._scheme, '-configuration', self._configuration,
                    'clean'
                ])
                # Now re-run the original build.
                print(f'{Clr.MAG}RE-ATTEMPTING XCODE BUILD'
                      f' AFTER CLEAN{Clr.RST}')
                self._run_cmd(self._build_cmd_args())

        if self._returncode != 0:
            raise CleanError(f'Command failed with code {self._returncode}.')

    @staticmethod
    def _argstr(args: list[str], flag: str) -> str:
        try:
            return args[args.index(flag) + 1]
        except (ValueError, IndexError) as exc:
            raise RuntimeError(f'{flag} value not found') from exc

    def _build_cmd_args(self) -> list[str]:
        return ['xcodebuild'] + self._args

    def _run_cmd(self, cmd: list[str]) -> None:
        # reset some state
        self._output = []
        self._section = None
        self._returncode = 0
        print(f'{Clr.BLU}Running build: {Clr.BLD}{cmd}{Clr.RST}')
        with subprocess.Popen(cmd,
                              stdout=subprocess.PIPE,
                              stderr=subprocess.STDOUT) as proc:
            if proc.stdout is None:
                raise RuntimeError('Error running command')
            while True:
                line = proc.stdout.readline().decode()
                if len(line) == 0:
                    break
                self._output.append(line)
                self._print_filtered_line(line)
            proc.wait()
            self._returncode = proc.returncode

    def _print_filtered_line(self, line: str) -> None:

        # pylint: disable=too-many-branches
        # pylint: disable=too-many-statements

        # NOTE: xcodebuild output can be coming from multiple tasks and
        # intermingled, so lets try to be as conservative as possible when
        # hiding lines. When we're not 100% sure we know what a line is,
        # we should print it to be sure.

        if self._verbose:
            sys.stdout.write(line)
            return

        # Look for a few special cases regardless of the section we're in:
        if line == '** BUILD SUCCEEDED **\n':
            sys.stdout.write(
                f'{Clr.GRN}{Clr.BLD}XCODE BUILD SUCCEEDED{Clr.RST}\n')
            return

        if line == '** CLEAN SUCCEEDED **\n':
            sys.stdout.write(
                f'{Clr.GRN}{Clr.BLD}XCODE CLEAN SUCCEEDED{Clr.RST}\n')
            return

        if 'warning: OpenGL is deprecated.' in line:
            return  # yes Apple, I know.

        # xcodebuild output generally consists of some high level command
        # ('CompileC blah blah blah') followed by a number of related lines.
        # Look for particular high level commands to switch us into different
        # modes.
        sectionchanged = False
        for section in _Section:
            if line.startswith(f'{section.value} '):
                self._section = section
                sectionchanged = True

        if sectionchanged:
            self._section_line_count = 0
        else:
            self._section_line_count += 1

        # There's a lot of random chatter at the start of builds,
        # so let's go ahead and ignore everything before we've got a
        # line-mode set.
        if self._section is None:
            return
        if self._section is _Section.COMPILEC:
            self._print_compilec_line(line)
        elif self._section is _Section.MKDIR:
            self._print_mkdir_line(line)
        elif self._section is _Section.LD:
            self._print_ld_line(line)
        elif self._section is _Section.COMPILEASSETCATALOG:
            self._print_compile_asset_catalog_line(line)
        elif self._section is _Section.CODESIGN:
            self._print_code_sign_line(line)
        elif self._section is _Section.COMPILESTORYBOARD:
            self._print_compile_storyboard_line(line)
        elif self._section is _Section.LINKSTORYBOARDS:
            self._print_simple_section_line(
                line, ignore_line_start_tails=['/ibtool'])
        elif self._section is _Section.PROCESSINFOPLISTFILE:
            self._print_process_info_plist_file_line(line)
        elif self._section is _Section.COPYSWIFTLIBS:
            self._print_simple_section_line(
                line, ignore_line_starts=['builtin-swiftStdLibTool'])
        elif self._section is _Section.REGISTEREXECUTIONPOLICYEXCEPTION:
            self._print_simple_section_line(
                line,
                ignore_line_starts=[
                    'builtin-RegisterExecutionPolicyException'
                ])
        elif self._section is _Section.VALIDATE:
            self._print_simple_section_line(
                line, ignore_line_starts=['builtin-validationUtility'])
        elif self._section is _Section.TOUCH:
            self._print_simple_section_line(
                line, ignore_line_starts=['/usr/bin/touch'])
        elif self._section is _Section.REGISTERWITHLAUNCHSERVICES:
            self._print_simple_section_line(
                line, ignore_line_start_tails=['lsregister'])
        elif self._section is _Section.METALLINK:
            self._print_simple_section_line(line,
                                            prefix='Linking',
                                            ignore_line_start_tails=['/metal'])
        elif self._section is _Section.COMPILESWIFT:
            self._print_simple_section_line(
                line,
                prefix='Compiling',
                prefix_index=3,
                ignore_line_start_tails=['/swift-frontend', 'EmitSwiftModule'])
        elif self._section is _Section.CREATEBUILDDIRECTORY:
            self._print_simple_section_line(
                line, ignore_line_starts=['builtin-create-build-directory'])
        elif self._section is _Section.COMPILEMETALFILE:
            self._print_simple_section_line(line,
                                            prefix='Metal-Compiling',
                                            ignore_line_start_tails=['/metal'])
        elif self._section is _Section.COPY:
            self._print_simple_section_line(
                line, ignore_line_starts=['builtin-copy'])
        elif self._section is _Section.COPYSTRINGSFILE:
            self._print_simple_section_line(line,
                                            ignore_line_starts=[
                                                'builtin-copyStrings',
                                                'CopyPNGFile',
                                                'ConvertIconsetFile'
                                            ],
                                            ignore_line_start_tails=[
                                                '/InfoPlist.strings:1:1:',
                                                '/copypng', '/iconutil'
                                            ])
        elif self._section is _Section.WRITEAUXILIARYFILE:
            # EW: this spits out our full list of entitlements line by line.
            # We should make this smart enough to ignore that whole section
            # but just ignoring specific exact lines for now.
            self._print_simple_section_line(
                line,
                ignore_line_starts=[
                    'PhaseScriptExecution',
                    '/bin/sh -c',
                    'write-file',
                    'builtin-productPackagingUtility',
                    'ProcessProductPackaging',
                    'Entitlements:',
                    '{',
                    '}',
                    ');',
                    '};',
                    '"com.apple.security.get-task-allow"'
                    '"com.apple.security.app-sandbox"',
                    '"com.apple.Music"',
                    '"com.apple.Music.library.read"',
                    '"com.apple.Music.playback"',
                    '"com.apple.security.app-sandbox"',
                    '"com.apple.security.automation.apple-events"',
                    '"com.apple.security.device.bluetooth"',
                    '"com.apple.security.device.usb"',
                    '"com.apple.security.get-task-allow"',
                    '"com.apple.security.network.client"',
                    '"com.apple.security.network.server"',
                    '"com.apple.security.scripting-targets"',
                    '"com.apple.Music.library.read",',
                ])
        elif self._section is _Section.COMPILESWIFTSOURCES:
            self._print_simple_section_line(
                line,
                prefix='Compiling Swift Sources',
                prefix_index=None,
                ignore_line_starts=['PrecompileSwiftBridgingHeader'],
                ignore_line_start_tails=['/swiftc', '/swift-frontend'])
        elif self._section is _Section.PROCESSPCH:
            self._print_simple_section_line(
                line,
                ignore_line_starts=['Precompile of'],
                ignore_line_start_tails=['/clang'])
        elif self._section is _Section.PROCESSPCHPLUSPLUS:
            self._print_simple_section_line(
                line,
                ignore_line_starts=['Precompile of'],
                ignore_line_start_tails=['/clang'])
        elif self._section is _Section.PHASESCRIPTEXECUTION:
            self._print_simple_section_line(line,
                                            prefix='Running Script',
                                            ignore_line_starts=['/bin/sh'])
        else:
            assert_never(self._section)

    def _print_compilec_line(self, line: str) -> None:

        # First line of the section.
        if self._section_line_count == 0:
            fname = os.path.basename(shlex.split(line)[2])
            sys.stdout.write(f'{Clr.BLU}Compiling {Clr.BLD}{fname}{Clr.RST}\n')
            return

        # Ignore empty lines or things we expect to be there.
        splits = line.split()
        if not splits:
            return
        if splits[0] in ['cd', 'export']:
            return
        if splits[0].endswith('/clang'):
            return

        # Fall back on printing anything we don't recognize.
        sys.stdout.write(line)

    def _print_mkdir_line(self, line: str) -> None:

        # First line of the section.
        if self._section_line_count == 0:
            return

        # Ignore empty lines or things we expect to be there.
        splits = line.split()
        if not splits:
            return
        if splits[0] in ['cd', '/bin/mkdir']:
            return

        # Fall back on printing anything we don't recognize.
        sys.stdout.write(line)

    def _print_ld_line(self, line: str) -> None:

        # First line of the section.
        if self._section_line_count == 0:
            name = os.path.basename(shlex.split(line)[1])
            sys.stdout.write(f'{Clr.BLU}Linking {Clr.BLD}{name}{Clr.RST}\n')
            return

        # Ignore empty lines or things we expect to be there.
        splits = line.split()
        if not splits:
            return
        if splits[0] in ['cd']:
            return
        if splits[0].endswith('/clang++'):
            return

        # Fall back on printing anything we don't recognize.
        sys.stdout.write(line)

    def _print_compile_asset_catalog_line(self, line: str) -> None:
        # pylint: disable=too-many-return-statements

        # First line of the section.
        if self._section_line_count == 0:
            name = os.path.basename(shlex.split(line)[1])
            sys.stdout.write(
                f'{Clr.BLU}Compiling Asset Catalog {Clr.BLD}{name}{Clr.RST}\n')
            return

        # Ignore empty lines or things we expect to be there.
        line_s = line.strip()
        splits = line.split()
        if not splits:
            return
        if splits[0] in ['cd']:
            return
        if splits[0].endswith('/actool'):
            return
        if line_s == '/* com.apple.actool.compilation-results */':
            return
        if (' ibtoold[' in line_s
                and 'NSFileCoordinator is doing nothing' in line_s):
            return
        if any(line_s.endswith(x) for x in ('.plist', '.icns', '.car')):
            return

        # Fall back on printing anything we don't recognize.
        sys.stdout.write(line)

    def _print_compile_storyboard_line(self, line: str) -> None:

        # First line of the section.
        if self._section_line_count == 0:
            name = os.path.basename(shlex.split(line)[1])
            sys.stdout.write(
                f'{Clr.BLU}Compiling Storyboard {Clr.BLD}{name}{Clr.RST}\n')
            return

        # Ignore empty lines or things we expect to be there.
        splits = line.split()
        if not splits:
            return
        if splits[0] in ['cd', 'export']:
            return
        if splits[0].endswith('/ibtool'):
            return

        # Fall back on printing anything we don't recognize.
        sys.stdout.write(line)

    def _print_code_sign_line(self, line: str) -> None:

        # First line of the section.
        if self._section_line_count == 0:
            name = os.path.basename(shlex.split(line)[1])
            sys.stdout.write(f'{Clr.BLU}Signing'
                             f' {Clr.BLD}{name}{Clr.RST}\n')
            return

        # Ignore empty lines or things we expect to be there.
        splits = line.split()
        if not splits:
            return
        if splits[0] in ['cd', 'export', '/usr/bin/codesign']:
            return
        if line.strip().startswith('Signing Identity:'):
            return
        if ': replacing existing signature' in line:
            return

        # Fall back on printing anything we don't recognize.
        sys.stdout.write(line)

    def _print_process_info_plist_file_line(self, line: str) -> None:

        # First line of the section.
        if self._section_line_count == 0:
            name = os.path.basename(shlex.split(line)[1])
            sys.stdout.write(f'{Clr.BLU}Processing {Clr.BLD}{name}{Clr.RST}\n')
            return

        # Ignore empty lines or things we expect to be there.
        splits = line.split()
        if not splits:
            return
        if splits[0] in ['cd', 'export', 'builtin-infoPlistUtility']:
            return

        # Fall back on printing anything we don't recognize.
        sys.stdout.write(line)

    def _print_simple_section_line(
            self,
            line: str,
            prefix: str = None,
            prefix_index: int | None = 1,
            ignore_line_starts: list[str] = None,
            ignore_line_start_tails: list[str] = None) -> None:

        if ignore_line_starts is None:
            ignore_line_starts = []
        if ignore_line_start_tails is None:
            ignore_line_start_tails = []

        # First line of the section.
        if self._section_line_count == 0:
            if prefix is not None:
                if prefix_index is None:
                    sys.stdout.write(f'{Clr.BLU}{prefix}{Clr.RST}\n')
                else:
                    name = os.path.basename(shlex.split(line)[prefix_index])
                    sys.stdout.write(f'{Clr.BLU}{prefix}'
                                     f' {Clr.BLD}{name}{Clr.RST}\n')
            return

        # Ignore empty lines or things we expect to be there.
        splits = line.split()
        if not splits:
            return
        for start in ['cd', 'export'] + ignore_line_starts:
            # The start strings they pass may themselves be splittable so
            # we may need to compare more than one string.
            startsplits = start.split()
            if splits[:len(startsplits)] == startsplits:
                return
        if any(splits[0].endswith(tail) for tail in ignore_line_start_tails):
            return

        # Fall back on printing anything we don't recognize.
        if prefix is None:
            # If a prefix was not supplied for this section, the user will
            # have no way to know what this output relates to. Tack a bit
            # on to clarify in that case.
            assert self._section is not None
            sys.stdout.write(f'{Clr.YLW}Unexpected {self._section.value}'
                             f' Output:{Clr.RST} {line}')
        else:
            sys.stdout.write(line)


def project_build_path(projroot: str, project_path: str, scheme: str,
                       configuration: str) -> str:
    """Get build paths for an xcode project (cached for efficiency)."""
    # pylint: disable=too-many-locals

    config_path = os.path.join(projroot, '.cache', 'xcode_build_path')
    config: dict[str, dict[str, Any]] = {}

    build_dir: str | None = None
    executable_path: str | None = None

    if os.path.exists(config_path):
        with open(config_path, encoding='utf-8') as infile:
            config = json.loads(infile.read())
        if (project_path in config and configuration in config[project_path]
                and scheme in config[project_path][configuration]):

            # Ok we've found a build-dir entry for this project; now if it
            # exists on disk and all timestamps within it are decently
            # close to the one we've got recorded, lets use it.
            # (Anything using this script should also be building
            # stuff there so mod times should be pretty recent; if not
            # then its worth re-caching to be sure.)
            cached_build_dir = config[project_path][configuration][scheme][
                'build_dir']
            cached_timestamp = config[project_path][configuration][scheme][
                'timestamp']
            cached_executable_path = config[project_path][configuration][
                scheme]['executable_path']
            assert isinstance(cached_build_dir, str)
            assert isinstance(cached_timestamp, float)
            assert isinstance(cached_executable_path, str)
            now = time.time()
            if (os.path.isdir(cached_build_dir)
                    and abs(now - cached_timestamp) < 60 * 60 * 24):
                build_dir = cached_build_dir
                executable_path = cached_executable_path

    # If we don't have a path at this point we look it up and cache it.
    if build_dir is None:
        print('Caching xcode build path...', file=sys.stderr)
        cmd = [
            'xcodebuild', '-project', project_path, '-showBuildSettings',
            '-configuration', configuration, '-scheme', scheme
        ]
        output = subprocess.run(cmd, check=True,
                                capture_output=True).stdout.decode()

        prefix = 'TARGET_BUILD_DIR = '
        lines = [
            l for l in output.splitlines() if l.strip().startswith(prefix)
        ]
        if len(lines) != 1:
            raise Exception(
                'TARGET_BUILD_DIR not found in xcodebuild settings output')
        build_dir = lines[0].replace(prefix, '').strip()

        prefix = 'EXECUTABLE_PATH = '
        lines = [
            l for l in output.splitlines() if l.strip().startswith(prefix)
        ]
        if len(lines) != 1:
            raise Exception(
                'EXECUTABLE_PATH not found in xcodebuild settings output')
        executable_path = lines[0].replace(prefix, '').strip()

        if project_path not in config:
            config[project_path] = {}
        if configuration not in config[project_path]:
            config[project_path][configuration] = {}
        config[project_path][configuration][scheme] = {
            'build_dir': build_dir,
            'executable_path': executable_path,
            'timestamp': time.time()
        }
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        with open(config_path, 'w', encoding='utf-8') as outfile:
            outfile.write(json.dumps(config))

    assert build_dir is not None
    assert executable_path is not None
    return os.path.join(build_dir, executable_path)
