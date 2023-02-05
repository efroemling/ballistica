# Released under the MIT License. See LICENSE for details.
#
"""Functionality used for building."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import TYPE_CHECKING

from efro.terminal import Clr

if TYPE_CHECKING:
    from typing import Callable


class Lazybuild:
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
        dirfilter: Callable[[str, str], bool] | None = None,
        filefilter: Callable[[str, str], bool] | None = None,
        srcpaths_fullclean: list[str] | None = None,
        command_fullclean: str | None = None,
    ) -> None:
        self.target = target
        self.srcpaths = srcpaths
        self.command = command
        self.dirfilter = dirfilter
        self.filefilter = filefilter
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

        self.have_fullclean_changes = False
        self.have_changes = False
        self.total_unchanged_count = 0

        # We support a mechanism where some paths can be passed as 'fullclean'
        # paths - these will trigger a separate 'fullclean' command as well as
        # the regular command when any of them change. This is handy for 'meta'
        # type builds where a lot of tools scripts can conceivably influence
        # target creation, but where it would be unwieldy to list all of them
        # as sources in a Makefile.
        self.srcpaths_fullclean = srcpaths_fullclean
        self.command_fullclean = command_fullclean
        if (self.srcpaths_fullclean is None) != (
            self.command_fullclean is None
        ):
            raise RuntimeError(
                'Must provide both srcpaths_fullclean and'
                ' command_fullclean together'
            )

    def run(self) -> None:
        """Do the thing."""

        self._check_paths()

        if self.have_fullclean_changes:
            assert self.command_fullclean is not None
            print(
                f'{Clr.MAG}Lazybuild: full-clean input changed;'
                f' running {Clr.BLD}{self.command_fullclean}.{Clr.RST}'
            )
            subprocess.run(self.command_fullclean, shell=True, check=True)

        if self.have_changes:
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
        else:
            print(
                f'{Clr.BLU}Lazybuild: skipping "{self.target_name_pretty}"'
                f' ({self.total_unchanged_count} inputs unchanged).{Clr.RST}'
            )

    def _check_paths(self) -> None:
        # First check our fullclean paths if we have them.
        # any changes here will kick off a full-clean and then a build.
        if self.srcpaths_fullclean is not None:
            for srcpath in self.srcpaths_fullclean:
                src_did_change, src_unchanged_count = self._check_path(srcpath)
                if src_did_change:
                    self.have_fullclean_changes = True
                    self.have_changes = True
                    return  # Can stop as soon as we find a change.
                self.total_unchanged_count += src_unchanged_count

        # Ok; no fullclean changes found. Now check our regular paths.
        # Any changes here just trigger a regular build.
        for srcpath in self.srcpaths:
            src_did_change, src_unchanged_count = self._check_path(srcpath)
            if src_did_change:
                self.have_changes = True
                return  # Can stop as soon as we find a change.
            self.total_unchanged_count += src_unchanged_count

    def _check_path(self, srcpath: str) -> tuple[bool, int]:
        """Return whether path has changed and unchanged file count if not."""
        unchanged_count = 0

        # Add files verbatim; recurse through dirs.
        if os.path.isfile(srcpath):
            if self._test_path(srcpath):
                return True, 0
            unchanged_count += 1
            return False, unchanged_count
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
                    return True, 0
                unchanged_count += 1
        return False, unchanged_count

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
        # Now see this path is newer than our target..
        if self.mtime is None or os.path.getmtime(path) >= self.mtime:
            print(
                f'{Clr.MAG}Lazybuild: '
                f'{Clr.BLD}{self.target_name_pretty}{Clr.RST}{Clr.MAG}'
                f' build'
                f' triggered by change in {Clr.BLD}{path}{Clr.RST}{Clr.MAG}'
                f'.{Clr.RST}'
            )
            return True
        return False
