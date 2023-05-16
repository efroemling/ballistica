# Released under the MIT License. See LICENSE for details.
#
"""Checks we can run on the overall project state."""

from __future__ import annotations

from typing import TYPE_CHECKING
from pathlib import Path
import subprocess
import os

from efro.error import CleanError
from efro.terminal import Clr
from efrotools import get_public_license, PYVER

if TYPE_CHECKING:
    from batools.project._updater import ProjectUpdater
    from batools.featureset import FeatureSet


def _get_legal_notice_private() -> str:
    """Return the one line legal notice we expect private files to have."""
    return 'Copyright (c) 2011-2022 Eric Froemling'


def check_source_files(self: ProjectUpdater) -> None:
    """Check project source files."""
    for fsrc in self.source_files:
        if fsrc.endswith('.cpp') or fsrc.endswith('.cxx'):
            raise RuntimeError('please use .cc for c++ files; found ' + fsrc)

        # Watch out for in-progress emacs edits.
        # Could just ignore these but it probably means I intended
        # to save something and forgot.
        if '/.#' in fsrc:
            raise CleanError(f'Found an unsaved emacs file: "{fsrc}".')

        fname = 'src/ballistica' + fsrc
        _check_source_file(self, fname)


def _check_source_file(self: ProjectUpdater, fname: str) -> None:
    with open(os.path.join(self.projroot, fname), encoding='utf-8') as infile:
        lines = infile.read().splitlines()

    if self.license_line_checks:
        _check_c_license(self, fname, lines)

    _source_file_feature_set_namespace_check(self, fname, lines)


def _source_file_feature_set_namespace_check(
    self: ProjectUpdater, fname: str, lines: list[str]
) -> None:
    """Make sure C++ code uses correct namespaces based on its location."""
    # pylint: disable=too-many-branches
    # if bool(True):
    #     return

    # Extensions we know we're skipping.
    if any(fname.endswith(x) for x in ['.c', '.swift']):
        return

    if not any(fname.endswith(x) for x in ['.cc', '.h', '.mm']):
        raise CleanError(f"Unrecognized source file type: '{fname}'.")

    splits = fname.split('/')
    assert len(splits) >= 3  # should be at least src, ballistica, foo
    toplevelname = splits[2]

    # Make sure FOO in src/ballistica/FOO corresponds to a feature-set.
    # (or one of our reserved names).
    reserved_names = {'shared'}
    feature_set = self.feature_sets.get(toplevelname)

    if toplevelname not in reserved_names and feature_set is None:
        raise CleanError(
            f"{toplevelname} in path '{fname}' does not correspond"
            ' to a feature-set.'
        )

    # If the feature-set lists these files as to-be-ignored, ignore.
    if (
        feature_set is not None
        and fname in feature_set.cpp_namespace_check_disable_files
    ):
        return

    # Ignore ballistica.h/cc for now
    if len(splits) == 3:
        return

    # Anything under shared should only use ballistica namespace.
    if splits[2] == 'shared':
        for i, line in enumerate(lines):
            if line.startswith('namespace '):
                namespace, predecs_only = _get_namespace_info(lines, i)
                if namespace != 'ballistica' and not predecs_only:
                    raise CleanError(
                        f'Invalid line "{line}" at {fname} line {i+1}.\n'
                        f"Files under 'shared' should use only ballistica"
                        f' namespace.'
                    )
        return

    # Anything else should use only the featureset namespace.
    for i, line in enumerate(lines):
        if line.startswith('namespace '):
            namespace, predecs_only = _get_namespace_info(lines, i)
            if namespace != f'ballistica::{toplevelname}' and not predecs_only:
                raise CleanError(
                    f'Invalid line "{line}" at {fname} line {i+1}.\n'
                    f"This file is associated with the '{toplevelname}'"
                    ' FeatureSet so should be using the'
                    f" 'ballistica::{toplevelname}' namespace."
                )


def _get_namespace_info(lines: list[str], index: int) -> tuple[str, bool]:
    """Given a line no, return name of namespace declared and whether it
    is only predeclares."""
    assert lines[index].startswith('namespace ')
    # Special case: single-line empty declaration.
    splits = lines[index].split()
    assert splits[0] == 'namespace'
    if '{}' in lines[index]:
        assert splits[2] == '{}'
        # Not considering this a predeclare statement since it doesn't need to
        # be there.
        return splits[1], False
    assert splits[2] == '{'
    name = splits[1]
    # Now scan lines until we find the close or a non-predeclare statement
    index += 1
    while True:
        if lines[index].startswith('}'):
            return name, True
        if not (
            lines[index].startswith('class ') and lines[index].endswith(';')
        ):
            # Found a non-predeclare statement
            return name, False
        index += 1


