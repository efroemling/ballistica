# Released under the MIT License. See LICENSE for details.
#
"""Functionality used for building."""

from __future__ import annotations

import os
import time
import subprocess
from pathlib import Path
from typing import TYPE_CHECKING


# Pylint's preferred import order here seems non-deterministic (as of 2.17.2).
# pylint: disable=useless-suppression
# pylint: disable=wrong-import-order
from efro.terminal import Clr
from efrotools.buildlock import BuildLock
from efrotools import get_string_hash

# pylint: enable=wrong-import-order
# pylint: enable=useless-suppression

if TYPE_CHECKING:
    from typing import Callable


class LazyBuildContext:
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

    def __init__(
        self,
        target: str,
        srcpaths: list[str],
        command: str,
        buildlockname: str | None = None,
        dirfilter: Callable[[str, str], bool] | None = None,
        filefilter: Callable[[str, str], bool] | None = None,
        srcpaths_fullclean: list[str] | None = None,
        manifest_file: str | None = None,
        command_fullclean: str | None = None,
    ) -> None:
        self.target = target
        self.srcpaths = srcpaths
        self.command = command
        self.dirfilter = dirfilter
        self.filefilter = filefilter
        self.buildlockname = buildlockname
        self.mtime = (
            None
            if not os.path.exists(self.target)
            else os.path.getmtime(self.target)
        )

        # Show prettier names for lazybuild cache dir targets.
        if target.startswith('.cache/lazybuild/'):
            self.target_name_pretty = target[len('.cache/lazybuild/') :]
        else:
            self.target_name_pretty = target

        self.have_changes = False
        self.have_fullclean_changes = False
        self.total_unchanged_count = 0
        self.printed_trigger = False

        # We support a mechanism where some paths can be passed as 'fullclean'
        # paths - these will trigger a separate 'fullclean' command as well as
        # the regular command when any of them change. This is handy for 'meta'
        # type builds where a lot of tools scripts can conceivably influence
        # target creation, but where it would be unwieldy to list all of them
        # as dependency relationships in a Makefile.
        self.srcpaths_fullclean = srcpaths_fullclean
        self.command_fullclean = command_fullclean

        # We also support a 'manifest' file which is a hash of all filenames
        # processed as part of srcpaths OR srcpaths_fullclean. If defined,
        # any changes in this hash will result in the full-clean-command
        # being run. This is useful for blowing away old output files when
        # source files are removed.
        self.manifest_file = manifest_file

    def run(self) -> None:
        """Do the thing."""
        starttime = time.monotonic()

        self._check_for_changes()

        if self.have_changes:
            # If we were given a build-lock-name, surround our payload
            # with a build-lock. This can be used as a sanity-check to make
            # sure that only one build for some given purpose is being run at
            # once.
            if self.buildlockname is not None:
                with BuildLock(self.buildlockname):
                    self._run_commands_and_update_target()
            else:
                self._run_commands_and_update_target()

        else:
            duration = time.monotonic() - starttime
            print(
                f'{Clr.BLU}Lazybuild: skipping "{self.target_name_pretty}"'
                f' (checked {self.total_unchanged_count} inputs'
                f' in {duration:.2}s).{Clr.RST}'
            )

    def _run_commands_and_update_target(self) -> None:
        assert self.have_changes

        if self.have_fullclean_changes:
            assert self.command_fullclean is not None
            print(
                f'{Clr.MAG}Lazybuild:'
                f' {Clr.SCYN}{Clr.BLD}full-clean{Clr.RST}'
                f'{Clr.MAG} input changed;'
                f' running {Clr.BLD}{self.command_fullclean}.{Clr.RST}',
                flush=True,
            )
            subprocess.run(self.command_fullclean, shell=True, check=True)

        subprocess.run(self.command, shell=True, check=True)

        # Complain if the target path does not exist at this point.
        # (otherwise we'd create an empty file there below which can
        # cause problems).
        # We make a special exception for files under .cache/lazybuild
        # since those are not actually meaningful files; only used for
        # dep tracking.
        if not self.target.startswith(
            '.cache/lazybuild'
        ) and not os.path.isfile(self.target):
            raise RuntimeError(
                f'Expected output file \'{self.target}\' not found'
                f' after running lazybuild command:'
                f' \'{self.command}\'.'
            )

        # We also explicitly update the mod-time of the target;
        # the command we (such as a VM build) may not have actually
        # done anything but we still want to update our target to
        # be newer than all the lazy sources.
        os.makedirs(os.path.dirname(self.target), exist_ok=True)
        Path(self.target).touch()

    def _check_for_changes(self) -> None:
        manfile = self.manifest_file
        # If we're watching for file adds/removes/renames in addition
        # to just modtimes, build a set of all files we come across.
        man_input_paths = set[str]() if manfile is not None else None

        # First check our fullclean paths if we have them.
        # any changes here will kick off a full-clean and then a build.
        if self.srcpaths_fullclean is not None:
            for srcpath in self.srcpaths_fullclean:
                src_did_change, src_unchanged_count = self._check_path(
                    srcpath, man_input_paths
                )
                if src_did_change:
                    self.have_changes = True
                    self.have_fullclean_changes = True

                    # If we're *not* building a manifest
                    # we can bail on the first difference.
                    if manfile is None:
                        return
                self.total_unchanged_count += src_unchanged_count

        # Now check our regular paths.
        # Any changes here just trigger a regular build.
        for srcpath in self.srcpaths:
            src_did_change, src_unchanged_count = self._check_path(
                srcpath, man_input_paths
            )
            if src_did_change:
                self.have_changes = True
                # If we're *not* building a manifest
                # we can bail on the first difference.
                if manfile is None:
                    return
            self.total_unchanged_count += src_unchanged_count

        # If we built a manifest, check/write it and kick off
        # a full-clean if anything differed.
        if manfile is not None:
            assert man_input_paths is not None
            # Need to sort to keep this deterministic.
            hashstr = get_string_hash('\n'.join(sorted(man_input_paths)))
            try:
                with open(manfile, encoding='utf-8') as infile:
                    existing_hash = infile.read()
            except FileNotFoundError:
                existing_hash = None
            if hashstr != existing_hash:
                # Manifest changed; write new one and mark us changed.
                os.makedirs(os.path.dirname(manfile), exist_ok=True)
                with open(manfile, 'w', encoding='utf-8') as outfile:
                    outfile.write(hashstr)
                self.have_changes = True
                self.have_fullclean_changes = True

    def _check_path(
        self, srcpath: str, manifest_paths: set[str] | None
    ) -> tuple[bool, int]:
        """Return whether path has changed and unchanged file count if not."""
        unchanged_count = 0

        # Add files verbatim; recurse through dirs.
        if os.path.isfile(srcpath):
            if self._test_path(srcpath):
                return True, 0
            unchanged_count += 1
            return False, unchanged_count

        results: tuple[bool, int] | None = None

        for root, dirnames, fnames in os.walk(srcpath, topdown=True):
            # In top-down mode we can modify dirnames in-place to
            # prevent recursing into them at all.
            for dirname in list(dirnames):  # (make a copy)
                if not self._default_dir_filter(root, dirname) or (
                    self.dirfilter is not None
                    and not self.dirfilter(root, dirname)
                ):
                    dirnames.remove(dirname)

            for fname in fnames:
                if not self._default_file_filter(root, fname) or (
                    self.filefilter is not None
                    and not self.filefilter(root, fname)
                ):
                    continue
                fpath = os.path.join(root, fname)

                # For now don't wanna worry about supporting spaces.
                if ' ' in fpath:
                    raise RuntimeError(f'Invalid path with space: {fpath}')

                if self._test_path(fpath):
                    results = (True, 0)

                    # If we're not building a manifest we can bail
                    # immediately on a negative result.
                    if manifest_paths is None:
                        return results

                # Add files to any manifest set we're building.
                if manifest_paths is not None:
                    manifest_paths.add(fpath)

                unchanged_count += 1

        # If we got here with no negatives, succeed.
        if results is None:
            results = (False, unchanged_count)

        return results

    def _default_dir_filter(self, root: str, dirname: str) -> bool:
        del root  # Unused.

        # Ignore hidden dirs.
        if dirname.startswith('.'):
            return False

        # Ignore Python caches.
        if dirname == '__pycache__':
            return False

        return True

    def _default_file_filter(self, root: str, fname: str) -> bool:
        del root  # Unused.

        # Ignore hidden files.
        if fname.startswith('.'):
            return False

        return True

    def _test_path(self, path: str) -> bool:
        # Now see this path is newer than our target.
        if self.mtime is None or os.path.getmtime(path) > self.mtime:
            # Only announce trigger condition once.
            if not self.printed_trigger:
                self.printed_trigger = True
                print(
                    f'{Clr.MAG}Lazybuild: '
                    f'{Clr.BLD}{self.target_name_pretty}{Clr.RST}{Clr.MAG}'
                    f' build triggered by change in '
                    f'{Clr.BLD}{path}{Clr.RST}{Clr.MAG}.{Clr.RST}',
                    flush=True,
                )
            return True
        return False
