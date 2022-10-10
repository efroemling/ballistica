# Released under the MIT License. See LICENSE for details.
#
"""Provides a system for caching linting/formatting operations."""

from __future__ import annotations

import json
import os
from typing import TYPE_CHECKING

# Pylint's preferred import order here seems non-deterministic (as of 2.10.1).
# pylint: disable=useless-suppression
# pylint: disable=wrong-import-order
from efro.terminal import Clr
from efrotools import get_files_hash

# pylint: enable=wrong-import-order
# pylint: enable=useless-suppression

if TYPE_CHECKING:
    from typing import Sequence, Any
    from pathlib import Path


class FileCache:
    """A cache of file hashes/etc. used in linting/formatting/etc."""

    def __init__(self, path: Path):
        self._path = path
        self.curhashes: dict[str, str | None] = {}
        self.mtimes: dict[str, float] = {}
        self.entries: dict[str, Any]
        if not os.path.exists(path):
            self.entries = {}
        else:
            with open(path, 'r', encoding='utf-8') as infile:
                self.entries = json.loads(infile.read())

    def update(self, filenames: Sequence[str], extrahash: str) -> None:
        """Update the cache for the provided files and hash type.

        Hashes will be checked for all files (incorporating extrahash)
        and mismatched hash values cleared. Entries for no-longer-existing
        files will be cleared as well.
        """

        # First, completely prune entries for nonexistent files.
        self.entries = {
            path: val
            for path, val in self.entries.items()
            if os.path.isfile(path)
        }

        # Also remove any not in our passed list.
        self.entries = {
            path: val for path, val in self.entries.items() if path in filenames
        }

        # Add empty entries for files that lack them.
        # Also check and store current hashes for all files and clear
        # any entry hashes that differ so we know they're dirty.
        for filename in filenames:
            if filename not in self.entries:
                self.entries[filename] = {}
            self.curhashes[filename] = curhash = get_files_hash(
                [filename], extrahash
            )
            # Also store modtimes; we'll abort cache writes if
            # anything changed.
            self.mtimes[filename] = os.path.getmtime(filename)
            entry = self.entries[filename]
            if 'hash' in entry and entry['hash'] != curhash:
                del entry['hash']

    def get_dirty_files(self) -> Sequence[str]:
        """Return paths for all entries with no hash value."""

        return [
            key for key, value in self.entries.items() if 'hash' not in value
        ]

    def mark_clean(self, files: Sequence[str]) -> None:
        """Marks provided files as up to date."""
        for fname in files:
            self.entries[fname]['hash'] = self.curhashes[fname]

            # Also update their registered mtimes.
            self.mtimes[fname] = os.path.getmtime(fname)

    def write(self) -> None:
        """Writes the state back to its file."""

        # Check all file mtimes against the ones we started with;
        # if anything has been modified, don't write.
        for fname, mtime in self.mtimes.items():
            if os.path.getmtime(fname) != mtime:
                print(
                    f'{Clr.MAG}File changed during run:'
                    f' "{fname}"; cache not updated.{Clr.RST}'
                )
                return
        out = json.dumps(self.entries)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with self._path.open('w') as outfile:
            outfile.write(out)
