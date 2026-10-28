# Released under the MIT License. See LICENSE for details.
#
"""Scanner for ``# ba_meta`` directives in Python source.

.. warning::

  This is an internal api and subject to change at any time. Do not use
  it in mod code.

Recognized directive shapes:

- ``# ba_meta require api <N>`` — module-level API version
  requirement. When ``expected_api_version`` is supplied, modules
  whose value doesn't match are skipped (and listed in
  :attr:`ScanResults.incorrect_api_modules`). When it is ``None``
  the line is parsed for validity but no filtering occurs.
- ``# ba_meta export <TYPE>`` — export the class defined on the
  next non-blank source line under the export-type ``<TYPE>``.
- ``# ba_meta require asset-package <NUM>`` — module declares that
  it needs the asset-package-version with that numeric id at runtime.

Other shapes are reported as malformed.

This module has no dependencies beyond the standard library so it
can run anywhere — in the game runtime (wrapped by
:class:`babase._meta.MetadataSubsystem`), in build/tooling contexts
(e.g. ``tools/pcommand assetpins``), or in tests.

Higher-level concerns — background-thread scheduling, UI feedback,
expansion of legacy export-type shortcuts, deprecation warnings —
live in the consumer.
"""

import os
import zlib
import logging
import pkgutil
import zipimport
import threading
import importlib.machinery
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Protocol, runtime_checkable

from bacommon.assetpackage import ApverNum
from bacommon.metascancache import FROZEN_MTIME_NS, ModuleOutcome, ScanCache

if TYPE_CHECKING:
    from typing import Callable
    from concurrent.futures import Future
    from _typeshed.importlib import PathEntryFinderProtocol

# Fast bytes-level test applied to raw module data before any
# decoding: files not containing this marker can hold no directives,
# so the scan skips decode/line-split for them entirely (the vast
# majority of files).
_MARKER_BYTES = b'# ba_meta'
_MARKER_STR = '# ba_meta'

#: Scan-path alias the app uses for its own Python dir, and so what
#: build tooling must seed that dir's cache entries under.
APP_SCAN_ALIAS = 'app'

#: Legacy export-type shortcut names the app accepts, mapped to the
#: canonical class paths it substitutes (with a deprecation warning).
#: Shared so build tooling scans exactly as the app does.
DEPRECATED_EXPORT_SHORTCUTS: dict[str, str] = {
    # DEPRECATED as of 6/2025.
    'plugin': 'babase.Plugin',
    # DEPRECATED as of 12/2023.
    'keyboard': 'bauiv1.Keyboard',
}


@runtime_checkable
class _SupportsGetData(Protocol):
    """The sliver of the loader protocol we need.

    Matches importlib's ``ResourceLoader.get_data`` shape; both
    ``SourceFileLoader`` and ``zipimport.zipimporter`` provide it.
    Checked structurally at runtime rather than via importlib's ABCs
    since not all loaders register with those.
    """

    def get_data(self, path: str) -> bytes:
        """Return raw bytes for a loadable path."""


@runtime_checkable
class _SupportsGetSource(Protocol):
    """Fallback loader shape (importlib ``InspectLoader.get_source``)."""

    def get_source(self, fullname: str) -> str | None:
        """Return source text for a module name, if available."""


def _is_scannable_path(path: str) -> bool:
    """Can this path host scannable modules?

    True for existing directories plus zip archives and paths inside
    them (anything zipimport accepts).
    """
    if os.path.isdir(path):
        return True
    try:
        zipimport.zipimporter(path)
    except zipimport.ZipImportError, OSError:
        return False
    return True


def _zip_entry_identity(
    finder: zipimport.zipimporter, display: str
) -> tuple[bool, list | None]:
    """Is ``display`` in the importer's archive, and its identity if so.

    The identity is the entry's uncompressed size and CRC32, read from
    the directory zipimport already holds in memory (its private
    table-of-contents; anything unexpected there just means no
    identity, so no caching).
    """
    pathname = display
    if os.altsep:
        pathname = pathname.replace(os.altsep, os.sep)
    prefix = finder.archive + os.sep
    key = pathname[len(prefix) :] if pathname.startswith(prefix) else pathname
    try:
        files = _zip_toc(finder)
    except Exception:
        # Can't look; let the read decide whether it exists.
        _warn_zip_identity_unavailable()
        return True, None
    if key not in files:
        return False, None
    toc_entry = files[key]
    if toc_entry is None:
        return True, None  # (zipimport's placeholder; not a real file.)
    try:
        # (path, compress, data_size, file_size, file_offset, time,
        # date, crc)
        return True, ['z', int(toc_entry[3]), int(toc_entry[7])]
    except Exception:
        _warn_zip_identity_unavailable()
        return True, None


