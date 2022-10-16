# Released under the MIT License. See LICENSE for details.
#
"""General project related functionality."""

from __future__ import annotations

import os
import sys
import subprocess
from dataclasses import dataclass
from typing import TYPE_CHECKING

from efro.error import CleanError
from efro.terminal import Clr

if TYPE_CHECKING:
    pass


def project_centric_path(projroot: str, path: str) -> str:
    """Convert a CWD-relative path to a project-relative one."""
    abspath = os.path.abspath(path)
    if abspath == projroot:
        return '.'
    projprefix = f'{projroot}/'
    if not abspath.startswith(projprefix):
        raise RuntimeError(
            f'Path "{abspath}" is not under project root "{projprefix}"'
        )
    return abspath[len(projprefix) :]


def get_legal_notice_private() -> str:
    """Return the one line legal notice we expect private files to have."""
    return 'Copyright (c) 2011-2022 Eric Froemling'


@dataclass
class LineChange:
    """A change applying to a particular line in a file."""

    line_number: int
    expected: str
    can_auto_update: bool


class Updater:
    """Context for an app run."""

    def __init__(self, check: bool, fix: bool) -> None:
        from efrotools import getconfig, getlocalconfig
        from pathlib import Path

        self._check = check
        self._fix = fix
        self._checkarg = ' --check' if self._check else ''
        self._checkarglist: list[str] = ['--check'] if self._check else []

        # We behave differently in the public repo
        self._public = getconfig(Path('.'))['public']
        assert isinstance(self._public, bool)

        self._source_files: list[str] = []
        self._header_files: list[str] = []

        self._line_corrections: dict[str, list[LineChange]] = {}
        self._file_changes: dict[str, str] = {}

        self._license_line_checks = bool(
            getlocalconfig(Path('.')).get('license_line_checks', True)
        )

        self._internal_source_dirs: set[str] | None = None
        self._internal_source_files: set[str] | None = None

    def run(self) -> None:
        """Do the thing."""

        # Make sure we're operating from a project root.
        if not os.path.isdir('config') or not os.path.isdir('tools'):
            raise Exception('This must be run from a project root.')

        # Note: we need to update the meta Makefile first since its output
        # manifest may be used when generating asset/resource targets.
        self._update_meta_makefile()
        self._update_resources_makefile()
        self._update_assets_makefile()

        self._check_makefiles()
        self._check_python_files()
        self._check_sync_states()
        self._check_misc()

        self._find_sources_and_headers('src/ballistica')

        # FIXME: It might make more sense to have some of these checks
        # run via 'make check' rather than here through 'make update'.
        self._check_source_files()
        self._check_headers()

        self._update_cmake_files()
        self._update_visual_studio_projects()

        # If we're all good to here, do the actual writes we set up above.
        self._apply_line_changes()
        self._apply_file_changes()

        self._update_dummy_modules()

        # Though not technically necessary, let's go ahead and update
        # irony compile-commands, tool configs, etc. as part of the
        # update process. This lessens the chance we'll have tools
        # behave funny until the next time we run a build.
        subprocess.run(['make', f'-j{os.cpu_count()}', 'prereqs'], check=True)

        if self._check:
            print(f'{Clr.BLU}Check-Builds: Everything up to date.{Clr.RST}')
        else:
            print(f'{Clr.GRN}Update-Project: SUCCESS!{Clr.RST}')

    def _get_internal_source_files(self) -> set[str]:
        from pathlib import Path
        from efrotools import getconfig

        # Fetch/calc just once and cache results.
        if self._internal_source_files is None:
            sources: list[str]
            if self._public:
                sources = []
            else:
                sources = getconfig(Path('.')).get('internal_source_files', [])
            if not isinstance(sources, list):
                raise CleanError(
                    f'Expected list for internal_source_files;'
                    f' got {type(sources)}'
                )
            self._internal_source_files = set(sources)
        return self._internal_source_files

    def _get_internal_source_dirs(self) -> set[str]:
        from pathlib import Path
        from efrotools import getconfig

        # Fetch/calc just once and cache results.
        if self._internal_source_dirs is None:
            sources: list[str]
            if self._public:
                sources = []
            else:
                sources = getconfig(Path('.')).get('internal_source_dirs', [])
            if not isinstance(sources, list):
                raise CleanError(
                    f'Expected list for internal_source_dirs;'
                    f' got {type(sources)}'
                )
            self._internal_source_dirs = set(sources)
        return self._internal_source_dirs

    def _apply_file_changes(self) -> None:
        # Now write out any project files that have changed
        # (or error if we're in check mode).
        unchanged_project_count = 0
        for fname, fcode in self._file_changes.items():
            f_orig: str | None
            if os.path.exists(fname):
                with open(fname, 'r', encoding='utf-8') as infile:
                    f_orig = infile.read()
            else:
                f_orig = None
            if f_orig == fcode.replace('\r\n', '\n'):
                unchanged_project_count += 1
            else:
                if self._check:
                    print(
                        f'{Clr.RED}ERROR: found out-of-date'
                        f' project file: {fname}{Clr.RST}'
                    )
                    sys.exit(255)

                print(f'{Clr.BLU}Writing project file: {fname}{Clr.RST}')
                with open(fname, 'w', encoding='utf-8') as outfile:
                    outfile.write(fcode)
        if unchanged_project_count > 0:
            print(
                f'All {unchanged_project_count} project files are up to date.'
            )

    def _apply_line_changes(self) -> None:

        # Build a flat list of entries that can and can-not be auto applied.
        manual_changes: list[tuple[str, LineChange]] = []
        auto_changes: list[tuple[str, LineChange]] = []
        for fname, entries in self._line_corrections.items():
            for entry in entries:
                if entry.can_auto_update:
                    auto_changes.append((fname, entry))
                else:
                    manual_changes.append((fname, entry))

        # If there are any manual-only entries, list then and bail.
        # (Don't wanna allow auto-apply unless it fixes everything)
        if manual_changes:
            print(
                f'{Clr.RED}Found erroneous lines '
                f'requiring manual correction:{Clr.RST}'
            )
            for change in manual_changes:
                print(
                    f'{Clr.RED}{change[0]}:{change[1].line_number + 1}:'
                    f' Expected line to be:\n  {change[1].expected}{Clr.RST}'
                )

            sys.exit(-1)

        # Now, if we've got auto entries, either list or auto-correct them.
        if auto_changes:
            if not self._fix:
                for i, change in enumerate(auto_changes):
                    print(
                        f'{Clr.RED}#{i}:'
                        f' {change[0]}:{change[1].line_number+1}:'
                        f'{Clr.RST}'
                    )
                    print(
                        f'{Clr.RED}  Expected "{change[1].expected}"{Clr.RST}'
                    )
                    with open(change[0], encoding='utf-8') as infile:
                        lines = infile.read().splitlines()
                    line = lines[change[1].line_number]
                    print(f'{Clr.RED}  Found "{line}"{Clr.RST}')
                print(
                    f'{Clr.RED}All {len(auto_changes)} errors are'
                    f' auto-fixable; run tools/pcommand update_project'
                    f' --fix to apply corrections. {Clr.RST}'
                )
                sys.exit(255)
            else:
                for i, change in enumerate(auto_changes):
                    print(f'{Clr.BLU}Correcting file: {change[0]}{Clr.RST}')
                    with open(change[0], encoding='utf-8') as infile:
                        lines = infile.read().splitlines()
                    lines[change[1].line_number] = change[1].expected
                    with open(change[0], 'w', encoding='utf-8') as outfile:
                        outfile.write('\n'.join(lines) + '\n')

        # If there were no issues whatsoever, note that.
        if not manual_changes and not auto_changes:
            fcount = len(self._header_files) + len(self._source_files)
            print(f'No issues found in {fcount} source files.')

    def _check_source_files(self) -> None:

        for fsrc in self._source_files:
            if fsrc.endswith('.cpp') or fsrc.endswith('.cxx'):
                raise Exception('please use .cc for c++ files; found ' + fsrc)

            # Watch out for in-progress emacs edits.
            # Could just ignore these but it probably means I intended
            # to save something and forgot.
            if '/.#' in fsrc:
                print(
                    f'{Clr.RED}'
                    f'ERROR: Found an unsaved emacs file: "{fsrc}"'
                    f'{Clr.RST}'
                )
                sys.exit(255)

            fname = 'src/ballistica' + fsrc
            self._check_source_file(fname)

    def _check_source_file(self, fname: str) -> None:
        with open(fname, encoding='utf-8') as infile:
            lines = infile.read().splitlines()

        if self._license_line_checks:
            self._check_c_license(fname, lines)

    def _check_headers(self) -> None:
        for header_file_raw in self._header_files:
            assert header_file_raw[0] == '/'
            header_file = 'src/ballistica' + header_file_raw

            if header_file.endswith('.h'):
                self._check_header(header_file)

    def _add_line_correction(
        self,
        filename: str,
        line_number: int,
        expected: str,
        can_auto_update: bool,
    ) -> None:
        # No longer allowing negatives here since they don't show up nicely
        # in correction list.
        assert line_number >= 0
        self._line_corrections.setdefault(filename, []).append(
            LineChange(
                line_number=line_number,
                expected=expected,
                can_auto_update=can_auto_update,
            )
        )

    def _check_c_license(self, fname: str, lines: list[str]) -> None:
        from efrotools import get_public_license

        # Look for public license line (public or private repo)
        # or private license line (private repo only)
        line_private = '// ' + get_legal_notice_private()
        line_public = get_public_license('c++')
        lnum = 0

        if self._public:
            if lines[lnum] != line_public:
                # Allow auto-correcting from private to public line
                allow_auto = lines[lnum] == line_private
                self._add_line_correction(
                    fname,
                    line_number=lnum,
                    expected=line_public,
                    can_auto_update=allow_auto,
                )
        else:
            if lines[lnum] not in [line_public, line_private]:
                self._add_line_correction(
                    fname,
                    line_number=lnum,
                    expected=line_private,
                    can_auto_update=False,
                )

    def _check_header(self, fname: str) -> None:

        # Make sure its define guard is correct.
        guard = fname[4:].upper().replace('/', '_').replace('.', '_') + '_'
        with open(fname, encoding='utf-8') as fhdr:
            lines = fhdr.read().splitlines()

        if self._license_line_checks:
            self._check_c_license(fname, lines)

        # Check for header guard lines at top
        line = '#ifndef ' + guard
        lnum = 2
        if lines[lnum] != line:
            # Allow auto-correcting if it looks close already
            # (don't want to blow away an unrelated line)
            allow_auto = lines[lnum].startswith('#ifndef BALLISTICA_')
            self._add_line_correction(
                fname,
                line_number=lnum,
                expected=line,
                can_auto_update=allow_auto,
            )
        line = '#define ' + guard
        lnum = 3
        if lines[lnum] != line:
            # Allow auto-correcting if it looks close already
            # (don't want to blow away an unrelated line)
            allow_auto = lines[lnum].startswith('#define BALLISTICA_')
            self._add_line_correction(
                fname,
                line_number=lnum,
                expected=line,
                can_auto_update=allow_auto,
            )

        # Check for header guard at bottom
        line = '#endif  // ' + guard
        lnum = len(lines) - 1
        if lines[lnum] != line:
            # Allow auto-correcting if it looks close already
            # (don't want to blow away an unrelated line)
            allow_auto = lines[lnum].startswith('#endif  // BALLISTICA_')
            self._add_line_correction(
                fname,
                line_number=lnum,
                expected=line,
                can_auto_update=allow_auto,
            )

    def _check_makefiles(self) -> None:
        from efrotools import get_public_license

        # Run a few sanity checks on whatever makefiles we come across.
        fnames = (
            subprocess.run(
                'find . -maxdepth 3 -name Makefile',
                shell=True,
                capture_output=True,
                check=True,
            )
            .stdout.decode()
            .split()
        )
        fnames = [n for n in fnames if '/build/' not in n]

        for fname in fnames:
            with open(fname, encoding='utf-8') as infile:
                makefile = infile.read()
            if self._public:
                public_license = get_public_license('makefile')
                if public_license not in makefile:
                    raise CleanError(f'Pub license not found in {fname}.')
            else:
                if (
                    get_legal_notice_private() not in makefile
                    and get_public_license('makefile') not in makefile
                ):
                    raise CleanError(f'Priv or pub legal not found in {fname}.')

    def _check_python_file(self, fname: str) -> None:
        # pylint: disable=too-many-branches
        from efrotools import get_public_license, PYVER

        with open(fname, encoding='utf-8') as infile:
            contents = infile.read()
            lines = contents.splitlines()

        # Make sure all standalone scripts are pointing to the right
        # version of python (with a few exceptions where it needs to
        # differ)
        if contents.startswith('#!/'):
            copyrightline = 1
            if fname not in ['tools/vmshell']:
                if not contents.startswith(f'#!/usr/bin/env python{PYVER}'):
                    raise CleanError(
                        f'Incorrect shebang (first line) for ' f'{fname}.'
                    )
        else:
            copyrightline = 0

        # Special case: it there's spinoff autogenerate notice there,
        # look below it.
        if (
            lines[copyrightline] == ''
            and 'THIS FILE IS AUTOGENERATED' in lines[copyrightline + 1]
        ):
            copyrightline += 2

        if lines[copyrightline].startswith('# Synced from '):
            copyrightline += 3

        for i, line in enumerate(lines):
            # stuff under the ba module.
            if '/ba/' in fname:
                # Don't allow importing ba at the top level from within ba.
                if line == 'import ba':
                    raise CleanError(
                        f'{fname}:{i+1}: no top level ba imports allowed'
                        f' under ba module.'
                    )
            if '/bastd/' in fname:
                # Don't allow importing _ba or _bainternal anywhere here.
                # (any internal needs should be in ba.internal)
                if 'import _ba' in line:
                    raise CleanError(
                        f'{fname}:{i+1}: _ba or _bainternal imports not'
                        f' allowed under bastd.'
                    )

        # In all cases, look for our one-line legal notice.
        # In the public case, look for the rest of our public license too.
        if self._license_line_checks:
            public_license = get_public_license('python')
            private_license = '# ' + get_legal_notice_private()
            lnum = copyrightline
            if len(lines) < lnum + 1:
                raise RuntimeError('Not enough lines in file:', fname)

            disable_note = (
                'NOTE: You can disable license line'
                ' checks by adding "license_line_checks": false\n'
                'to the root dict in config/localconfig.json.\n'
                'see https://ballistica.net/wiki'
                '/Knowledge-Nuggets#'
                'hello-world-creating-a-new-game-type'
            )

            if self._public:
                # Check for public license only.
                if lines[lnum] != public_license:
                    raise CleanError(
                        f'License text not found'
                        f" at '{fname}' line {lnum+1};"
                        f' please correct.\n'
                        f'Expected text is: {public_license}\n'
                        f'{disable_note}'
                    )
            else:
                # Check for public or private license.
                if (
                    lines[lnum] != public_license
                    and lines[lnum] != private_license
                ):
                    raise CleanError(
                        f'License text not found'
                        f" at '{fname}' line {lnum+1};"
                        f' please correct.\n'
                        f'Expected text (for public files):'
                        f' {public_license}\n'
                        f'Expected text (for private files):'
                        f' {private_license}\n'
                        f'{disable_note}'
                    )

    def _check_python_files(self) -> None:
        from pathlib import Path
        from efrotools.code import get_script_filenames

        scriptfiles = get_script_filenames(Path('.'))
        for fname in scriptfiles:
            self._check_python_file(fname)

        # Check our packages and make sure all subdirs contain and __init__.py
        # (I tend to forget this sometimes)
        packagedirs = ['tools/efrotools', 'tools/efro']

        # (Assume all dirs under these dirs are packages)
        dirs_of_packages = ['assets/src/ba_data/python', 'tests']
        for dir_of_packages in dirs_of_packages:
            for name in os.listdir(dir_of_packages):
                if not name.startswith('.') and os.path.isdir(
                    os.path.join(dir_of_packages, name)
                ):
                    packagedirs.append(os.path.join(dir_of_packages, name))

        for packagedir in packagedirs:
            for root, _dirs, files in os.walk(packagedir):
                if (
                    '__pycache__' not in root
                    and os.path.basename(root) != '.vscode'
                ):
                    if '__init__.py' not in files:
                        print(
                            Clr.RED
                            + 'Error: no __init__.py in package dir: '
                            + root
                            + Clr.RST
                        )
                        sys.exit(255)

    def _update_visual_studio_project(self, basename: str) -> None:

        fname = (
            f'ballisticacore-windows/{basename}/'
            f'BallisticaCore{basename}.vcxproj'
        )

        # Currently just silently skipping if not found (for public repo).
        if not os.path.exists(fname):
            raise CleanError(f'Visual Studio project not found: {fname}')

        with open(fname, encoding='utf-8') as infile:
            lines = infile.read().splitlines()

        src_root = '..\\..\\src'

        public_project = 'Internal' not in basename

        all_files = sorted(
            [
                f
                for f in (self._source_files + self._header_files)
                if not f.endswith('.m')
                and not f.endswith('.mm')
                and not f.endswith('.c')
                and self._is_public_source_file(f) == public_project
            ]
        )

        # Find the ItemGroup containing stdafx.cpp. This is where we'll dump
        # our stuff.
        index = lines.index('    <ClCompile Include="stdafx.cpp">')
        begin_index = end_index = index
        while lines[begin_index] != '  <ItemGroup>':
            begin_index -= 1
        while lines[end_index] != '  </ItemGroup>':
            end_index += 1
        group_lines = lines[begin_index + 1 : end_index]

        # Strip out any existing files from src/ballistica.
        group_lines = [
            l for l in group_lines if src_root + '\\ballistica\\' not in l
        ]

        # Now add in our own.
        # Note: we can't use C files in this build at the moment; breaks
        # precompiled header stuff. (shouldn't be a problem though).
        group_lines = [
            '    <'
            + ('ClInclude' if src.endswith('.h') else 'ClCompile')
            + ' Include="'
            + src_root
            + '\\ballistica'
            + src.replace('/', '\\')
            + '" />'
            for src in all_files
        ] + group_lines

        filtered = lines[: begin_index + 1] + group_lines + lines[end_index:]
        self._file_changes[fname] = '\r\n'.join(filtered) + '\r\n'

        self._update_visual_studio_project_filters(filtered, fname, src_root)

    def _update_visual_studio_project_filters(
        self, lines_in: list[str], fname: str, src_root: str
    ) -> None:
        filterpaths: set[str] = set()
        filterlines: list[str] = [
            '<?xml version="1.0" encoding="utf-8"?>',
            '<Project ToolsVersion="4.0"'
            ' xmlns="http://schemas.microsoft.com/developer/msbuild/2003">',
            '  <ItemGroup>',
        ]
        sourcelines = [l for l in lines_in if 'Include="' + src_root in l]
        for line in sourcelines:
            entrytype = line.strip().split()[0][1:]
            path = line.split('"')[1]
            filterlines.append('    <' + entrytype + ' Include="' + path + '">')

            # If we have a dir foo/bar/eep we need to create filters for
            # each of foo, foo/bar, and foo/bar/eep
            splits = path[len(src_root) :].split('\\')
            splits = [s for s in splits if s != '']
            splits = splits[:-1]
            for i in range(len(splits)):
                filterpaths.add('\\'.join(splits[: (i + 1)]))
            filterlines.append(
                '      <Filter>' + '\\'.join(splits) + '</Filter>'
            )
            filterlines.append('    </' + entrytype + '>')
        filterlines += [
            '  </ItemGroup>',
            '  <ItemGroup>',
        ]
        for filterpath in sorted(filterpaths):
            filterlines.append('    <Filter Include="' + filterpath + '" />')
        filterlines += [
            '  </ItemGroup>',
            '</Project>',
        ]
        self._file_changes[fname + '.filters'] = (
            '\r\n'.join(filterlines) + '\r\n'
        )

    def _update_visual_studio_projects(self) -> None:
        self._update_visual_studio_project('Generic')
        self._update_visual_studio_project('Headless')
        if not self._public:
            self._update_visual_studio_project('GenericInternal')
            self._update_visual_studio_project('HeadlessInternal')
            self._update_visual_studio_project('Oculus')
            self._update_visual_studio_project('OculusInternal')

    def _is_public_source_file(self, filename: str) -> bool:
        assert filename.startswith('/')
        filename = f'src/ballistica{filename}'

        # If its under any of our internal source dirs, make it internal.
        for srcdir in self._get_internal_source_dirs():
            assert not srcdir.startswith('/')
            assert not srcdir.endswith('/')
            if filename.startswith(f'{srcdir}/'):
                return False

        # If its specifically listed as an internal file, make it internal.
        return filename not in self._get_internal_source_files()

    def _update_cmake_file(self, fname: str) -> None:
        with open(fname, encoding='utf-8') as infile:
            lines = infile.read().splitlines()

        for section in ['PUBLIC', 'PRIVATE']:
            # Public repo has no private section.
            if self._public and section == 'PRIVATE':
                continue

            auto_start = lines.index(
                f'  # AUTOGENERATED_{section}_BEGIN (this section'
                f' is managed by the "update_project" tool)'
            )
            auto_end = lines.index(f'  # AUTOGENERATED_{section}_END')
            our_lines = [
                '  ${BA_SRC_ROOT}/ballistica' + f
                for f in sorted(self._source_files + self._header_files)
                if not f.endswith('.mm')
                and not f.endswith('.m')
                and self._is_public_source_file(f) == (section == 'PUBLIC')
            ]
            lines = lines[: auto_start + 1] + our_lines + lines[auto_end:]

        self._file_changes[fname] = '\n'.join(lines) + '\n'

    def _update_cmake_files(self) -> None:
        # Note: currently not updating cmake files at all in public builds;
        # will need to get this working at some point...

        # Top level cmake builds:
        fname = 'ballisticacore-cmake/CMakeLists.txt'
        if not self._public:
            self._update_cmake_file(fname)

        # CMake android components:
        fname = (
            'ballisticacore-android/BallisticaCore/src/main/cpp/CMakeLists.txt'
        )
        if not self._public:
            self._update_cmake_file(fname)

    def _find_sources_and_headers(self, scan_dir: str) -> None:
        src_files = set()
        header_files = set()
        exts = ['.c', '.cc', '.cpp', '.cxx', '.m', '.mm']
        header_exts = ['.h']

        # Gather all sources and headers.
        # HMMM: Ideally we should use efrotools.code.get_code_filenames() here.
        # (though we return things relative to the scan-dir which could
        # throw things off)
        for root, _dirs, files in os.walk(scan_dir):
            for ftst in files:
                if any(ftst.endswith(ext) for ext in exts):
                    src_files.add(os.path.join(root, ftst)[len(scan_dir) :])
                if any(ftst.endswith(ext) for ext in header_exts):
                    header_files.add(os.path.join(root, ftst)[len(scan_dir) :])
        self._source_files = sorted(src_files)
        self._header_files = sorted(header_files)

    def _check_misc(self) -> None:
        # Misc sanity checks.
        if not self._public:
            # Make sure we're set to prod master server.
            with open(
                'src/ballistica/internal/master_server_config.h',
                encoding='utf-8',
            ) as infile:
                msconfig = infile.read()
                if (
                    '// V2 Master Server:\n' '\n' '// PROD\n' '#if 1\n'
                ) not in msconfig:
                    raise CleanError('Not using prod v2 master server.')

    def _check_sync_states(self) -> None:
        # Make sure none of our sync targets have been mucked with since
        # their last sync.
        if (
            subprocess.run(
                ['tools/pcommand', 'sync', 'check'], check=False
            ).returncode
            != 0
        ):
            raise CleanError('Sync check failed; you may need to run "sync".')

    def _update_assets_makefile(self) -> None:
        if (
            subprocess.run(
                ['tools/pcommand', 'update_assets_makefile', self._checkarg],
                check=False,
            ).returncode
            != 0
        ):
            print(f'{Clr.RED}Error checking/updating assets Makefile.{Clr.RST}')
            sys.exit(255)

    def _update_meta_makefile(self) -> None:
        try:
            subprocess.run(
                ['tools/pcommand', 'update_meta_makefile'] + self._checkarglist,
                check=True,
            )
        except Exception as exc:
            raise CleanError('Error checking/updating meta Makefile.') from exc

    def _update_resources_makefile(self) -> None:
        try:
            subprocess.run(
                ['tools/pcommand', 'update_resources_makefile']
                + self._checkarglist,
                check=True,
            )
        except Exception as exc:
            raise CleanError(
                'Error checking/updating resources Makefile.'
            ) from exc

    def _update_dummy_modules(self) -> None:
        # Update our dummy _ba module.
        # Note: This should happen near the end because it may run the cmake
        # build so its success may depend on the cmake build files having
        # already been updated.
        try:
            subprocess.run(
                ['tools/pcommand', 'update_dummy_modules'] + self._checkarglist,
                check=True,
            )
        except Exception as exc:
            raise CleanError('Error checking/updating dummy module.') from exc
