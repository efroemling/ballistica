#!/usr/bin/env python3.7
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
"""This script acts as a 'meta' Makefile for the project. It is in charge
of generating Makefiles, IDE project files, procedurally generated source
files, etc. based on the current structure of the project.
It can also perform sanity checks or cleanup tasks.

Updating should be explicitly run by the user through commands such as
'make update', 'make check' or 'make preflight'. Other make targets should
avoid running this script as it can modify the project structure
arbitrarily which is not a good idea in the middle of a build.

If the script is invoked with a --check argument, it should not modify any
files but instead fail if any modifications *would* have been made.
(used in CI builds to make sure things are kosher).
"""

from __future__ import annotations

import os
import sys
import subprocess
from dataclasses import dataclass
from typing import TYPE_CHECKING

from efro.terminal import Clr

if TYPE_CHECKING:
    from typing import Optional, Tuple, List, Dict, Set


def get_legal_notice_private() -> str:
    """Return the one line legal notice we expect private files to have."""
    # We just use the first line of the mit license (just the copyright)
    from efrotools import MIT_LICENSE
    return MIT_LICENSE.splitlines()[0]


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

        # We behave differently in the public repo
        self._public = getconfig(Path('.'))['public']
        assert isinstance(self._public, bool)

        self._source_files: List[str] = []
        self._header_files: List[str] = []

        self._line_corrections: Dict[str, List[LineChange]] = {}
        self._file_changes: Dict[str, str] = {}

        self._copyright_checks = bool(
            getlocalconfig(Path('.')).get('copyright_checks', True))

    def run(self) -> None:
        """Do the thing."""

        # Make sure we're operating from a project root.
        if not os.path.isdir('config') or not os.path.isdir('tools'):
            raise Exception('This must be run from a project root.')

        # NOTE: Do py-enums before updating asset deps since it is an asset.
        self._update_python_enums_module()
        self._update_resources_makefile()
        self._update_generated_code_makefile()
        self._update_assets_makefile()

        self._check_makefiles()
        self._check_python_files()
        self._check_sync_states()

        self._find_sources_and_headers('src/ballistica')

        # FIXME: It might make more sense to have some of these checks
        # run via 'make check' rather than here through 'make update'.
        self._check_source_files()
        self._check_headers()

        self._update_cmake_files()
        self._update_visual_studio_projects()

        # If we're all good to here, do actual writes set up
        # by the above stuff.
        self._apply_line_changes()
        self._apply_file_changes()
        self._update_compile_commands_file()

        # We only check/update these in core; not spinoff projects.
        # That is because they create hashes based on source files
        # that get filtered for spinoff projects so always trip
        # dirty-checks there. If we want to generate these uniquely per
        # spinoff project we would need to start running updates
        # independently for those projects as opposed to just using
        # things as spinoff creates them.

        # (this will get filtered and be unequal in spinoff projects)
        if 'ballistica' + 'core' == 'ballisticacore':
            self._update_dummy_module()
            self._update_docs_md()

        if self._check:
            print(f'{Clr.BLU}Check-Builds: Everything up to date.{Clr.RST}')
        else:
            print(f'{Clr.GRN}Update-Project: SUCCESS!{Clr.RST}')

    def _update_dummy_module(self) -> None:
        # Update our dummy _ba module.
        # We need to do this near the end because it may run the cmake build
        # so its success may depend on the cmake build files having already
        # been updated.
        if os.path.exists('tools/gendummymodule.py'):
            if os.system('tools/gendummymodule.py' + self._checkarg) != 0:
                print(
                    f'{Clr.RED}Error checking/updating dummy module.{Clr.RST}')
                sys.exit(255)

    def _update_docs_md(self) -> None:
        # Update our docs/*.md files.
        # We need to do this near the end because it may run the cmake build
        # so its success may depend on the cmake build files having already
        # been updated.
        # (only do this if gendocs is available)
        if os.path.exists('tools/gendocs.py'):
            if os.system('tools/pcommand update_docs_md' +
                         self._checkarg) != 0:
                print(f'{Clr.RED}Error checking/updating'
                      f' docs markdown.{Clr.RST}')
                sys.exit(255)

    def _update_compile_commands_file(self) -> None:
        # Update our local compile-commands file based on any changes to
        # our cmake stuff. Do this at end so cmake changes already happened.
        if not self._check and os.path.exists('ballisticacore-cmake'):
            if os.system('make .irony/compile_commands.json') != 0:
                print(f'{Clr.RED}Error updating compile-commands.{Clr.RST}')
                sys.exit(255)

    def _apply_file_changes(self) -> None:
        # Now write out any project files that have changed
        # (or error if we're in check mode).
        unchanged_project_count = 0
        for fname, fcode in self._file_changes.items():
            f_orig: Optional[str]
            if os.path.exists(fname):
                with open(fname, 'r') as infile:
                    f_orig = infile.read()
            else:
                f_orig = None
            if f_orig == fcode.replace('\r\n', '\n'):
                unchanged_project_count += 1
            else:
                if self._check:
                    print(f'{Clr.RED}ERROR: found out-of-date'
                          f' project file: {fname}{Clr.RST}')
                    sys.exit(255)

                print(f'{Clr.BLU}Writing project file: {fname}{Clr.RST}')
                with open(fname, 'w') as outfile:
                    outfile.write(fcode)
        if unchanged_project_count > 0:
            print(
                f'All {unchanged_project_count} project files are up to date.')

    def _apply_line_changes(self) -> None:
        # pylint: disable=too-many-branches

        # Build a flat list of entries that can and can-not be auto applied.
        manual_changes: List[Tuple[str, LineChange]] = []
        auto_changes: List[Tuple[str, LineChange]] = []
        for fname, entries in self._line_corrections.items():
            for entry in entries:
                if entry.can_auto_update:
                    auto_changes.append((fname, entry))
                else:
                    manual_changes.append((fname, entry))

        # If there are any manual-only entries, list then and bail.
        # (Don't wanna allow auto-apply unless it fixes everything)
        if manual_changes:
            print(f'{Clr.RED}Found erroneous lines '
                  f'requiring manual correction:{Clr.RST}')
            for change in manual_changes:
                print(
                    f'{Clr.RED}{change[0]}:{change[1].line_number + 1}:'
                    f' Expected line to be:\n  {change[1].expected}{Clr.RST}')

                # Make a note on copyright lines that this can be disabled.
                if 'Copyright' in change[1].expected:
                    print(f'{Clr.RED}NOTE: You can disable copyright'
                          f' checks by adding "copyright_checks": false\n'
                          f'to the root dict in config/localconfig.json.\n'
                          f'see https://ballistica.net/wiki'
                          f'/Knowledge-Nuggets#'
                          f'hello-world-creating-a-new-game-type{Clr.RST}')
            sys.exit(-1)

        # Now, if we've got auto entries, either list or auto-correct them.
        if auto_changes:
            if not self._fix:
                for i, change in enumerate(auto_changes):
                    print(f'{Clr.RED}#{i}: {change[0]}:{Clr.RST}')
                    print(
                        f'{Clr.RED}  Expected "{change[1].expected}"{Clr.RST}')
                    with open(change[0]) as infile:
                        lines = infile.read().splitlines()
                    line = lines[change[1].line_number]
                    print(f'{Clr.RED}  Found "{line}"{Clr.RST}')
                print(f'{Clr.RED}All {len(auto_changes)} errors are'
                      f' auto-fixable; run tools/pcommand update_project'
                      f' --fix to apply corrections. {Clr.RST}')
                sys.exit(255)
            else:
                for i, change in enumerate(auto_changes):
                    print(f'{Clr.BLU}Correcting file: {change[0]}{Clr.RST}')
                    with open(change[0]) as infile:
                        lines = infile.read().splitlines()
                    lines[change[1].line_number] = change[1].expected
                    with open(change[0], 'w') as outfile:
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
                print(f'{Clr.RED}'
                      f'ERROR: Found an unsaved emacs file: "{fsrc}"'
                      f'{Clr.RST}')
                sys.exit(255)

            fname = 'src/ballistica' + fsrc
            self._check_source_file(fname)

    def _check_source_file(self, fname: str) -> None:
        with open(fname) as infile:
            lines = infile.read().splitlines()

        # Look for copyright/legal-notice line(s)
        if self._copyright_checks:
            legal_notice = '// ' + get_legal_notice_private()
            lnum = 0
            if lines[lnum] != legal_notice:
                # Allow auto-correcting if it looks close already
                # (don't want to blow away an unrelated line)
                allow_auto = 'Copyright' in lines[
                    lnum] and 'Eric Froemling' in lines[lnum]
                self._add_line_correction(fname,
                                          line_number=lnum,
                                          expected=legal_notice,
                                          can_auto_update=allow_auto)

    def _check_headers(self) -> None:
        for header_file_raw in self._header_files:
            assert header_file_raw[0] == '/'
            header_file = 'src/ballistica' + header_file_raw

            if header_file.endswith('.h'):
                self._check_header(header_file)

    def _add_line_correction(self, filename: str, line_number: int,
                             expected: str, can_auto_update: bool) -> None:
        self._line_corrections.setdefault(filename, []).append(
            LineChange(line_number=line_number,
                       expected=expected,
                       can_auto_update=can_auto_update))

    def _check_header(self, fname: str) -> None:

        # Make sure its define guard is correct.
        guard = (fname[4:].upper().replace('/', '_').replace('.', '_') + '_')
        with open(fname) as fhdr:
            lines = fhdr.read().splitlines()

        if self._public:
            raise RuntimeError('FIXME: Check for full license.')

        # Look for copyright/legal-notice line(s)
        line = '// ' + get_legal_notice_private()
        lnum = 0
        if lines[lnum] != line:
            # Allow auto-correcting if it looks close already
            # (don't want to blow away an unrelated line)
            allow_auto = 'Copyright' in lines[
                lnum] and 'Eric Froemling' in lines[lnum]
            self._add_line_correction(fname,
                                      line_number=lnum,
                                      expected=line,
                                      can_auto_update=allow_auto)

        # Check for header guard at top
        line = '#ifndef ' + guard
        lnum = 2
        if lines[lnum] != line:
            # Allow auto-correcting if it looks close already
            # (don't want to blow away an unrelated line)
            allow_auto = lines[lnum].startswith('#ifndef BALLISTICA_')
            self._add_line_correction(fname,
                                      line_number=lnum,
                                      expected=line,
                                      can_auto_update=allow_auto)

        # Check for header guard at bottom
        line = '#endif  // ' + guard
        lnum = -1
        if lines[lnum] != line:
            # Allow auto-correcting if it looks close already
            # (don't want to blow away an unrelated line)
            allow_auto = lines[lnum].startswith('#endif  // BALLISTICA_')
            self._add_line_correction(fname,
                                      line_number=lnum,
                                      expected=line,
                                      can_auto_update=allow_auto)

    def _check_makefiles(self) -> None:
        from efrotools import get_public_license

        # Run a few sanity checks on whatever makefiles we come across.
        fnames = subprocess.run('find . -maxdepth 3 -name Makefile',
                                shell=True,
                                capture_output=True,
                                check=True).stdout.decode().split()
        fnames = [n for n in fnames if '/build/' not in n]

        for fname in fnames:
            with open(fname) as infile:
                makefile = infile.read()
            if get_legal_notice_private() not in makefile:
                raise RuntimeError(f'Priv legal not found in {fname}')
            if self._public:
                public_license = get_public_license('makefile')
                if public_license not in makefile:
                    raise RuntimeError(f'Pub license not found in {fname}')

    def _check_python_file(self, fname: str) -> None:
        # pylint: disable=too-many-branches
        from efrotools import get_public_license, PYVER
        with open(fname) as infile:
            contents = infile.read()
            lines = contents.splitlines()

        # Make sure all standalone scripts are pointing to the right
        # version of python (with a few exceptions where it needs to
        # differ)
        if contents.startswith('#!/'):
            copyrightline = 1
            if fname not in [
                    'tools/devtool', 'tools/version_utils', 'tools/vmshell'
            ]:
                if not contents.startswith(f'#!/usr/bin/env python{PYVER}'):
                    print(f'{Clr.RED}Incorrect shebang (first line) for '
                          f'{fname}.{Clr.RST}')
                    sys.exit(255)
        else:
            copyrightline = 0

        # Special case: it there's spinoff autogenerate notice there,
        # look below it.
        if (lines[copyrightline] == ''
                and 'THIS FILE IS AUTOGENERATED' in lines[copyrightline + 1]):
            copyrightline += 2

        # In all cases, look for our one-line legal notice.
        # In the public case, look for the rest of our public license too.
        if self._copyright_checks:
            public_license = get_public_license('python')
            line = '# ' + get_legal_notice_private()

            # (Sanity check: public license's first line should be
            # same as priv)
            if line != public_license.splitlines()[0]:
                raise RuntimeError(
                    'Public license first line should match priv.')

            lnum = copyrightline
            if len(lines) < lnum + 1:
                raise RuntimeError('Not enough lines in file:', fname)

            if lines[lnum] != line:
                # Allow auto-correcting if it looks close already
                # (don't want to blow away an unrelated line)
                allow_auto = 'Copyright' in lines[
                    lnum] and 'Eric Froemling' in lines[lnum]
                self._add_line_correction(fname,
                                          line_number=lnum,
                                          expected=line,
                                          can_auto_update=allow_auto)
                found_intact_private = False
            else:
                found_intact_private = True

            if self._public:
                # Check for the full license.
                # If we can't find the full license but we found
                # a private-license line, offer to replace it with the
                # full one. Otherwise just complain and die.

                # Try to be reasonably certain it's not in here...
                definitely_have_full = public_license in contents
                might_have_full = ('Permission is hereby granted' in contents
                                   or 'THE SOFTWARE IS PROVIDED' in contents)

                # Only muck with it if we're not sure we've got it.
                if not definitely_have_full:
                    if found_intact_private and not might_have_full:
                        self._add_line_correction(fname,
                                                  line_number=lnum,
                                                  expected=public_license,
                                                  can_auto_update=True)
                    else:
                        raise RuntimeError(
                            f'Found incorrect license text in {fname};'
                            f' please correct.')

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
                if (not name.startswith('.') and os.path.isdir(
                        os.path.join(dir_of_packages, name))):
                    packagedirs.append(os.path.join(dir_of_packages, name))

        for packagedir in packagedirs:
            for root, _dirs, files in os.walk(packagedir):
                if ('__pycache__' not in root
                        and os.path.basename(root) != '.vscode'):
                    if '__init__.py' not in files:
                        print(Clr.RED +
                              'Error: no __init__.py in package dir: ' + root +
                              Clr.RST)
                        sys.exit(255)

    def _update_visual_studio_project(self, fname: str, src_root: str) -> None:
        with open(fname) as infile:
            lines = infile.read().splitlines()

        # Hmm can we include headers in the project for easy access?
        # Seems VS attempts to compile them if we do so here.
        # all_files = sorted(src_files + header_files)
        # del header_files  # Unused.
        all_files = sorted([
            f for f in (self._source_files + self._header_files)
            if not f.endswith('.m') and not f.endswith('.mm')
            and not f.endswith('.c')
        ])

        # Find the ItemGroup containing stdafx.cpp. This is where we'll dump
        # our stuff.
        index = lines.index('    <ClCompile Include="stdafx.cpp">')
        begin_index = end_index = index
        while lines[begin_index] != '  <ItemGroup>':
            begin_index -= 1
        while lines[end_index] != '  </ItemGroup>':
            end_index += 1
        group_lines = lines[begin_index + 1:end_index]

        # Strip out any existing files from src/ballistica.
        group_lines = [
            l for l in group_lines if src_root + '\\ballistica\\' not in l
        ]

        # Now add in our own.
        # Note: we can't use C files in this build at the moment; breaks
        # precompiled header stuff. (shouldn't be a problem though).
        group_lines = [
            '    <' +
            ('ClInclude' if src.endswith('.h') else 'ClCompile') + ' Include="'
            + src_root + '\\ballistica' + src.replace('/', '\\') + '" />'
            for src in all_files
        ] + group_lines
        filtered = lines[:begin_index + 1] + group_lines + lines[end_index:]
        self._file_changes[fname] = '\r\n'.join(filtered) + '\r\n'

        self._update_visual_studio_project_filters(filtered, fname, src_root)

    def _update_visual_studio_project_filters(self, lines_in: List[str],
                                              fname: str,
                                              src_root: str) -> None:
        filterpaths: Set[str] = set()
        filterlines: List[str] = [
            '<?xml version="1.0" encoding="utf-8"?>',
            '<Project ToolsVersion="4.0"'
            ' xmlns="http://schemas.microsoft.com/developer/msbuild/2003">',
            '  <ItemGroup>',
        ]
        sourcelines = [l for l in lines_in if 'Include="' + src_root in l]
        for line in sourcelines:
            entrytype = line.strip().split()[0][1:]
            path = line.split('"')[1]
            filterlines.append('    <' + entrytype + ' Include="' + path +
                               '">')

            # If we have a dir foo/bar/eep we need to create filters for
            # each of foo, foo/bar, and foo/bar/eep
            splits = path[len(src_root):].split('\\')
            splits = [s for s in splits if s != '']
            splits = splits[:-1]
            for i in range(len(splits)):
                filterpaths.add('\\'.join(splits[:(i + 1)]))
            filterlines.append('      <Filter>' + '\\'.join(splits) +
                               '</Filter>')
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
        self._file_changes[fname +
                           '.filters'] = '\r\n'.join(filterlines) + '\r\n'

    def _update_visual_studio_projects(self) -> None:
        fname = 'ballisticacore-windows/BallisticaCore/BallisticaCore.vcxproj'
        if os.path.exists(fname):
            self._update_visual_studio_project(fname, '..\\..\\src')
        fname = ('ballisticacore-windows/BallisticaCoreHeadless/'
                 'BallisticaCoreHeadless.vcxproj')
        if os.path.exists(fname):
            self._update_visual_studio_project(fname, '..\\..\\src')
        fname = ('ballisticacore-windows/BallisticaCoreOculus'
                 '/BallisticaCoreOculus.vcxproj')
        if os.path.exists(fname):
            self._update_visual_studio_project(fname, '..\\..\\src')

    def _update_cmake_file(self, fname: str) -> None:

        with open(fname) as infile:
            lines = infile.read().splitlines()
        auto_start = lines.index('  #AUTOGENERATED_BEGIN (this section'
                                 ' is managed by the "update_project" tool)')
        auto_end = lines.index('  #AUTOGENERATED_END')
        our_lines = [
            '  ${BA_SRC_ROOT}/ballistica' + f
            for f in sorted(self._source_files + self._header_files)
            if not f.endswith('.mm') and not f.endswith('.m')
        ]
        filtered = lines[:auto_start + 1] + our_lines + lines[auto_end:]
        self._file_changes[fname] = '\n'.join(filtered) + '\n'

    def _update_cmake_files(self) -> None:
        fname = 'ballisticacore-cmake/CMakeLists.txt'
        if os.path.exists(fname):
            self._update_cmake_file(fname)
        fname = ('ballisticacore-android/BallisticaCore'
                 '/src/main/cpp/CMakeLists.txt')
        if os.path.exists(fname):
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
                    src_files.add(os.path.join(root, ftst)[len(scan_dir):])
                if any(ftst.endswith(ext) for ext in header_exts):
                    header_files.add(os.path.join(root, ftst)[len(scan_dir):])
        self._source_files = sorted(src_files)
        self._header_files = sorted(header_files)

    def _check_sync_states(self) -> None:
        # Make sure none of our sync targets have been mucked with since
        # their last sync.
        if os.system('tools/pcommand sync check') != 0:
            print(Clr.RED + 'Sync check failed; you may need to run "sync".' +
                  Clr.RST)
            sys.exit(255)

    def _update_assets_makefile(self) -> None:
        if os.system(f'tools/pcommand update_assets_makefile {self._checkarg}'
                     ) != 0:
            print(
                f'{Clr.RED}Error checking/updating assets Makefile.f{Clr.RST}')
            sys.exit(255)

    def _update_generated_code_makefile(self) -> None:
        if os.path.exists('tools/update_generated_code_makefile'):
            if os.system('tools/update_generated_code_makefile' +
                         self._checkarg) != 0:
                print(f'{Clr.RED}Error checking/updating'
                      f' generated-code Makefile{Clr.RED}')
                sys.exit(255)

    def _update_resources_makefile(self) -> None:
        if os.path.exists('tools/update_resources_makefile'):
            if os.system('tools/update_resources_makefile' +
                         self._checkarg) != 0:
                print(f'{Clr.RED}Error checking/updating'
                      f' resources Makefile.{Clr.RST}')
                sys.exit(255)

    def _update_python_enums_module(self) -> None:
        if os.path.exists('tools/update_python_enums_module'):
            if os.system('tools/update_python_enums_module' +
                         self._checkarg) != 0:
                print(f'{Clr.RED}Error checking/updating'
                      f' python enums module.{Clr.RST}')
                sys.exit(255)


# if __name__ == '__main__':
#     App().run()
