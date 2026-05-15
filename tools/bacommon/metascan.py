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

from __future__ import annotations

import os
import time
import logging
from pathlib import Path
from dataclasses import dataclass, field


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
    """Scans directories for ``# ba_meta`` directives.

    Pure-Python; no runtime dependencies. Construct with a list of
    paths (which must already be on PYTHONPATH if discovered
    modules will be imported by the consumer), then call
    :meth:`run`. Results land in ``results``.

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
    ) -> None:
        """Given one or more paths, parses available meta information.

        It is assumed that these paths are also in PYTHONPATH.
        It is also assumed that any subdirectories are Python
        packages.
        """
        # Skip non-existent paths completely.
        self.base_paths = [Path(p) for p in paths if os.path.isdir(p)]
        self.expected_api_version = expected_api_version
        self.deprecated_export_shortcuts: dict[str, str] = (
            dict(deprecated_export_shortcuts)
            if deprecated_export_shortcuts is not None
            else {}
        )
        self.extra_paths: list[Path] = []
        # When extras are expected, run() blocks until set_extras()
        # flips this to True. Synchronous callers skip the wait
        # entirely by leaving expects_extras=False.
        self.extra_paths_set = not expects_extras
        self.results = ScanResults()

    def set_extras(self, paths: list[str]) -> None:
        """Set extra portion."""
        # Skip non-existent paths completely.
        self.extra_paths += [Path(p) for p in paths if os.path.isdir(p)]
        self.extra_paths_set = True

    def run(self) -> None:
        """Do the thing."""
        for pathlist in [self.base_paths, self.extra_paths]:
            # Spin and wait until extra paths are provided before doing them.
            if pathlist is self.extra_paths:
                while not self.extra_paths_set:
                    time.sleep(0.001)

            modules: list[tuple[Path, Path]] = []
            for path in pathlist:
                self._get_path_module_entries(path, '', modules)
            for moduledir, subpath in modules:
                try:
                    self._scan_module(moduledir, subpath)
                except Exception:
                    logging.exception("metascan: Error scanning '%s'.", subpath)

        # Sort our results.
        for exportlist in self.results.exports.values():
            exportlist.sort()
        for modlist in self.results.asset_packages.values():
            modlist.sort()

    def _get_path_module_entries(
        self, path: Path, subpath: str | Path, modules: list[tuple[Path, Path]]
    ) -> None:
        """Scan provided path and add module entries to provided list."""
        try:
            fullpath = Path(path, subpath)
            # Note: skipping hidden dirs (starting with '.').
            entries = [
                (path, Path(subpath, name))
                for name in os.listdir(fullpath)
                if not name.startswith('.')
            ]
        except PermissionError:
            # Expected sometimes.
            entries = []
        except Exception:
            # Unexpected; report this.
            logging.exception('metascan: Error in _get_path_module_entries.')
            self.results.announce_errors_occurred = True
            entries = []

        # Now identify python packages/modules out of what we found.
        for entry in entries:
            if entry[1].name.endswith('.py'):
                modules.append(entry)
            elif (
                Path(entry[0], entry[1]).is_dir()
                and Path(entry[0], entry[1], '__init__.py').is_file()
            ):
                modules.append(entry)

    def _scan_module(self, moduledir: Path, subpath: Path) -> None:
        """Scan an individual module and add the findings to results."""
        if subpath.name.endswith('.py'):
            fpath = Path(moduledir, subpath)
            ispackage = False
        else:
            fpath = Path(moduledir, subpath, '__init__.py')
            ispackage = True
        with fpath.open(encoding='utf-8') as infile:
            flines = infile.readlines()
        meta_lines = {
            lnum: l[1:].split()
            for lnum, l in enumerate(flines)
            # Do a simple 'in' check for speed but then make sure its
            # also at the beginning of the line. This allows disabling
            # meta-lines and avoids false positives from code that
            # wrangles them.
            if ('# ba_meta' in l and l.strip().startswith('# ba_meta '))
        }
        is_top_level = len(subpath.parts) <= 1
        required_api = self._get_api_requirement(
            subpath, meta_lines, is_top_level
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
                subpath,
                required_api,
                self.expected_api_version,
            )
            self.results.incorrect_api_modules.append(
                self._module_name_for_subpath(subpath)
            )
            return

        # Ok; can proceed with a full scan of this module.
        self._process_module_meta_tags(subpath, flines, meta_lines)

        # If its a package, recurse into its subpackages.
        if ispackage:
            try:
                submodules: list[tuple[Path, Path]] = []
                self._get_path_module_entries(moduledir, subpath, submodules)
                for submodule in submodules:
                    if submodule[1].name != '__init__.py':
                        self._scan_module(submodule[0], submodule[1])
            except Exception:
                logging.exception('metascan: Error scanning %s.', subpath)

    def _module_name_for_subpath(self, subpath: Path) -> str:
        # (should not be getting these)
        assert '__init__.py' not in str(subpath)

        return '.'.join(subpath.parts).removesuffix('.py')

    def _process_module_meta_tags(
        self,
        subpath: Path,
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
                    subpath,
                    lindex + 1,
                )
                self.results.announce_errors_occurred = True
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
                modulename = self._module_name_for_subpath(subpath)
                pkg_id = mline[3]
                self.results.asset_packages.setdefault(pkg_id, []).append(
                    modulename
                )
            elif len(mline) != 3 or mline[1] != 'export':
                # No other directive shapes are recognized.
                logging.warning(
                    'metascan: %s:%d: unrecognized ba_meta statement.',
                    subpath,
                    lindex + 1,
                )
                self.results.announce_errors_occurred = True
            else:
                # Looks like we've got a valid export line!
                modulename = self._module_name_for_subpath(subpath)
                exporttypestr = mline[2]
                export_class_name = self._get_export_class_name(
                    subpath, flines, lindex
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
                            subpath,
                            lindex + 1,
                            exporttypestr,
                            canonical,
                        )
                        self.results.announce_errors_occurred = True
                        exporttypestr = canonical

                    self.results.exports.setdefault(exporttypestr, []).append(
                        classname
                    )

    def _get_export_class_name(
        self, subpath: Path, lines: list[str], lindex: int
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
                cbits = lbits[1].split('(')
                if len(cbits) > 1 and cbits[0].isidentifier():
                    classname = cbits[0]
                    break  # Success!
        if classname is None:
            logging.warning(
                'metascan: %s:%d: class definition not found below'
                " 'ba_meta export' statement.",
                subpath,
                lindexorig + 1,
            )
            self.results.announce_errors_occurred = True
        return classname

    def _get_api_requirement(
        self,
        subpath: Path,
        meta_lines: dict[int, list[str]],
        toplevel: bool,
    ) -> int | None:
        """Return an API requirement integer or None if none present.

        Malformed api requirement strings will be logged as warnings.
        """
        lines = [
            l
            for l in meta_lines.values()
            if len(l) == 4
            and l[0] == 'ba_meta'
            and l[1] == 'require'
            and l[2] == 'api'
            and l[3].isdigit()
        ]

        # We're successful if we find exactly one properly formatted
        # line.
        if len(lines) == 1:
            return int(lines[0][3])

        # Ok; not successful. lets issue warnings for a few error cases.
        if len(lines) > 1:
            logging.warning(
                "metascan: %s: multiple '# ba_meta require api <NUM>'"
                ' lines found; ignoring module.',
                subpath,
            )
            self.results.announce_errors_occurred = True
        elif not lines and toplevel and meta_lines:
            # If we're a top-level module containing meta lines but no
            # valid "require api" line found, complain.
            logging.warning(
                "metascan: %s: no valid '# ba_meta require api <NUM>"
                ' line found; ignoring module.',
                subpath,
            )
            self.results.announce_errors_occurred = True
        return None