def check_headers(self: ProjectUpdater) -> None:
    """Check all project headers."""
    for header_file_raw in self.header_files:
        assert header_file_raw[0] == '/'
        header_file = f'src/ballistica{header_file_raw}'
        if header_file.endswith('.h'):
            _check_header(self, header_file)


def _check_header(self: ProjectUpdater, fname: str) -> None:
    # Make sure its define guard is correct.
    guard = fname[4:].upper().replace('/', '_').replace('.', '_') + '_'
    with open(os.path.join(self.projroot, fname), encoding='utf-8') as fhdr:
        lines = fhdr.read().splitlines()

    if self.license_line_checks:
        _check_c_license(self, fname, lines)

    _source_file_feature_set_namespace_check(self, fname, lines)

    # Check for header guard lines at top
    line = f'#ifndef {guard}'
    lnum = 2
    if lines[lnum] != line:
        # Allow auto-correcting if it looks close already
        # (don't want to blow away an unrelated line)
        allow_auto = lines[lnum].startswith('#ifndef BALLISTICA_')
        self.add_line_correction(
            fname,
            line_number=lnum,
            expected=line,
            can_auto_update=allow_auto,
        )
    line = f'#define {guard}'
    lnum = 3
    if lines[lnum] != line:
        # Allow auto-correcting if it looks close already
        # (don't want to blow away an unrelated line)
        allow_auto = lines[lnum].startswith('#define BALLISTICA_')
        self.add_line_correction(
            fname,
            line_number=lnum,
            expected=line,
            can_auto_update=allow_auto,
        )

    # Check for header guard at bottom
    line = f'#endif  // {guard}'
    lnum = len(lines) - 1
    if lines[lnum] != line:
        # Allow auto-correcting if it looks close already
        # (don't want to blow away an unrelated line)
        allow_auto = lines[lnum].startswith('#endif  // BALLISTICA_')
        self.add_line_correction(
            fname,
            line_number=lnum,
            expected=line,
            can_auto_update=allow_auto,
        )


def _check_c_license(
    self: ProjectUpdater, fname: str, lines: list[str]
) -> None:
    # Look for public license line (public or private repo) or private
    # license line (private repo only)
    line_private = '// ' + _get_legal_notice_private()
    line_public = get_public_license('c++')
    lnum = 0

    if self.public:
        if lines[lnum] != line_public:
            # Allow auto-correcting from private to public line
            allow_auto = lines[lnum] == line_private
            self.add_line_correction(
                fname,
                line_number=lnum,
                expected=line_public,
                can_auto_update=allow_auto,
            )
    else:
        if lines[lnum] not in [line_public, line_private]:
            self.add_line_correction(
                fname,
                line_number=lnum,
                expected=line_private,
                can_auto_update=False,
            )


def check_makefiles(self: ProjectUpdater) -> None:
    """Check all project makefiles."""

    # Run a few sanity checks on whatever makefiles we come across.
    fpaths = (
        subprocess.run(
            ['find', self.projroot, '-maxdepth', '3', '-name', 'Makefile'],
            capture_output=True,
            check=True,
        )
        .stdout.decode()
        .split()
    )

    # Ignore stuff in the build dir such as cmake-generated ones.
    fpaths = [
        n
        for n in fpaths
        if not n.startswith(os.path.join(self.projroot, 'build'))
    ]

    for fpath in fpaths:
        with open(fpath, encoding='utf-8') as infile:
            makefile = infile.read()

        # Make sure public repo is public-license only.
        if self.public:
            public_license = get_public_license('makefile')
            if public_license not in makefile:
                raise CleanError(f'Pub license not found in {fpath}.')
        # Allow both public and private license in private repo.
        else:
            if (
                _get_legal_notice_private() not in makefile
                and get_public_license('makefile') not in makefile
            ):
                raise CleanError(f'Priv or pub legal not found in {fpath}.')