def _zip_toc(finder: zipimport.zipimporter) -> dict:
    """zipimport's private in-memory table of contents for an archive."""
    # pylint: disable=protected-access
    toc: dict = finder._get_files()  # type: ignore[attr-defined]
    return toc


_g_warned_zip_identity = False


def _warn_zip_identity_unavailable() -> None:
    """Note (once) that zipimport internals didn't look as expected.

    Scanning still works, but nothing in zip archives gets cached, so
    Android launches lose the scan cache entirely. Likely a Python
    update changed zipimport's private table-of-contents.
    """
    global _g_warned_zip_identity  # pylint: disable=global-statement
    if _g_warned_zip_identity:
        return
    _g_warned_zip_identity = True
    logging.warning(
        'metascan: zipimport internals look different than expected;'
        ' zip archive contents will not be cached (scans run slower).'
    )


def _locate_direct(
    finder: importlib.machinery.FileFinder | _SupportsGetData,
    display: str,
    *,
    content: bool,
) -> tuple[list | None, Callable[[], bytes | None]] | None:
    """Identity and reader for a module read directly (no find_spec).

    None if the module has no source there. With ``content``, plain
    files are read right away and keyed like zip entries (size and
    CRC32), for building seeds.
    """
    if isinstance(finder, _SupportsGetData):
        gfinder = finder
        identity: list | None = None
        if isinstance(finder, zipimport.zipimporter):
            found, identity = _zip_entry_identity(finder, display)
            if not found:
                return None

        def _read_get_data() -> bytes | None:
            try:
                return gfinder.get_data(display)
            except OSError:
                return None

        return identity, _read_get_data

    if content:
        try:
            with open(display, 'rb') as infile:
                data = infile.read()
        except OSError:
            return None
        return ['z', len(data), zlib.crc32(data)], lambda: data

    try:
        stat = os.stat(display)
    except OSError:
        return None

    def _read_file() -> bytes | None:
        try:
            with open(display, 'rb') as infile:
                return infile.read()
        except OSError:
            return None

    return ['f', stat.st_size, stat.st_mtime_ns], _read_file


def extract_meta_lines(lines: list[str]) -> dict[int, list[str]]:
    """Tokenize ``# ba_meta`` directive lines from Python source lines.

    Returns a dict mapping line index to the whitespace-split tokens
    of everything after the leading ``#`` (so a well-formed line
    yields ``['ba_meta', ...]``). This is the single definition of
    which lines count as directives; all ``# ba_meta`` parsing should
    go through it rather than ad-hoc regexes so the rules can't
    drift.
    """
    return {
        lnum: l[1:].split()
        for lnum, l in enumerate(lines)
        # Do a simple 'in' check for speed but then make sure its
        # also at the beginning of the line. This allows disabling
        # meta-lines and avoids false positives from code that
        # wrangles them. Bare '# ba_meta' lines with no directive
        # are included here so they get flagged as unrecognized.
        if (
            '# ba_meta' in l
            and (l.strip() == '# ba_meta' or l.strip().startswith('# ba_meta '))
        )
    }


def api_requirement_values(meta_lines: dict[int, list[str]]) -> list[int]:
    """Return values of all well-formed ``require api`` directives.

    Input is tokenized directive lines from
    :func:`extract_meta_lines`. Anything less than a fully
    well-formed ``# ba_meta require api <N>`` line is ignored here
    (consumers decide whether zero or multiple results is an error).
    """
    return [
        int(l[3])
        for l in meta_lines.values()
        if len(l) == 4
        and l[0] == 'ba_meta'
        and l[1] == 'require'
        and l[2] == 'api'
        and l[3].isdigit()
    ]


