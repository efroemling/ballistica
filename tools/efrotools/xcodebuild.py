# Released under the MIT License. See LICENSE for details.
#
"""Functionality related to Xcode on Apple platforms."""
# pylint: disable=too-many-lines
from __future__ import annotations

import json
import os
import sys
import time
import shlex
import logging
import tempfile
import subprocess
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, assert_never
from dataclasses import dataclass

from filelock import FileLock

from efro.terminal import Clr
from efro.error import CleanError
from efro.dataclassio import ioprepped, dataclass_from_dict
from efrotools import getlocalconfig  # pylint: disable=wrong-import-order

if TYPE_CHECKING:
    from typing import Any


@ioprepped
@dataclass
class SigningConfig:
    """Info about signing."""

    certfile: str
    certpass: str


# HOW THIS WORKS:

# Basically we scan line beginnings for the following words followed by
# spaces. When we find one, we switch our section to that until a different
# section header is found. We then call parse/print functions with new lines
# depending on the current section.

# Section line parsing/printing is generally blacklist based; if we recognize
# a line is not needed we can ignore it. We generally look for specific
# strings or string-endings in a line to do this. We want to be sure to print
# anything we don't recognize to avoid hiding important output.

# I'm sure this system isn't 100% accurate with threads spitting out
# overlapping output and whatnot, but it hopefully works 'well enough'.


