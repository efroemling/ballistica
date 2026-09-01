# Released under the MIT License. See LICENSE for details.
#
"""Scanner for ``# ba_meta`` directives in Python source.

Recognized directive shapes:

- ``# ba_meta require api <N>`` — module-level API version
  requirement. When ``expected_api_version`` is supplied, modules
  whose value doesn't match are skipped (and listed in
  :attr:`ScanResults.incorrect_api_modules`). When it is ``None``
  the line is parsed for validity but no filtering occurs.
- ``# ba_meta export <TYPE>`` — export the class defined on the
  next non-blank source line under the export-type ``<TYPE>``.
- ``# ba_meta require asset-package <ID>`` — module declares that
  it needs the named asset-package at runtime.

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
import logging
import pkgutil
import zipimport
import threading
import importlib.machinery
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from concurrent.futures import Future
    from _typeshed.importlib import PathEntryFinderProtocol

# Fast bytes-level test applied to raw module data before any
# decoding: files not containing this marker can hold no directives,
# so the scan skips decode/line-split for them entirely (the vast
# majority of files).
_MARKER_BYTES = b'# ba_meta'
_MARKER_STR = '# ba_meta'


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
    asset_packages: dict[str, list[str]] = field(default_factory=dict)
    incorrect_api_modules: list[str] = field(default_factory=list)
    announce_errors_occurred: bool = False

    def exports_by_name(self, name: str) -> list[str]:
        """Return exports matching a given name."""
        return self.exports.get(name, [])


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
    ) -> None:
        """Given one or more paths, parses available meta information.

        It is assumed that these paths are also in PYTHONPATH.
        Paths may be directories, zip archives, or paths inside zip
        archives.
        """
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
                        futures += [
                            pool.submit(
                                self._scan_module_tree,
                                path,
                                finder,
                                modinfo.name,
                                modinfo.ispkg,
                            )
                            for modinfo in pkgutil.iter_modules([path])
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

    def _load_module_payload(
        self,
        path: str,
        finder: PathEntryFinderProtocol,
        fullname: str,
        ispkg: bool,
    ) -> tuple[str, bytes | str, list[str]] | None:
        """Locate and read a module's raw source via its loader.

        Returns ``(display_path, payload, submodule_locations)``
        where payload is raw utf-8 bytes when possible (only files
        that pass the marker prefilter get decoded) or already-str
        for get_source-only loaders. ``None`` for modules that can't
        carry meta tags (sourceless modules, unsupported loaders).
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
            data: bytes
            try:
                if isinstance(finder, _SupportsGetData):
                    data = finder.get_data(display)
                else:
                    with open(display, 'rb') as infile:
                        data = infile.read()
            except OSError:
                # No .py source present (bytecode-only, etc).
                return None
            return display, data, sublocs

        spec = finder.find_spec(fullname)
        if (
            spec is None
            or spec.loader is None
            or spec.origin is None
            # Sourceless modules (compiled extensions, bytecode-only).
            or not spec.origin.endswith('.py')
        ):
            return None
        sublocs = list(spec.submodule_search_locations or [])
        if isinstance(spec.loader, _SupportsGetData):
            return spec.origin, spec.loader.get_data(spec.origin), sublocs
        if isinstance(spec.loader, _SupportsGetSource):
            source = spec.loader.get_source(fullname)
            if source is not None:
                return spec.origin, source, sublocs
        return None

    def _scan_module(
        self,
        results: ScanResults,
        children: list[tuple[str, str]],
        *,
        path: str,
        finder: PathEntryFinderProtocol,
        fullname: str,
        ispkg: bool,
        is_top_level: bool,
    ) -> None:
        """Scan an individual module and add the findings to results."""
        loaded = self._load_module_payload(path, finder, fullname, ispkg)
        if loaded is None:
            return
        display, payload, sublocs = loaded

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
            results, display, meta_lines, is_top_level
        )

        # Top level modules with no discernible api version get ignored.
        if is_top_level and required_api is None:
            return

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
            results.incorrect_api_modules.append(fullname)
            return

        # Ok; can proceed with a full scan of this module.
        self._process_module_meta_tags(
            results, display, fullname, flines, meta_lines
        )

        # If its a package, queue its contents for scanning.
        for subpath in sublocs:
            children.append((subpath, f'{fullname}.'))

    def _process_module_meta_tags(
        self,
        results: ScanResults,
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
                results.announce_errors_occurred = True
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
                # 'require asset-package <ID>' — record the dependency.
                pkg_id = mline[3]
                results.asset_packages.setdefault(pkg_id, []).append(modulename)
            elif len(mline) != 3 or mline[1] != 'export':
                # No other directive shapes are recognized.
                logging.warning(
                    'metascan: %s:%d: unrecognized ba_meta statement.',
                    display,
                    lindex + 1,
                )
                results.announce_errors_occurred = True
            else:
                # Looks like we've got a valid export line!
                exporttypestr = mline[2]
                export_class_name = self._get_export_class_name(
                    results, display, flines, lindex
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
                        results.announce_errors_occurred = True
                        exporttypestr = canonical

                    results.exports.setdefault(exporttypestr, []).append(
                        classname
                    )

    def _get_export_class_name(
        self,
        results: ScanResults,
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
            results.announce_errors_occurred = True
        return classname

    def _get_api_requirement(
        self,
        results: ScanResults,
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
            results.announce_errors_occurred = True
        elif not values and toplevel and meta_lines:
            # If we're a top-level module containing meta lines but no
            # valid "require api" line found, complain.
            logging.warning(
                "metascan: %s: no valid '# ba_meta require api <NUM>"
                ' line found; ignoring module.',
                display,
            )
            results.announce_errors_occurred = True
        return None