def get_source_api_requirement(source: str) -> int | None:
    """Return the api version required by a Python source string.

    Returns the value only when exactly one well-formed
    ``# ba_meta require api <N>`` line is present; ``None``
    otherwise (none found, or ambiguous multiples).
    """
    values = api_requirement_values(extract_meta_lines(source.splitlines()))
    return values[0] if len(values) == 1 else None


@dataclass
class ScanResults:
    """Final results from a meta-scan."""

    exports: dict[str, list[str]] = field(default_factory=dict)
    asset_packages: dict[ApverNum, list[str]] = field(default_factory=dict)
    incorrect_api_modules: list[str] = field(default_factory=list)
    announce_errors_occurred: bool = False
    #: Number of top-level modules/packages found under each scanned
    #: path (keyed by the path as passed in). Counts everything the
    #: import system could load from there, with or without ba_meta
    #: directives; the engine uses it to tell whether a user's mods
    #: dir holds any Python at all.
    module_counts: dict[str, int] = field(default_factory=dict)

    def exports_by_name(self, name: str) -> list[str]:
        """Return exports matching a given name."""
        return self.exports.get(name, [])


def write_seed(
    python_dir: str,
    alias: str,
    outpath: str,
    *,
    expected_api_version: int | None,
    deprecated_export_shortcuts: dict[str, str] | None = None,
) -> int:
    """Precompute a :class:`ScanCache` seed for a Python dir.

    For a dir that will ship inside a zip archive (an Android apk):
    entries get keyed by content as zip entries are, under ``alias``
    (which the app must also use for that dir), so at runtime they
    apply to exactly the files they were computed from. The scan
    settings must match the app's too. Returns the entry count.
    """
    cache = ScanCache()
    scan = DirectoryScan(
        paths=[python_dir],
        expected_api_version=expected_api_version,
        deprecated_export_shortcuts=deprecated_export_shortcuts,
        cache=cache,
        path_aliases={python_dir: alias},
        content_identities=True,
    )
    scan.run()
    cache.save(outpath)
    return cache.entry_count