class _Section(Enum):
    COMPILEC = 'CompileC'
    COMPILEXCSTRINGS = 'CompileXCStrings'
    SWIFTCOMPILE = 'SwiftCompile'
    SWIFTGENERATEPCH = 'SwiftGeneratePch'
    SWIFTDRIVER = 'SwiftDriver'
    SWIFTDRIVERJOBDISCOVERY = 'SwiftDriverJobDiscovery'
    SWIFTEMITMODULE = 'SwiftEmitModule'
    COMPILESWIFT = 'CompileSwift'
    MKDIR = 'MkDir'
    LD = 'Ld'
    CPRESOURCE = 'CpResource'
    COMPILEASSETCATALOG = 'CompileAssetCatalog'
    CODESIGN = 'CodeSign'
    COMPILESTORYBOARD = 'CompileStoryboard'
    CONVERTICONSETFILE = 'ConvertIconsetFile'
    LINKSTORYBOARDS = 'LinkStoryboards'
    PROCESSINFOPLISTFILE = 'ProcessInfoPlistFile'
    COPYSWIFTLIBS = 'CopySwiftLibs'
    REGISTEREXECUTIONPOLICYEXCEPTION = 'RegisterExecutionPolicyException'
    VALIDATE = 'Validate'
    TOUCH = 'Touch'
    REGISTERWITHLAUNCHSERVICES = 'RegisterWithLaunchServices'
    METALLINK = 'MetalLink'
    CREATEBUILDDIRECTORY = 'CreateBuildDirectory'
    COMPILEMETALFILE = 'CompileMetalFile'
    COPY = 'Copy'
    COPYSTRINGSFILE = 'CopyStringsFile'
    WRITEAUXILIARYFILE = 'WriteAuxiliaryFile'
    COMPILESWIFTSOURCES = 'CompileSwiftSources'
    PROCESSPCH = 'ProcessPCH'
    PROCESSPCHPLUSPLUS = 'ProcessPCH++'
    PHASESCRIPTEXECUTION = 'PhaseScriptExecution'
    PROCESSPRODUCTPACKAGING = 'ProcessProductPackaging'
    PROCESSPRODUCTPACKAGINGDER = 'ProcessProductPackagingDER'
    CLANGSTATCACHE = 'ClangStatCache'
    EXTRACTAPPINTENTSMETADATA = 'ExtractAppIntentsMetadata'
    SWIFTMERGEGENERATEDHEADERS = 'SwiftMergeGeneratedHeaders'
    GENERATEDSYMFILE = 'GenerateDSYMFile'
    GENERATEASSETSYMBOLS = 'GenerateAssetSymbols'


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
        self._project: str | None = (
            self._argstr(args, '-project') if '-project' in args else None
        )
        self._scheme: str | None = (
            self._argstr(args, '-scheme') if '-scheme' in args else None
        )
        self._configuration: str | None = (
            self._argstr(args, '-configuration')
            if '-configuration' in args
            else None
        )

        # Use random name for temp keychains to hopefully avoid collisions
        # and make snooping harder.
        self._keychain_name = f'build{os.urandom(8).hex()}.keychain'
        self._keychain_pass = os.urandom(16).hex()

        self._signingconfigname: str | None = None
        self._signingconfig: SigningConfig | None = None
        if '-baSigningConfig' in args:
            self._signingconfigname = self._argstr(
                args, '-baSigningConfig', remove=True
            )

            lconfig = getlocalconfig(projroot=Path(projroot))
            if self._signingconfigname not in lconfig.get(
                'apple_signing_configs', {}
            ):
                raise CleanError(
                    f"Error: Signing-config '{self._signingconfigname}'"
                    ' is not present in localconfig.'
                )
            try:
                self._signingconfig = dataclass_from_dict(
                    SigningConfig,
                    lconfig['apple_signing_configs'][self._signingconfigname],
                )
                if not os.path.exists(self._signingconfig.certfile):
                    raise RuntimeError(
                        f'Certfile not found at'
                        f" '{self._signingconfig.certfile}'."
                    )
            except Exception:
                logging.exception(
                    "Error loading signing-config '%s'.",
                    self._signingconfigname,
                )

    def run(self) -> None:
        """Do the thing."""

        # Ok here's the deal:
        # First I tried creating file-locks only while creating or destroying
        # temp keychains that we use for builds, but I'm still seeing random
        # code signing failures when 2 builds overlap.
        # So now I'm going with a single lock that is held throughout the
        # entire build when code signing is involved. We'll see if that works.
        # If that seems to slow things down too much we can try something in
        # the middle such as enforcing a cooldown period after making keychain
        # changes or something like that.

        # Go with a lock for the full build duration only if there's signing
        # involved.
        if self._signingconfig is not None:
            wait_start_time = time.monotonic()
            print('Waiting for xcode build lock...', flush=True)
            with self._get_build_file_lock():
                wait_time = time.monotonic() - wait_start_time
                print(
                    f'Xcode build lock acquired in {wait_time:.2f} seconds.',
                    flush=True,
                )
                self._run()
        else:
            self._run()

    def _run(self) -> None:
        self._set_up_keychain()

        try:
            self._run_cmd(self._build_cmd_args())
            assert self._returncode is not None

            # In some failure cases we may want to run a clean and try again.
            if self._returncode != 0:
                # Getting this error sometimes after xcode updates.
                if (
                    'error: PCH file built from a different branch'
                    in '\n'.join(self._output)
                ):
                    # Assume these were all passed for the build that just
                    # failed.
                    assert self._project is not None
                    assert self._scheme is not None
                    assert self._configuration is not None
                    print(
                        f'{Clr.MAG}WILL CLEAN AND'
                        f' RE-ATTEMPT XCODE BUILD{Clr.RST}'
                    )
                    self._run_cmd(
                        [
                            'xcodebuild',
                            '-project',
                            self._project,
                            '-scheme',
                            self._scheme,
                            '-configuration',
                            self._configuration,
                            'clean',
                        ]
                    )
                    # Now re-run the original build.
                    print(
                        f'{Clr.MAG}RE-ATTEMPTING XCODE BUILD'
                        f' AFTER CLEAN{Clr.RST}'
                    )
                    self._run_cmd(self._build_cmd_args())

            if self._returncode != 0:
                raise CleanError(
                    f'Command failed with code {self._returncode}.'
                )
        finally:
            self._tear_down_keychain()

    def _get_keychain_file_lock(self) -> FileLock:
        """Return a lock that we hold while mucking with keychain stuff."""
        path = os.path.join(tempfile.gettempdir(), 'ba_xc_keychain_lock')
        return FileLock(path)

    def _get_build_file_lock(self) -> FileLock:
        """Return a lock that we hold for an entire build."""
        path = os.path.join(tempfile.gettempdir(), 'ba_xc_build_lock')
        return FileLock(path)

    def _set_up_keychain(self) -> None:
        # If we're specifying a signing configuration, this sets it up
        # via a temporary keychain.
        # As seen in https://github.com/Apple-Actions/import-codesign-certs
        # And similarly https://xcodebuild.tips/pages/certificates-and-keys/
        if self._signingconfig is None:
            return

        # We're mucking with keychain settings here which is a global thing.
        # Let's try to at least avoid two of us mucking with it at once.
        assert self._signingconfigname is not None
        with self._get_keychain_file_lock():
            print(f"Setting up signing-config '{self._signingconfigname}'...")

            # Create a new temp keychain.
            subprocess.run(
                [
                    'security',
                    'create-keychain',
                    '-p',
                    self._keychain_pass,
                    self._keychain_name,
                ],
                check=True,
                capture_output=True,
            )
            # Grab list of current keychains.
            keychains = [
                line.strip().replace('"', '')
                for line in subprocess.run(
                    ['security', 'list-keychains', '-d', 'user'],
                    check=True,
                    capture_output=True,
                )
                .stdout.decode()
                .splitlines()
            ]
            # Warn if we're seeing keychain leaks/etc.
            if len(keychains) != 1:
                print(
                    f'{Clr.RED}Expected to initially find 1 keychain;'
                    f' got {keychains}{Clr.RST}'
                )
            assert all(os.path.exists(p) for p in keychains)

            keychains.insert(0, self._keychain_name)
            subprocess.run(
                ['security', 'list-keychains', '-d', 'user', '-s'] + keychains,
                check=True,
            )
            subprocess.run(
                [
                    'security',
                    'unlock-keychain',
                    '-p',
                    self._keychain_pass,
                    self._keychain_name,
                ],
                check=True,
                capture_output=True,
            )
            subprocess.run(
                [
                    'security',
                    'import',
                    self._signingconfig.certfile,
                    '-k',
                    self._keychain_name,
                    '-f',
                    'pkcs12',
                    '-A',
                    '-T',
                    '/usr/bin/codesign',
                    '-T',
                    '/usr/bin/security',
                    '-P',
                    self._signingconfig.certpass,
                ],
                check=True,
                capture_output=True,
            )
            subprocess.run(
                [
                    'security',
                    'set-key-partition-list',
                    '-S',
                    'apple-tool:,apple:',
                    '-k',
                    self._keychain_pass,
                    self._keychain_name,
                ],
                check=True,
                capture_output=True,
            )

    def _tear_down_keychain(self) -> None:
        if self._signingconfig is None:
            return

        # We're mucking with keychain settings here which is a global thing.
        # Let's try to at least avoid two of us mucking with it at once.
        with self._get_keychain_file_lock():
            print('Tearing down signing-config...')

            # Grab list of current keychains.
            keychains = [
                line.strip().replace('"', '')
                for line in subprocess.run(
                    ['security', 'list-keychains', '-d', 'user'],
                    check=True,
                    capture_output=True,
                )
                .stdout.decode()
                .splitlines()
            ]

            # Strip out ours.
            keychains = [k for k in keychains if self._keychain_name not in k]

            # Warn if this doesn't put us back to the default 1.
            if len(keychains) != 1:
                print(
                    f'{Clr.RED}Expected to restore to 1 keychain;'
                    f' got {keychains}{Clr.RST}'
                )
            subprocess.run(
                ['security', 'list-keychains', '-d', 'user', '-s'] + keychains,
                check=True,
                capture_output=True,
            )
            subprocess.run(
                ['security', 'delete-keychain', self._keychain_name],
                check=True,
                capture_output=True,
            )

    @staticmethod
    def _argstr(args: list[str], flag: str, remove: bool = False) -> str:
        try:
            flagindex = args.index(flag)
            val = args[flagindex + 1]
            if remove:
                del args[flagindex : flagindex + 2]
            return val
        except (ValueError, IndexError) as exc:
            raise RuntimeError(f'{flag} value not found') from exc

    def _build_cmd_args(self) -> list[str]:
        return ['xcodebuild'] + self._args

    def _run_cmd(self, cmd: list[str]) -> None:
        # reset some state
        self._output = []
        self._section = None
        self._returncode = 0
        print(f'{Clr.BLU}Running build: {Clr.BLD}{cmd}{Clr.RST}', flush=True)
        with subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT
        ) as proc:
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
        # pylint: disable=too-many-return-statements

        # NOTE: xcodebuild output can be coming from multiple tasks and
        # intermingled, so lets try to be as conservative as possible when
        # hiding lines. When we're not 100% sure we know what a line is,
        # we should print it to be sure.

        if self._verbose:
            sys.stdout.write(line)
            sys.stdout.flush()
            return

        # Look for a few special cases regardless of the section we're in:
        if line == '** BUILD SUCCEEDED **\n':
            sys.stdout.write(
                f'{Clr.GRN}{Clr.BLD}XCODE BUILD SUCCEEDED{Clr.RST}\n'
            )
            sys.stdout.flush()
            return

        if line == '** CLEAN SUCCEEDED **\n':
            sys.stdout.write(
                f'{Clr.GRN}{Clr.BLD}XCODE CLEAN SUCCEEDED{Clr.RST}\n'
            )
            sys.stdout.flush()
            return

        # Seeing these popping up in the middle of other stuff a lot.
        if any(
            line.startswith(x)
            for x in [
                'SwiftDriver\\ Compilation\\ Requirements ',
                'SwiftDriver\\ Compilation ',
            ]
        ):
            return
        lsplits = line.split()
        if lsplits and lsplits[0] in ['builtin-Swift-Compilation']:
            return

        # If they're warning us about build phases running every time,
        # spit out a simplified warning.
        before = "Run script build phase '"
        after = "' will be run during every build because"
        if before in line and after in line:
            phasename = line.split(before)[-1].split(after)[0]
            sys.stdout.write(
                f"{Clr.WHT}Warning: build phase '{phasename}'"
                f' is running every time (no deps set up).{Clr.RST}\n'
            )
            return

        warnstr = 'warning: The Copy Bundle Resources build phase contains'
        if warnstr in line:
            warnstr2 = line[line.index(warnstr) :].replace(
                'warning: ', 'Warning: '
            )
            sys.stdout.write(f'{Clr.WHT}{warnstr2}{Clr.RST}')
            return

        # if 'warning: OpenGL is deprecated.' in line:
        #    return  # yes Apple, I know.

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
        elif self._section is _Section.SWIFTCOMPILE:
            self._print_swift_compile_line(line)
        elif self._section is _Section.SWIFTMERGEGENERATEDHEADERS:
            self._print_simple_section_line(
                line, ignore_line_starts=['builtin-swiftHeaderTool']
            )
        elif self._section is _Section.SWIFTDRIVER:
            self._print_simple_section_line(
                line,
                ignore_line_starts=[
                    'builtin-SwiftDriver',
                    'builtin-Swift-Compilation',
                ],
            )
        elif self._section is _Section.SWIFTEMITMODULE:
            self._print_simple_section_line(
                line,
                ignore_line_starts=[
                    'builtin-SwiftDriver',
                    'builtin-swiftTaskExecution',
                ],
            )
        elif self._section is _Section.SWIFTGENERATEPCH:
            self._print_simple_section_line(
                line,
                ignore_line_starts=['builtin-swiftTaskExecution'],
                prefix_unexpected=False,
            )
        elif self._section is _Section.GENERATEDSYMFILE:
            self._print_simple_section_line(
                line,
                prefix='Generating DSYM File',
                ignore_line_start_tails=['/dsymutil'],
            )
        elif self._section is _Section.SWIFTDRIVERJOBDISCOVERY:
            self._print_simple_section_line(
                line,
                ignore_line_starts=[
                    'builtin-Swift-Compilation-Requirements',
                    'builtin-Swift-Compilation',
                    'builtin-swiftTaskExecution',
                ],
            )
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
                line, ignore_line_start_tails=['/ibtool']
            )
        elif self._section is _Section.CPRESOURCE:
            self._print_simple_section_line(
                line, ignore_line_starts=['builtin-copy']
            )
        elif self._section is _Section.PROCESSINFOPLISTFILE:
            self._print_process_info_plist_file_line(line)
        elif self._section is _Section.COPYSWIFTLIBS:
            self._print_simple_section_line(
                line,
                ignore_line_starts=['builtin-swiftStdLibTool'],
            )
        elif self._section is _Section.REGISTEREXECUTIONPOLICYEXCEPTION:
            self._print_simple_section_line(
                line,
                ignore_line_starts=['builtin-RegisterExecutionPolicyException'],
            )
        elif self._section is _Section.VALIDATE:
            self._print_simple_section_line(
                line,
                ignore_line_starts=['builtin-validationUtility'],
            )
        elif self._section is _Section.COMPILEXCSTRINGS:
            self._print_simple_section_line(
                line,
                prefix='Compiling strings',
                ignore_line_start_tails=['/xcstringstool'],
            )
        elif self._section is _Section.CONVERTICONSETFILE:
            self._print_simple_section_line(
                line,
                prefix='Creating',
                prefix_index=1,
                ignore_line_start_tails=['/iconutil'],
            )
        elif self._section is _Section.TOUCH:
            self._print_simple_section_line(
                line,
                ignore_line_starts=['/usr/bin/touch'],
            )
        elif self._section is _Section.REGISTERWITHLAUNCHSERVICES:
            self._print_simple_section_line(
                line, ignore_line_start_tails=['lsregister']
            )
        elif self._section is _Section.METALLINK:
            self._print_simple_section_line(
                line,
                prefix='Linking',
                prefix_index=1,
                ignore_line_start_tails=['/metal'],
            )
        # I think this is outdated and can go away?...
        elif self._section is _Section.COMPILESWIFT:
            self._print_simple_section_line(
                line,
                prefix='Compiling',
                prefix_index=3,
                ignore_line_start_tails=[
                    '/swift-frontend',
                    'EmitSwiftModule',
                ],
            )
        elif self._section is _Section.CREATEBUILDDIRECTORY:
            self._print_simple_section_line(
                line,
                ignore_line_starts=['builtin-create-build-directory'],
                ignore_line_start_tails=['/clang-stat-cache'],
            )
        elif self._section is _Section.COMPILEMETALFILE:
            self._print_simple_section_line(
                line,
                prefix='Metal-Compiling',
                prefix_index=1,
                ignore_line_start_tails=['/metal'],
            )
        elif self._section is _Section.COPY:
            self._print_simple_section_line(
                line,
                ignore_line_starts=['builtin-copy'],
            )
        elif self._section is _Section.CLANGSTATCACHE:
            self._print_simple_section_line(
                line,
                ignore_line_start_tails=['/clang-stat-cache'],
            )
        elif self._section is _Section.EXTRACTAPPINTENTSMETADATA:
            # Don't think we need to see this.
            if 'note: Metadata extraction skipped' in line:
                pass
            else:
                self._print_simple_section_line(
                    line,
                    ignore_line_start_tails=['/appintentsmetadataprocessor'],
                )
        elif self._section is _Section.COPYSTRINGSFILE:
            self._print_simple_section_line(
                line,
                ignore_line_starts=[
                    'builtin-copyStrings',
                    'CopyPNGFile',
                ],
                ignore_line_start_tails=[
                    '/InfoPlist.strings:1:1:',
                    '/copypng',
                    '/iconutil',
                ],
                ignore_containing=[
                    'note: detected encoding of input file as Unicode (UTF-8)'
                ],
            )
        elif self._section is _Section.PROCESSPRODUCTPACKAGING:
            if '.net.froemling.ballistica.ios"' in line:
                return
            self._print_simple_section_line(
                line,
                ignore_line_starts=[
                    '"application-identifier"',
                    '"com.apple.developer.ubiquity-kvstore-identifier"',
                    '"get-task-allow"',
                    '"keychain-access-groups"',
                    'builtin-productPackagingUtility',
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
                    '"com.apple.developer.game-center"',
                    '"com.apple.developer.team-identifier"',
                    '"com.apple.application-identifier"',
                    '"com.apple.security.network.client"',
                    '"com.apple.security.network.server"',
                    '"com.apple.security.scripting-targets"',
                    '"com.apple.Music.library.read",',
                ],
            )
        elif self._section is _Section.GENERATEASSETSYMBOLS:
            self._print_simple_section_line(
                line,
                ignore_containing=[
                    '/* com.apple.actool.compilation-results */',
                    '/GeneratedAssetSymbols-Index.plist',
                    '/GeneratedAssetSymbols.h',
                    '/GeneratedAssetSymbols.swift',
                ],
            )

        elif self._section is _Section.PROCESSPRODUCTPACKAGINGDER:
            self._print_simple_section_line(
                line,
                ignore_line_start_tails=['/derq'],
            )
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
                ],
            )
        elif self._section is _Section.COMPILESWIFTSOURCES:
            self._print_simple_section_line(
                line,
                prefix='Compiling Swift Sources',
                prefix_index=None,
                ignore_line_starts=['PrecompileSwiftBridgingHeader'],
                ignore_line_start_tails=['/swiftc', '/swift-frontend'],
            )
        elif self._section is _Section.PROCESSPCH:
            self._print_simple_section_line(
                line,
                ignore_line_starts=['Precompile of'],
                ignore_line_start_tails=['/clang'],
            )
        elif self._section is _Section.PROCESSPCHPLUSPLUS:
            self._print_simple_section_line(
                line,
                ignore_line_starts=['Precompile of'],
                ignore_line_start_tails=['/clang'],
            )
        elif self._section is _Section.PHASESCRIPTEXECUTION:
            self._print_simple_section_line(
                line,
                prefix='Running Script',
                prefix_index=1,
                ignore_line_starts=['/bin/sh'],
            )
        # elif self._section is _Section.NOTE:
        #     self._print_note_line(line)
        else:
            assert_never(self._section)
        sys.stdout.flush()

    def _print_compilec_line(self, line: str) -> None:
        # TEMP
        # sys.stdout.write(line)
        # return

        # First line of the section.
        if self._section_line_count == 0:
            # If the file path starts with cwd, strip that out.
            fname = shlex.split(line)[2].removeprefix(f'{os.getcwd()}/')
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

    def _print_swift_compile_line(self, line: str) -> None:
        # First line of the section.
        if self._section_line_count == 0:
            # Currently seeing 2 mostly identical lines per compiled files.
            # The first has a 'Compiling\ foo.swift /path/to/foo.swift'
            # The second is just /path/to/foo.swift.
            # Let's hide the first.
            if line.split()[3] == 'Compiling\\':
                return

            # If the file path starts with cwd, strip that out.
            fname = shlex.split(line)[3].removeprefix(f'{os.getcwd()}/')
            sys.stdout.write(f'{Clr.BLU}Compiling {Clr.BLD}{fname}{Clr.RST}\n')
            return

        # Ignore empty lines or things we expect to be there.
        splits = line.split()
        if not splits:
            return
        if splits[0] in [
            'cd',
            'builtin-swiftTaskExecution',
        ]:
            return
        if any(splits[0].endswith(s) for s in ['/clang', '/swift-frontend']):
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
                f'{Clr.BLU}Compiling Asset Catalog {Clr.BLD}{name}{Clr.RST}\n'
            )
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
        if (
            ' ibtoold[' in line_s
            and 'NSFileCoordinator is doing nothing' in line_s
        ):
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
                f'{Clr.BLU}Compiling Storyboard {Clr.BLD}{name}{Clr.RST}\n'
            )
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
        # pylint: disable=too-many-return-statements
        # First line of the section.
        if self._section_line_count == 0:
            name = os.path.basename(shlex.split(line)[1])
            sys.stdout.write(f'{Clr.BLU}Signing' f' {Clr.BLD}{name}{Clr.RST}\n')
            return

        # Ignore empty lines or things we expect to be there.
        splits = line.split()
        if not splits:
            return
        if (
            len(splits) > 1
            and splits[0] == 'Provisioning'
            and splits[1] == 'Profile:'
        ):
            return
        # A uuid string (provisioning profile id or whatnot)
        if (
            len(splits) == 1
            and splits[0].startswith('(')
            and splits[0].endswith(')')
            and len(splits[0].split('-')) == 5
        ):
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
        prefix: str | None = None,
        prefix_index: int | None = None,
        ignore_line_starts: list[str] | None = None,
        ignore_line_start_tails: list[str] | None = None,
        ignore_containing: list[str] | None = None,
        prefix_unexpected: bool = True,
    ) -> None:
        # pylint: disable=too-many-branches
        if ignore_line_starts is None:
            ignore_line_starts = []
        if ignore_line_start_tails is None:
            ignore_line_start_tails = []
        if ignore_containing is None:
            ignore_containing = []

        # First line of the section.
        if self._section_line_count == 0:
            if prefix is not None:
                if prefix_index is None:
                    sys.stdout.write(f'{Clr.BLU}{prefix}{Clr.RST}\n')
                else:
                    name = os.path.basename(shlex.split(line)[prefix_index])
                    sys.stdout.write(
                        f'{Clr.BLU}{prefix}' f' {Clr.BLD}{name}{Clr.RST}\n'
                    )
            return

        # Ignore empty lines or things we expect to be there.
        splits = line.split()
        if not splits:
            return
        for start in ['cd', 'export'] + ignore_line_starts:
            # The start strings they pass may themselves be splittable so
            # we may need to compare more than one string.
            startsplits = start.split()
            if splits[: len(startsplits)] == startsplits:
                return
        if any(splits[0].endswith(tail) for tail in ignore_line_start_tails):
            return
        if any(c in line for c in ignore_containing):
            return

        # Fall back on printing anything we don't recognize.
        if prefix is None and prefix_unexpected:
            # If a prefix was not supplied for this section, the user will
            # have no way to know what this output relates to. Tack a bit
            # on to clarify in that case (unless requested not to).
            assert self._section is not None
            sys.stdout.write(
                f'{Clr.YLW}Unfiltered Output (Section {self._section.value}):'
                f'{Clr.RST} {line}'
            )
        else:
            sys.stdout.write(line)


