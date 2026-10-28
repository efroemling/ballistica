# Released under the MIT License. See LICENSE for details.
#
"""Caching of ``# ba_meta`` scan results between scans.

.. warning::

  This is an internal api and subject to change at any time. Do not use
  it in mod code.

Used by ``bacommon.metascan.DirectoryScan``; see ``ScanCache``.
Standard library only, like the scanner.
"""

import os
import json
import logging
import zipimport
import threading
from dataclasses import dataclass, field

#: IMPORTANT: Bump this whenever what :class:`ScanCache` stores, or what
#: a module's outcome is (anything in how a module's source turns into
#: results), changes. Cached outcomes are otherwise trusted as long as
#: the module's own identity matches, even across app updates, so
#: without a bump, results from older scanner code would linger.
CACHE_FORMAT_VERSION = 2

#: Files modified at or before this (ns since epoch) have 'frozen'
#: mtimes: flatpak (ostree) installs give every file 0 and nix 1, in
#: every version, so mtime can't tell versions apart. Matches
#: ``baenv.frozen_source_mtimes()``.
FROZEN_MTIME_NS = 1_000_000_000


@dataclass
class ModuleOutcome:
    """What scanning a single module contributes to the results."""

    #: Whether to scan the module's submodules (packages only).
    recurse: bool = False
    #: (export-type, class-path) pairs, in source order.
    exports: list[tuple[str, str]] = field(default_factory=list)
    #: (asset-package-version-number, module-name) pairs.
    asset_packages: list[tuple[int, str]] = field(default_factory=list)
    #: Skipped for requiring a different api version (logs a warning).
    incorrect_api: bool = False
    #: Something about the module was malformed (logs a warning).
    announce: bool = False

    @property
    def cacheable(self) -> bool:
        """Can this be reused next time (it logged nothing)?"""
        return not self.incorrect_api and not self.announce

    def to_wire(self) -> list:
        """Compact json-friendly form (cacheable outcomes only)."""
        assert self.cacheable
        return [
            self.recurse,
            [list(e) for e in self.exports],
            [list(a) for a in self.asset_packages],
        ]

    @classmethod
    def from_wire(cls, wire: list) -> ModuleOutcome:
        """Inverse of :meth:`to_wire`."""
        recurse, exports, asset_packages = wire
        return cls(
            recurse=bool(recurse),
            exports=[(str(t), str(c)) for t, c in exports],
            asset_packages=[(int(a), str(m)) for a, m in asset_packages],
        )