class DirectoryScan:
    """Scans path entries for ``# ba_meta`` directives.

    Pure-Python; no runtime dependencies. Construct with a list of
    paths (which must already be on PYTHONPATH if discovered
    modules will be imported by the consumer), then call
    :meth:`run`. Results land in ``results``.

    Paths are walked through the standard import-finder machinery
    (:mod:`pkgutil`), not raw directory listings, so a path may be a
    directory, a zip archive, or a path inside a zip archive (e.g.
    ``bundle.zip/python``) — anything the import system itself could
    load from. Module source is read via the loader protocol
    (``get_data``/``get_source``); nothing is ever imported/executed
    by the scan.

    If ``expected_api_version`` is set, modules whose
    ``# ba_meta require api`` value doesn't match are skipped and
    listed in :attr:`ScanResults.incorrect_api_modules`. Pass
    ``None`` to scan regardless of api version (the typical
    tooling-side mode).

    If ``deprecated_export_shortcuts`` is provided, export-type
    strings that appear as keys are substituted with the
    corresponding canonical class path and a deprecation warning
    is emitted with file:line context. Pass ``None`` to perform
    no substitution.

    If ``expects_extras`` is True, :meth:`run` will block after
    finishing the base paths until :meth:`set_extras` is called
    from another thread. This supports the runtime pattern of
    kicking off the scan immediately and providing extra paths
    (workspace dirs, etc.) once they are known. Synchronous
    tooling callers should leave it at the default ``False``;
    :meth:`run` will then finish after the base paths.
    """

    def __init__(
        self,
        paths: list[str],
        expected_api_version: int | None = None,
        deprecated_export_shortcuts: dict[str, str] | None = None,
        *,
        expects_extras: bool = False,
        max_workers: int | None = None,
        cache: ScanCache | None = None,
        path_aliases: dict[str, str] | None = None,
        content_identities: bool = False,
    ) -> None:
        """Given one or more paths, parses available meta information.

        It is assumed that these paths are also in PYTHONPATH.
        Paths may be directories, zip archives, or paths inside zip
        archives.

        ``path_aliases`` gives scan paths stable names for cache keys
        (cache entries are keyed relative to their scan path, so an
        app's Python dir can move, as an apk's install path does on
        every update, without invalidating them). ``content_identities``
        keys plain files by size and CRC32 of their contents instead of
        mtime, matching how zip entries are keyed; it's for generating
        seeds (see :class:`ScanCache`), and reads every file.
        """
        #: Optional cache of per-module outcomes (see ScanCache). May be
        #: assigned any time before run().
        self.cache = cache
        self._path_aliases = dict(path_aliases or {})
        self._content_identities = content_identities
        # Skip non-existent/unscannable paths completely.
        self.base_paths = [str(p) for p in paths if _is_scannable_path(p)]
        self.expected_api_version = expected_api_version
        self.deprecated_export_shortcuts: dict[str, str] = (
            dict(deprecated_export_shortcuts)
            if deprecated_export_shortcuts is not None
            else {}
        )
        self.extra_paths: list[str] = []
        # When extras are expected, run() blocks until set_extras()
        # sets this event. Synchronous callers skip the wait
        # entirely by leaving expects_extras=False.
        self._extras_ready = threading.Event()
        if not expects_extras:
            self._extras_ready.set()
        # Default is single-worker: measured 2026-08-31 (Mac + Pixel
        # 7a), extra workers only ever paid off modestly for
        # cold-cache directory scans (~13%) and *hurt* everywhere
        # else (warm scans and zip scans both suffer from GIL/task
        # overhead since the bytes-marker prefilter leaves little
        # parallelizable work). The knob stays for callers who know
        # they're doing a cold multi-file scan on idle cores.
        self._max_workers = max_workers if max_workers is not None else 1
        self.results = ScanResults()

        # Our settings shape every module's outcome, so cached outcomes
        # only apply to scans with the same ones. (A short digest of
        # them, since it goes in every cache entry's key.)
        settings = repr(
            (
                expected_api_version,
                sorted(self.deprecated_export_shortcuts.items()),
            )
        )
        self._cache_sig = format(zlib.crc32(settings.encode()), '08x')

    def set_extras(self, paths: list[str]) -> None:
        """Set extra portion."""
        # Skip non-existent/unscannable paths completely. Note that
        # this must mutate extra_paths in place (run() holds a
        # reference to it) and must fully populate it before setting
        # the event.
        self.extra_paths += [str(p) for p in paths if _is_scannable_path(p)]
        self._extras_ready.set()

    def run(self) -> None:
        """Do the thing."""
        # Parallelism structure: top-level modules/packages are
        # enumerated serially (cheap) and each becomes one pool task
        # that scans its whole subtree into a private partial result;
        # partials merge here in submission order, so workers never
        # touch shared state and output is deterministic.
        with ThreadPoolExecutor(max_workers=self._max_workers) as pool:
            for pathlist in [self.base_paths, self.extra_paths]:
                # Wait until extra paths are provided before doing them.
                if pathlist is self.extra_paths:
                    self._extras_ready.wait()

                futures: list[Future[ScanResults]] = []
                for path in pathlist:
                    try:
                        finder = pkgutil.get_importer(path)
                        if finder is None:
                            continue
                        modinfos = list(pkgutil.iter_modules([path]))
                        self.results.module_counts[path] = len(modinfos)
                        futures += [
                            pool.submit(
                                self._scan_module_tree,
                                path,
                                finder,
                                modinfo.name,
                                modinfo.ispkg,
                            )
                            for modinfo in modinfos
                        ]
                    except Exception:
                        logging.exception(
                            "metascan: Error scanning path '%s'.", path
                        )
                        self.results.announce_errors_occurred = True
                for fut in futures:
                    self._merge_partial(fut.result())

        # Sort our results.
        for exportlist in self.results.exports.values():
            exportlist.sort()
        for modlist in self.results.asset_packages.values():
            modlist.sort()

    def _merge_partial(self, partial: ScanResults) -> None:
        """Fold one task's partial results into the shared results."""
        for exporttype, classnames in partial.exports.items():
            self.results.exports.setdefault(exporttype, []).extend(classnames)
        for pkg_id, modnames in partial.asset_packages.items():
            self.results.asset_packages.setdefault(pkg_id, []).extend(modnames)
        self.results.incorrect_api_modules += partial.incorrect_api_modules
        if partial.announce_errors_occurred:
            self.results.announce_errors_occurred = True

    def _scan_module_tree(
        self,
        path: str,
        finder: PathEntryFinderProtocol,
        fullname: str,
        ispkg: bool,
    ) -> ScanResults:
        """Scan a top-level module/package and its whole subtree.

        Runs in a worker thread; mutates only its own partial
        results. Modules are enumerated through the import path-hook
        machinery, which also handles the details we used to handle
        by hand: hidden/invalid names never yield modules and
        namespace-package dirs (no ``__init__``) are skipped.
        """
        results = ScanResults()
        # Entries: (path-entry, finder-for-it, fullname, ispkg, top?).
        stack: list[tuple[str, PathEntryFinderProtocol, str, bool, bool]] = [
            (path, finder, fullname, ispkg, True)
        ]
        while stack:
            epath, efinder, ename, eispkg, etop = stack.pop()
            children: list[tuple[str, str]] = []
            try:
                self._scan_module(
                    results,
                    children,
                    root=path,
                    path=epath,
                    finder=efinder,
                    fullname=ename,
                    ispkg=eispkg,
                    is_top_level=etop,
                )
            except Exception:
                logging.exception("metascan: Error scanning '%s'.", ename)
                results.announce_errors_occurred = True
            for subpath, prefix in children:
                try:
                    subfinder = pkgutil.get_importer(subpath)
                    if subfinder is None:
                        continue
                    stack += [
                        (subpath, subfinder, modinfo.name, modinfo.ispkg, False)
                        for modinfo in pkgutil.iter_modules(
                            [subpath], prefix=prefix
                        )
                    ]
                except Exception:
                    logging.exception(
                        "metascan: Error scanning path '%s'.", subpath
                    )
                    results.announce_errors_occurred = True
        return results

    def _locate_module(
        self,
        path: str,
        finder: PathEntryFinderProtocol,
        fullname: str,
        ispkg: bool,
    ) -> (
        tuple[str, list[str], list | None, Callable[[], bytes | str | None]]
        | None
    ):
        """Find a module's source without reading it yet.

        Returns ``(display_path, submodule_locations, identity,
        read)``. ``identity`` keys the module's source for caching
        (None if it can't be trusted to), and ``read()`` returns the
        raw source: utf-8 bytes when possible (only files that pass the
        marker prefilter get decoded) or already-str for
        get_source-only loaders, or None if it turns out unreadable.
        Returns None for modules that can't carry meta tags (sourceless
        modules, unsupported loaders).
        """
        tail = fullname.rpartition('.')[2]
        if isinstance(
            finder, (importlib.machinery.FileFinder, _SupportsGetData)
        ):
            # Direct-read fast paths, skipping find_spec entirely:
            # for plain dirs we open the file ourselves (which is all
            # SourceFileLoader.get_data does anyway), and finders like
            # zipimporter double as their own loaders. Notably,
            # zipimporter's find_spec *compiles* each module just to
            # calculate its filename, which would utterly dominate
            # scan time.
            if ispkg:
                display = os.path.join(path, tail, '__init__.py')
                sublocs = [os.path.join(path, tail)]
            else:
                display = os.path.join(path, tail + '.py')
                sublocs = []
            direct = _locate_direct(
                finder, display, content=self._content_identities
            )
            if direct is None:
                return None  # No .py source (bytecode-only, etc).
            identity, read = direct
            return display, sublocs, identity, read

        spec = finder.find_spec(fullname)
        if (
            spec is None
            or spec.loader is None
            or spec.origin is None
            # Sourceless modules (compiled extensions, bytecode-only).
            or not spec.origin.endswith('.py')
        ):
            return None
        origin = spec.origin
        loader = spec.loader
        specsublocs = list(spec.submodule_search_locations or [])
        if isinstance(loader, _SupportsGetData):
            gloader = loader
            return (
                origin,
                specsublocs,
                None,
                lambda: gloader.get_data(origin),
            )
        if isinstance(loader, _SupportsGetSource):
            sloader = loader
            return (
                origin,
                specsublocs,
                None,
                lambda: sloader.get_source(fullname),
            )
        return None

    def _cache_name_and_key(
        self,
        root: str,
        display: str,
        fullname: str,
        is_top_level: bool,
        identity: list | None,
    ) -> tuple[str, list | None]:
        """A module's cache entry name, and key (None if uncacheable)."""
        # Entries are named relative to their scan path (under its
        # alias, if any) so they survive that path moving.
        alias = self._path_aliases.get(root, root)
        rootprefix = root + os.sep
        relpath = (
            display[len(rootprefix) :]
            if display.startswith(rootprefix)
            else display
        )
        cachename = f'{alias}:{relpath}'

        cache = self.cache
        if cache is None or identity is None:
            return cachename, None
        if identity[0] == 'f' and identity[2] <= FROZEN_MTIME_NS:
            # Frozen mtime (flatpak/nix); key by install version instead.
            if cache.frozen_salt is None:
                return cachename, None
            identity = ['F', identity[1], cache.frozen_salt]
        return cachename, [self._cache_sig, fullname, is_top_level, *identity]

    def _scan_module(
        self,
        results: ScanResults,
        children: list[tuple[str, str]],
        *,
        root: str,
        path: str,
        finder: PathEntryFinderProtocol,
        fullname: str,
        ispkg: bool,
        is_top_level: bool,
    ) -> None:
        """Scan an individual module and add the findings to results."""
        located = self._locate_module(path, finder, fullname, ispkg)
        if located is None:
            return
        display, sublocs, identity, read = located

        cache = self.cache
        cachename, key = self._cache_name_and_key(
            root, display, fullname, is_top_level, identity
        )
        outcome: ModuleOutcome | None = None
        if key is not None:
            assert cache is not None
            outcome = cache.get(cachename, key)
        if outcome is None:
            payload = read()
            if payload is None:
                return
            outcome = self._compute_outcome(
                display, fullname, is_top_level, payload
            )
            if key is not None and outcome.cacheable:
                assert cache is not None
                cache.put(cachename, key, outcome)

        for exporttype, classname in outcome.exports:
            results.exports.setdefault(exporttype, []).append(classname)
        for apvernum, modulename in outcome.asset_packages:
            results.asset_packages.setdefault(ApverNum(apvernum), []).append(
                modulename
            )
        if outcome.incorrect_api:
            results.incorrect_api_modules.append(fullname)
        if outcome.announce:
            results.announce_errors_occurred = True

        # If its a package, queue its contents for scanning.
        if outcome.recurse:
            for subpath in sublocs:
                children.append((subpath, f'{fullname}.'))

    def _compute_outcome(
        self,
        display: str,
        fullname: str,
        is_top_level: bool,
        payload: bytes | str,
    ) -> ModuleOutcome:
        """Work out what a module contributes, from its source."""
        outcome = ModuleOutcome()

        # Cheap prefilter on the raw data: no marker anywhere means
        # no directives, so skip decode/line-splitting entirely.
        if isinstance(payload, bytes):
            source = payload.decode('utf-8') if _MARKER_BYTES in payload else ''
        else:
            source = payload if _MARKER_STR in payload else ''
        if source:
            flines = source.splitlines()
            meta_lines = extract_meta_lines(flines)
        else:
            flines = []
            meta_lines = {}
        required_api = self._get_api_requirement(
            outcome, display, meta_lines, is_top_level
        )

        # Top level modules with no discernible api version get ignored.
        if is_top_level and required_api is None:
            return outcome

        # If we find a module requiring a different api version than the
        # consumer expects, warn and ignore. If no api was supplied, do
        # no filtering.
        if (
            required_api is not None
            and self.expected_api_version is not None
            and required_api != self.expected_api_version
        ):
            logging.warning(
                'metascan: %s requires api %s but we are running'
                ' %s. Ignoring module.',
                display,
                required_api,
                self.expected_api_version,
            )
            outcome.incorrect_api = True
            return outcome

        # Ok; can proceed with a full scan of this module.
        self._process_module_meta_tags(
            outcome, display, fullname, flines, meta_lines
        )
        outcome.recurse = True
        return outcome

    def _process_module_meta_tags(
        self,
        outcome: ModuleOutcome,
        display: str,
        modulename: str,
        flines: list[str],
        meta_lines: dict[int, list[str]],
    ) -> None:
        """Pull data from a module based on its ba_meta tags."""
        for lindex, mline in meta_lines.items():
            # meta_lines is just anything containing the marker; make
            # sure the directive token is in the right place.
            if mline[0] != 'ba_meta':
                logging.warning(
                    'metascan: %s:%d: malformed ba_meta statement.',
                    display,
                    lindex + 1,
                )
                outcome.announce = True
            elif (
                len(mline) == 4 and mline[1] == 'require' and mline[2] == 'api'
            ):
                # Ignore 'require api X' lines in this pass; handled
                # already by _get_api_requirement.
                pass
            elif (
                len(mline) == 4
                and mline[1] == 'require'
                and mline[2] == 'asset-package'
            ):
                # 'require asset-package <NUM>' — record the dependency.
                if not mline[3].isdigit():
                    # Pre-numeric wrappers named the version by its
                    # string id; regenerate them to pick up the number.
                    logging.warning(
                        'metascan: %s:%d: asset-package requirement %r is'
                        ' not a numeric version id; regenerate the'
                        ' wrapper.',
                        display,
                        lindex + 1,
                        mline[3],
                    )
                    outcome.announce = True
                else:
                    outcome.asset_packages.append((int(mline[3]), modulename))
            elif len(mline) != 3 or mline[1] != 'export':
                # No other directive shapes are recognized.
                logging.warning(
                    'metascan: %s:%d: unrecognized ba_meta statement.',
                    display,
                    lindex + 1,
                )
                outcome.announce = True
            else:
                # Looks like we've got a valid export line!
                exporttypestr = mline[2]
                export_class_name = self._get_export_class_name(
                    outcome, display, flines, lindex
                )
                if export_class_name is not None:
                    classname = modulename + '.' + export_class_name

                    # If the export type is in the consumer-provided
                    # deprecated-shortcut map, sub in the canonical class
                    # path and warn.
                    canonical = self.deprecated_export_shortcuts.get(
                        exporttypestr
                    )
                    if canonical is not None:
                        logging.warning(
                            "metascan: %s:%d: '# ba_meta export %s'"
                            ' tag is deprecated and should be replaced'
                            " by '# ba_meta export %s'.",
                            display,
                            lindex + 1,
                            exporttypestr,
                            canonical,
                        )
                        outcome.announce = True
                        exporttypestr = canonical

                    outcome.exports.append((exporttypestr, classname))

    def _get_export_class_name(
        self,
        outcome: ModuleOutcome,
        display: str,
        lines: list[str],
        lindex: int,
    ) -> str | None:
        """Given line num of an export tag, returns its operand class name."""
        lindexorig = lindex
        classname = None
        while True:
            lindex += 1
            if lindex >= len(lines):
                break
            lbits = lines[lindex].split()
            if not lbits:
                continue  # Skip empty lines.
            if lbits[0] != 'class':
                break
            if len(lbits) > 1:
                # Pull the name off the front of forms such as 'Foo:',
                # 'Foo(Base):', or 'Foo[T](Base):'.
                cbit = lbits[1].split('(')[0].split('[')[0].split(':')[0]
                if cbit.isidentifier():
                    classname = cbit
                    break  # Success!
        if classname is None:
            logging.warning(
                'metascan: %s:%d: class definition not found below'
                " 'ba_meta export' statement.",
                display,
                lindexorig + 1,
            )
            outcome.announce = True
        return classname

    def _get_api_requirement(
        self,
        outcome: ModuleOutcome,
        display: str,
        meta_lines: dict[int, list[str]],
        toplevel: bool,
    ) -> int | None:
        """Return an API requirement integer or None if none present.

        Malformed api requirement strings will be logged as warnings.
        """
        values = api_requirement_values(meta_lines)

        # We're successful if we find exactly one properly formatted
        # line.
        if len(values) == 1:
            return values[0]

        # Ok; not successful. lets issue warnings for a few error cases.
        if len(values) > 1:
            logging.warning(
                "metascan: %s: multiple '# ba_meta require api <NUM>'"
                ' lines found; ignoring module.',
                display,
            )
            outcome.announce = True
        elif not values and toplevel and meta_lines:
            # If we're a top-level module containing meta lines but no
            # valid "require api" line found, complain.
            logging.warning(
                "metascan: %s: no valid '# ba_meta require api <NUM>"
                ' line found; ignoring module.',
                display,
            )
            outcome.announce = True
        return None