def project_build_path(
    projroot: str,
    project_path: str,
    scheme: str,
    configuration: str,
    executable: bool = True,
) -> str:
    """Get build paths for an xcode project (cached for efficiency)."""
    # pylint: disable=too-many-locals
    # pylint: disable=too-many-statements

    config_path = os.path.join(projroot, '.cache', 'xcode_build_path')
    config: dict[str, dict[str, Any]] = {}

    build_dir: str | None = None
    executable_path: str | None = None

    if os.path.exists(config_path):
        with open(config_path, encoding='utf-8') as infile:
            config = json.loads(infile.read())
        if (
            project_path in config
            and configuration in config[project_path]
            and scheme in config[project_path][configuration]
        ):
            # Ok we've found a build-dir entry for this project; now if it
            # exists on disk and all timestamps within it are decently
            # close to the one we've got recorded, lets use it.
            # (Anything using this script should also be building
            # stuff there so mod times should be pretty recent; if not
            # then its worth re-caching to be sure.)
            cached_build_dir = config[project_path][configuration][scheme][
                'build_dir'
            ]
            cached_timestamp = config[project_path][configuration][scheme][
                'timestamp'
            ]
            cached_executable_path = config[project_path][configuration][
                scheme
            ]['executable_path']
            assert isinstance(cached_build_dir, str)
            assert isinstance(cached_timestamp, float)
            assert isinstance(cached_executable_path, str)
            now = time.time()
            if (
                os.path.isdir(cached_build_dir)
                and abs(now - cached_timestamp) < 60 * 60 * 24
            ):
                build_dir = cached_build_dir
                executable_path = cached_executable_path

    # If we don't have a path at this point we look it up and cache it.
    if build_dir is None:
        print('Caching xcode build path...', file=sys.stderr)
        cmd = [
            'xcodebuild',
            '-project',
            project_path,
            '-showBuildSettings',
            '-configuration',
            configuration,
            '-scheme',
            scheme,
        ]
        output = subprocess.run(
            cmd, check=True, capture_output=True
        ).stdout.decode()

        prefix = 'TARGET_BUILD_DIR = '
        lines = [l for l in output.splitlines() if l.strip().startswith(prefix)]
        if len(lines) != 1:
            raise RuntimeError(
                'TARGET_BUILD_DIR not found in xcodebuild settings output.'
            )
        build_dir = lines[0].replace(prefix, '').strip()

        prefix = 'EXECUTABLE_PATH = '
        lines = [l for l in output.splitlines() if l.strip().startswith(prefix)]
        if len(lines) != 1:
            raise RuntimeError(
                'EXECUTABLE_PATH not found in xcodebuild settings output.'
            )
        executable_path = lines[0].replace(prefix, '').strip()

        if project_path not in config:
            config[project_path] = {}
        if configuration not in config[project_path]:
            config[project_path][configuration] = {}
        config[project_path][configuration][scheme] = {
            'build_dir': build_dir,
            'executable_path': executable_path,
            'timestamp': time.time(),
        }
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        with open(config_path, 'w', encoding='utf-8') as outfile:
            outfile.write(json.dumps(config))

    assert build_dir is not None
    if executable:
        assert executable_path is not None
        outpath = os.path.join(build_dir, executable_path)
        if not os.path.isfile(outpath):
            raise RuntimeError(f'Path is not a file: "{outpath}".')
    else:
        outpath = build_dir
        if not os.path.isdir(outpath):
            raise RuntimeError(f'Path is not a dir: "{outpath}".')

    return outpath
