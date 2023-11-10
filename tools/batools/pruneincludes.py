# Released under the MIT License. See LICENSE for details.
#
"""Utility to scan for unnecessary includes in c++ files."""

from __future__ import annotations

import os
import json
import tempfile
from typing import TYPE_CHECKING
from dataclasses import dataclass
import subprocess

from efro.error import CleanError
from efro.terminal import Clr
from efro.dataclassio import dataclass_from_dict, ioprepped

if TYPE_CHECKING:
    pass


@ioprepped
@dataclass
class _CompileCommandsEntry:
    directory: str
    command: str
    file: str


class Pruner:
    """Wrangles a prune operation."""

    def __init__(self, commit: bool, paths: list[str]) -> None:
        self.commit = commit
        self.paths = paths

        # Files we're ok checking despite them containing #ifs.
        self.ifdef_check_whitelist = {
            'src/ballistica/shared/python/python.cc',
            'src/ballistica/base/assets/assets.cc',
            'src/ballistica/ui_v1/python/methods/python_methods_ui_v1.cc',
            'src/ballistica/scene_v1/support/scene.cc',
            'src/ballistica/scene_v1/support/scene_v1_app_mode.cc',
        }

        # Exact lines we never flag as removable.
        self.line_whitelist = {
            '#include "ballistica/mgen/pyembed/binding_ba.inc"'
        }

    def run(self) -> None:
        """Do the thing."""

        cwd = os.getcwd()

        if self.commit:
            print(f'{Clr.MAG}{Clr.BLD}RUNNING IN COMMIT MODE!!!{Clr.RST}')

        self._prep_paths()

        entries = self._get_entries()

        processed_paths = set[str]()

        with tempfile.TemporaryDirectory() as tempdir:
            for entry in entries:
                # Entries list might have repeats.
                if entry.file in processed_paths:
                    continue
                processed_paths.add(entry.file)

                if not entry.file.startswith(cwd):
                    raise CleanError(
                        f'compile-commands file {entry.file}'
                        f' does not start with cwd "{cwd}".'
                    )
                relpath = entry.file.removeprefix(cwd + '/')

                # Only process our stuff under the ballistica dir.
                if not relpath.startswith('src/ballistica/'):
                    continue

                # If we were given a list of paths, constrain to those.
                if self.paths:
                    if os.path.abspath(entry.file) not in self.paths:
                        continue

                # See what file the command will write so we can prep its dir.
                splits = entry.command.split(' ')
                outpath = splits[splits.index('-o') + 1]
                outdir = os.path.dirname(outpath)
                cmd = (
                    f'cd "{tempdir}" && mkdir -p "{outdir}" && {entry.command}'
                )
                self._check_file(relpath, cmd)

    def _prep_paths(self) -> None:
        # First off, make sure all our whitelist files still exist.
        # This will be a nice reminder to keep the list updated with
        # any changes.
        for wpath in self.ifdef_check_whitelist:
            if not os.path.isfile(wpath):
                raise CleanError(
                    f"ifdef-check-whitelist entry does not exist: '{wpath}'."
                )

        # If we were given paths, make sure they exist and convert to absolute.
        if self.paths:
            for path in self.paths:
                if not os.path.exists(path):
                    raise CleanError(f'path not found: "{path}"')
            self.paths = [os.path.abspath(p) for p in self.paths]

    def _get_entries(self) -> list[_CompileCommandsEntry]:
        cmdspath = '.cache/compile_commands_db/compile_commands.json'
        if not os.path.isfile(cmdspath):
            raise CleanError(
                f'Compile-commands not found at "{cmdspath}".'
                f' do you have the irony build db enabled? (see Makefile)'
            )
        with open(cmdspath, encoding='utf-8') as infile:
            cmdsraw = json.loads(infile.read())
        if not isinstance(cmdsraw, list):
            raise CleanError(
                f'Expected list for compile-commands;'
                f' found {type(cmdsraw)}.'
            )
        return [dataclass_from_dict(_CompileCommandsEntry, e) for e in cmdsraw]

    def _check_file(self, path: str, cmd: str) -> None:
        """Run all checks on an individual file."""
        # pylint: disable=too-many-locals

        with open(path, encoding='utf-8') as infile:
            orig_contents = infile.read()
        orig_lines = orig_contents.splitlines(keepends=True)

        # If there's any conditional compilation in there, skip. Code that
        # isn't getting compiled by default could be using something from
        # an include.
        for i, line in enumerate(orig_lines):
            if (
                line.startswith('#if')
                and path not in self.ifdef_check_whitelist
            ):
                print(
                    f'Skipping {Clr.YLW}{path}{Clr.RST} due to line'
                    f' {i+1}: {line[:-1]}'
                )
                return
        includelines: list[int] = []
        for i, line in enumerate(orig_lines):
            if line.startswith('#include "') and line.strip().endswith('.h"'):
                includelines.append(i)

        # Remove any includes of our associated header file.
        # (we want to leave those in even if its technically not necessary).
        bpath = path.removeprefix('src/')
        our_header = '#include "' + os.path.splitext(bpath)[0] + '.h"\n'
        includelines = [h for h in includelines if orig_lines[h] != our_header]

        print(f'Processing {Clr.BLD}{Clr.BLU}{path}{Clr.RST}...')
        working_lines = orig_lines
        completed = False

        # First run the compile unmodified just to be sure it works.
        success = (
            subprocess.run(
                cmd, shell=True, check=False, capture_output=True
            ).returncode
            == 0
        )
        if not success:
            print(
                f'  {Clr.RED}{Clr.BLD}Initial test compile failed;'
                f' something is probably wrong.{Clr.RST}'
            )

        try:
            # Go through backwards because then removing a line doesn't
            # invalidate our next lines to check.
            for i, lineno in enumerate(reversed(includelines)):
                test_lines = working_lines.copy()
                print(f'  Checking include {i+1} of {len(includelines)}...')
                removed_line = test_lines.pop(lineno).removesuffix('\n')

                with open(path, 'w', encoding='utf-8') as outfile:
                    outfile.write(''.join(test_lines))
                success = (
                    subprocess.run(
                        cmd, shell=True, check=False, capture_output=True
                    ).returncode
                    == 0
                    and removed_line not in self.line_whitelist
                )
                if success:
                    working_lines = test_lines
                    print(
                        f'  {Clr.GRN}{Clr.BLD}Line {lineno+1}'
                        f' seems to be removable:{Clr.RST} {removed_line}'
                    )
            completed = True

        finally:
            if not completed:
                print(f'  {Clr.RED}{Clr.BLD}Error processing file.{Clr.RST}')

            # Restore original if we're not committing or something went wrong.
            if not self.commit or not completed:
                with open(path, 'w', encoding='utf-8') as outfile:
                    outfile.write(orig_contents)

            # Otherwise restore the latest working version if committing.
            elif self.commit:
                with open(path, 'w', encoding='utf-8') as outfile:
                    outfile.write(''.join(working_lines))