class ScanCache:
    """Per-module scan outcomes remembered from one scan to the next.

    Reading and parsing every module's source is most of what a scan
    costs, and from one launch to the next almost none of it changes.
    A module's outcome is reused only while its identity still matches:
    size and modification time for plain files (the rule Python itself
    uses to decide a ``.pyc`` is stale, so any edit that makes Python
    recompile a module makes us rescan it) or size and CRC32 for zip
    archive entries. Modules whose scan logged a warning are never
    cached, so warnings show up on every scan.

    Some installs freeze every file's modification time (flatpak at 0,
    nix at 1) so it says nothing about versions. Like our ``.pyc``
    cache, files like that are keyed by ``frozen_salt`` instead (pass
    something that changes with each install version, such as the
    app's build number); without one, they're never cached.

    Entries not used by the most recent scan are dropped on save, so
    the cache prunes itself as modules come and go.

    A *seed* (see :meth:`load_seed`) is a cache precomputed at build
    time, shipped with an app that keeps its Python in a zip archive
    (an Android apk). Its entries are keyed by content (size and CRC32)
    like any zip entry's, so they can only ever match files identical
    to the ones they were computed from; it gives a first launch with
    no cache yet a warm start.
    """

    def __init__(self, frozen_salt: str | None = None) -> None:
        self.frozen_salt = frozen_salt
        #: Lookups that found a reusable outcome / that didn't (for
        #: diagnostics and tests).
        self.hits = 0
        self.misses = 0
        #: Of the hits, how many came from the seed.
        self.seed_hits = 0
        #: Misses broken down by scan-path alias (the part of an entry
        #: name before its ':').
        self.misses_by_alias: dict[str, int] = {}
        self._warned_garbled = False
        self._entries: dict[str, list] = {}
        self._loaded_salt: str | None = None
        self._seed: dict[str, list] = {}
        self._used: dict[str, list] = {}
        self._dirty = False
        self._lock = threading.Lock()

    @classmethod
    def load(cls, path: str, frozen_salt: str | None = None) -> ScanCache:
        """Load a cache saved by :meth:`save`.

        A missing, unreadable or mismatched file gives an empty cache.
        """
        cache = cls(frozen_salt)
        cache._entries, cache._loaded_salt = _load_file(path)
        return cache

    @property
    def empty(self) -> bool:
        """Whether we loaded no entries (not counting any seed)."""
        return not self._entries

    @property
    def install_changed(self) -> bool:
        """Whether we were saved under a different ``frozen_salt``.

        That is, by a different version of the install (app build).
        Worth loading a seed then too: entries for files that changed
        in the update miss, but the new build's seed has them.
        """
        return self._loaded_salt != self.frozen_salt

    @property
    def entry_count(self) -> int:
        """Entries the most recent scan used or added (what saves)."""
        return len(self._used)

    def load_seed(self, path: str) -> bool:
        """Use a seed file as a fallback for entries we don't have.

        ``path`` may also point inside a zip archive (``foo.apk/a/b``).
        Returns whether a usable seed was found.
        """
        self._seed, _salt = _load_file(path)
        return bool(self._seed)

    def save(self, path: str) -> None:
        """Write the cache out, if it changed.

        Only entries used by the most recent scan are kept, so modules
        that went away drop out.
        """
        with self._lock:
            # (Rewrite on install changes too, to record the new one.)
            if (
                not self._dirty
                and len(self._used) == len(self._entries)
                and not self.install_changed
            ):
                return
            data = {
                'v': CACHE_FORMAT_VERSION,
                'b': self.frozen_salt,
                'e': dict(self._used),
            }
        dirname = os.path.dirname(path)
        if dirname:
            os.makedirs(dirname, exist_ok=True)
        tmppath = f'{path}.tmp'
        with open(tmppath, 'w', encoding='utf-8') as outfile:
            json.dump(data, outfile, separators=(',', ':'))
        os.replace(tmppath, path)

    def get(self, name: str, key: list) -> ModuleOutcome | None:
        """Return a module's remembered outcome, if still valid."""
        from_seed = False
        entry = self._entries.get(name)
        if entry is None or entry[0] != key:
            entry = self._seed.get(name)
            from_seed = True
        with self._lock:
            if entry is None or entry[0] != key:
                self._count_miss(name)
                return None
            self.hits += 1
            if from_seed:
                self.seed_hits += 1
                self._dirty = True
            self._used[name] = entry
        try:
            return ModuleOutcome.from_wire(entry[1])
        except Exception:
            # Garbled entry; treat as a miss (and replace it). We write
            # these files atomically, so this shouldn't happen.
            with self._lock:
                del self._used[name]
                self.hits -= 1
                self._count_miss(name)
                if from_seed:
                    self.seed_hits -= 1
                warn = not self._warned_garbled
                self._warned_garbled = True
            if warn:
                logging.warning(
                    'metascan: Garbled scan-cache entry for %s; rescanning.',
                    name,
                )
            return None

    def _count_miss(self, name: str) -> None:
        # (Call with the lock held.)
        self.misses += 1
        alias = name.partition(':')[0]
        self.misses_by_alias[alias] = self.misses_by_alias.get(alias, 0) + 1

    def put(self, name: str, key: list, outcome: ModuleOutcome) -> None:
        """Remember a module's outcome."""
        with self._lock:
            self._used[name] = [key, outcome.to_wire()]
            self._dirty = True


def _load_file(path: str) -> tuple[dict[str, list], str | None]:
    """Entries and salt from a saved cache/seed file.

    Entries are empty if the file is missing or unusable.
    """
    raw = _read_bytes(path)
    if raw is None:
        return {}, None  # No file; perfectly normal.
    try:
        data = json.loads(raw)
    except ValueError:
        # We write these atomically, so this shouldn't happen.
        logging.warning('metascan: Ignoring corrupt scan cache %s.', path)
        return {}, None
    if not isinstance(data, dict):
        logging.warning('metascan: Ignoring malformed scan cache %s.', path)
        return {}, None
    if data.get('v') != CACHE_FORMAT_VERSION:
        return {}, None  # From older (or newer) code; expected.
    entries = data.get('e')
    if not isinstance(entries, dict):
        logging.warning('metascan: Ignoring malformed scan cache %s.', path)
        return {}, None
    salt = data.get('b')
    out: dict[str, list] = entries
    return out, salt if isinstance(salt, str) else None


def _read_bytes(path: str) -> bytes | None:
    """Read a file, which may also live inside a zip archive."""
    try:
        with open(path, 'rb') as infile:
            return infile.read()
    except OSError:
        pass
    try:
        return zipimport.zipimporter(os.path.dirname(path)).get_data(path)
    except zipimport.ZipImportError, OSError:
        return None