def check_python_files(self: ProjectUpdater) -> None:
    """Check all project python files."""
    from efrotools.code import get_script_filenames

    scriptfiles = get_script_filenames(Path(self.projroot))
    for fname in scriptfiles:
        _check_python_file(self, fname)

    packagedirs: list[str] = []

    # Assume all dirs under these dirs are Python packages...
    dirs_of_packages = [
        'tools',
        'tests',
        'src/assets/ba_data/python',
        'src/meta',
    ]
    # EXCEPT for the following specifics.
    ignores: dict[str, set[str]] = {
        'tools': {
            'make_bob',
            'mali_texture_compression_tool',
            'nvidia_texture_tools',
            'powervr_tools',
        }
    }
    for dir_of_packages in dirs_of_packages:
        for name in os.listdir(os.path.join(self.projroot, dir_of_packages)):
            if name in ignores.get(dir_of_packages, {}):
                continue
            fullpath = os.path.join(self.projroot, dir_of_packages, name)
            if not name.startswith('.') and os.path.isdir(fullpath):
                packagedirs.append(fullpath)

    for packagedir in packagedirs:
        # Special case: if this dir contains ONLY __pycache__ dirs and
        # hidden files like .DS_Store, blow it away. It probably is left
        # over bits from a since-removed-or-renamed package.
        if _contains_only_pycache_and_cruft(packagedir):
            print(
                f"{Clr.MAG}NOTE: Directory '{packagedir}' contains only"
                ' __pycache__ and hidden files/dirs; assuming it is'
                ' left over from a deleted package and blowing it away.'
                f'{Clr.RST}'
            )
            subprocess.run(['rm', '-rf', packagedir], check=True)

        for root, dirs, files in os.walk(packagedir, topdown=True):
            # Skip over hidden and pycache dirs.
            for dirname in dirs:
                if dirname.startswith('.'):
                    dirs.remove(dirname)
            if '__pycache__' in dirs:
                dirs.remove('__pycache__')

            # Check our packages and make sure all subdirs contain an
            # __init__.py (I tend to forget this sometimes).
            if '__init__.py' not in files:
                raise CleanError(
                    f'No __init__.py under (presumed)'
                    f" Python package dir: '{root}'."
                )


def _check_python_file(self: ProjectUpdater, fname: str) -> None:
    # pylint: disable=too-many-branches

    with open(fname, encoding='utf-8') as infile:
        contents = infile.read()
        lines = contents.splitlines()

    # Make sure all standalone scripts are pointing to the right version
    # of Python (with a few exceptions where it needs to differ)
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
        # FIXME: update this for the new feature-set world. Perhaps we
        #  can screen for imports based on feature-set dependencies or
        #  perhaps we should not even try and just let feature-set test
        #  builds catch problems like that.
        if bool(False):
            # Stuff under the babase module.
            if '/babase/' in fname:
                # Don't allow importing ba at the top level from within babase.
                if line == 'import babase':
                    raise CleanError(
                        f'{fname}:{i+1}: no top level babase imports allowed'
                        f' under babase module.'
                    )
            if '/bastd/' in fname:
                # Don't allow importing _babase or _baplus anywhere here.
                # (any internal needs should be in babase.internal)
                if 'import _babase' in line:
                    raise CleanError(
                        f'{fname}:{i+1}: _babase or _baplus imports not'
                        f' allowed under bastd.'
                    )

    # In all cases, look for our one-line legal notice.
    # In the public case, look for the rest of our public license too.
    if self.license_line_checks:
        public_license = get_public_license('python')
        private_license = '# ' + _get_legal_notice_private()
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

        if self.public:
            if lines[lnum] != public_license:
                raise CleanError(
                    f'License text not found'
                    f" at '{fname}' line {lnum+1};"
                    f' please correct.\n'
                    f'Expected text is: {public_license}\n'
                    f'{disable_note}'
                )
        else:
            if lines[lnum] != public_license and lines[lnum] != private_license:
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


def _contains_only_pycache_and_cruft(path: str) -> bool:
    for _root, dirs, files in os.walk(path, topdown=True):
        # Skip over hidden and pycache dirs.
        for dirname in dirs:
            if dirname.startswith('.'):
                dirs.remove(dirname)
        if '__pycache__' in dirs:
            dirs.remove('__pycache__')

        # Return as soon as we find a single non-hidden file.
        for fname in files:
            if not fname.startswith('.'):
                return False

    # Welp.. found no normal files; just pycache and cruft.
    return True


def check_sync_states(self: ProjectUpdater) -> None:
    """Make sure project sync states are ok."""

    # Assuming nobody else will be using sync system.
    if self.public:
        return

    # Make sure none of our sync targets have been mucked with since
    # their last sync.
    if (
        subprocess.run(
            [os.path.join(self.projroot, 'tools/pcommand'), 'sync', 'check'],
            check=False,
        ).returncode
        != 0
    ):
        raise CleanError('Sync check failed; you may need to run "sync".')


def check_misc(self: ProjectUpdater) -> None:
    """Check misc project stuff."""

    # Make sure we're set to prod master server. (but ONLY when
    # checking; still want to be able to run updates).
    if not self.public and self.check and 'plus' in self.feature_sets:
        with open(
            os.path.join(
                self.projroot,
                'src/ballistica/plus/support/master_server_config.h',
            ),
            encoding='utf-8',
        ) as infile:
            msconfig = infile.read()
            if (
                '// V2 Master Server:\n' '\n' '// PROD\n' '#if 1\n'
            ) not in msconfig:
                raise CleanError('Not using prod v2 master server.')
