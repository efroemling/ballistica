# Released under the MIT License. See LICENSE for details.
#
"""Functionality related to dynamic discoverability of classes."""

from __future__ import annotations

import os
import time
import logging
from threading import Thread
from pathlib import Path
from typing import TYPE_CHECKING, TypeVar
from dataclasses import dataclass, field

from efro.call import tpartial
import _ba

if TYPE_CHECKING:
    from typing import Callable

# The meta api version of this build of the game.
# Only packages and modules requiring this exact api version
# will be considered when scanning directories.
# See: https://ballistica.net/wiki/Meta-Tag-System
CURRENT_API_VERSION = 7

# Meta export lines can use these names to represent these classes.
# This is purely a convenience; it is possible to use full class paths
# instead of these or to make the meta system aware of arbitrary classes.
EXPORT_CLASS_NAME_SHORTCUTS: dict[str, str] = {
    'plugin': 'ba.Plugin',
    'keyboard': 'ba.Keyboard',
    'game': 'ba.GameActivity',
}

T = TypeVar('T')


@dataclass
class ScanResults:
    """Final results from a meta-scan."""
    exports: dict[str, list[str]] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def exports_of_class(self, cls: type) -> list[str]:
        """Return exports of a given class."""
        return self.exports.get(f'{cls.__module__}.{cls.__qualname__}', [])


class MetadataSubsystem:
    """Subsystem for working with script metadata in the app.

    Category: **App Classes**

    Access the single shared instance of this class at 'ba.app.meta'.
    """

    def __init__(self) -> None:

        self._scan: DirectoryScan | None = None

        # Can be populated before starting the scan.
        self.extra_scan_dirs: list[str] = []

        # Results populated once scan is complete.
        self.scanresults: ScanResults | None = None

        self._scan_complete_cb: Callable[[], None] | None = None

    def start_scan(self, scan_complete_cb: Callable[[], None]) -> None:
        """Begin the overall scan.

        This will start scanning built in directories (which for vanilla
        installs should be the vast majority of the work). This should only
        be called once.
        """
        assert self._scan_complete_cb is None
        assert self._scan is None

        self._scan_complete_cb = scan_complete_cb
        self._scan = DirectoryScan(
            [_ba.app.python_directory_app, _ba.app.python_directory_user])

        Thread(target=self._run_scan_in_bg, daemon=True).start()

    def start_extra_scan(self) -> None:
        """Proceed to the extra_scan_dirs portion of the scan.

        This is for parts of the scan that must be delayed until
        workspace sync completion or other such events. This must be
        called exactly once.
        """
        assert self._scan is not None
        self._scan.set_extras(self.extra_scan_dirs)

    def load_exported_classes(
        self,
        cls: type[T],
        completion_cb: Callable[[list[type[T]]], None],
        completion_cb_in_bg_thread: bool = False,
    ) -> None:
        """High level function to load meta-exported classes.

        Will wait for scanning to complete if necessary, and will load all
        registered classes of a particular type in a background thread before
        calling the passed callback in the logic thread. Errors may be logged
        to messaged to the user in some way but the callback will be called
        regardless.
        To run the completion callback directly in the bg thread where the
        loading work happens, pass completion_cb_in_bg_thread=True.
        """
        Thread(
            target=tpartial(self._load_exported_classes, cls, completion_cb,
                            completion_cb_in_bg_thread),
            daemon=True,
        ).start()

    def _load_exported_classes(
        self,
        cls: type[T],
        completion_cb: Callable[[list[type[T]]], None],
        completion_cb_in_bg_thread: bool,
    ) -> None:
        from ba._general import getclass
        classes: list[type[T]] = []
        try:
            classnames = self._wait_for_scan_results().exports_of_class(cls)
            for classname in classnames:
                try:
                    classes.append(getclass(classname, cls))
                except Exception:
                    logging.exception('error importing %s', classname)

        except Exception:
            logging.exception('Error loading exported classes.')

        completion_call = tpartial(completion_cb, classes)
        if completion_cb_in_bg_thread:
            completion_call()
        else:
            _ba.pushcall(completion_call, from_other_thread=True)

    def _wait_for_scan_results(self) -> ScanResults:
        """Return scan results, blocking if the scan is not yet complete."""
        if self.scanresults is None:
            if _ba.in_logic_thread():
                logging.warning(
                    'ba.meta._wait_for_scan_results()'
                    ' called in logic thread before scan completed;'
                    ' this can cause hitches.')

            # Now wait a bit for the scan to complete.
            # Eventually error though if it doesn't.
            starttime = time.time()
            while self.scanresults is None:
                time.sleep(0.05)
                if time.time() - starttime > 10.0:
                    raise TimeoutError(
                        'timeout waiting for meta scan to complete.')
        return self.scanresults

    def _run_scan_in_bg(self) -> None:
        """Runs a scan (for use in background thread)."""
        try:
            assert self._scan is not None
            self._scan.run()
            results = self._scan.results
            self._scan = None
        except Exception as exc:
            results = ScanResults(errors=[f'Scan exception: {exc}'])

        # Place results and tell the logic thread they're ready.
        self.scanresults = results
        _ba.pushcall(self._handle_scan_results, from_other_thread=True)

    def _handle_scan_results(self) -> None:
        """Called in the logic thread with results of a completed scan."""
        from ba._language import Lstr
        assert _ba.in_logic_thread()

        results = self.scanresults
        assert results is not None

        # Spit out any warnings/errors that happened.
        # Warnings generally only get printed locally for users' benefit
        # (things like out-of-date scripts being ignored, etc.)
        # Errors are more serious and will get included in the regular log.
        if results.warnings or results.errors:
            import textwrap
            _ba.screenmessage(Lstr(resource='scanScriptsErrorText'),
                              color=(1, 0, 0))
            _ba.playsound(_ba.getsound('error'))
            if results.warnings:
                _ba.log(textwrap.indent('\n'.join(results.warnings),
                                        'Warning (meta-scan): '),
                        to_server=False)
            if results.errors:
                _ba.log(
                    textwrap.indent('\n'.join(results.errors),
                                    'Error (meta-scan): '))

        # Let the game know we're done.
        assert self._scan_complete_cb is not None
        self._scan_complete_cb()


class DirectoryScan:
    """Scans directories for metadata."""

    def __init__(self, paths: list[str]):
        """Given one or more paths, parses available meta information.

        It is assumed that these paths are also in PYTHONPATH.
        It is also assumed that any subdirectories are Python packages.
        """

        # Skip non-existent paths completely.
        self.base_paths = [Path(p) for p in paths if os.path.isdir(p)]
        self.extra_paths: list[Path] = []
        self.extra_paths_set = False
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
                    import traceback
                    self.results.warnings.append(
                        f"Error scanning '{subpath}': " +
                        traceback.format_exc())

        # Sort our results
        for exportlist in self.results.exports.values():
            exportlist.sort()

    def _get_path_module_entries(self, path: Path, subpath: str | Path,
                                 modules: list[tuple[Path, Path]]) -> None:
        """Scan provided path and add module entries to provided list."""
        try:
            # Special case: let's save some time and skip the whole 'ba'
            # package since we know it doesn't contain any meta tags.
            fullpath = Path(path, subpath)
            entries = [(path, Path(subpath, name))
                       for name in os.listdir(fullpath) if name != 'ba']
        except PermissionError:
            # Expected sometimes.
            entries = []
        except Exception as exc:
            # Unexpected; report this.
            self.results.errors.append(str(exc))
            entries = []

        # Now identify python packages/modules out of what we found.
        for entry in entries:
            if entry[1].name.endswith('.py'):
                modules.append(entry)
            elif (Path(entry[0], entry[1]).is_dir()
                  and Path(entry[0], entry[1], '__init__.py').is_file()):
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
            for lnum, l in enumerate(flines) if '# ba_meta ' in l
        }
        is_top_level = len(subpath.parts) <= 1
        required_api = self._get_api_requirement(subpath, meta_lines,
                                                 is_top_level)

        # Top level modules with no discernible api version get ignored.
        if is_top_level and required_api is None:
            return

        # If we find a module requiring a different api version, warn
        # and ignore.
        if required_api is not None and required_api != CURRENT_API_VERSION:
            self.results.warnings.append(
                f'Warning: {subpath} requires api {required_api} but'
                f' we are running {CURRENT_API_VERSION}; ignoring module.')
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
                import traceback
                self.results.warnings.append(
                    f"Error scanning '{subpath}': {traceback.format_exc()}")

    def _process_module_meta_tags(self, subpath: Path, flines: list[str],
                                  meta_lines: dict[int, list[str]]) -> None:
        """Pull data from a module based on its ba_meta tags."""
        for lindex, mline in meta_lines.items():
            # meta_lines is just anything containing '# ba_meta '; make sure
            # the ba_meta is in the right place.
            if mline[0] != 'ba_meta':
                self.results.warnings.append(
                    f'Warning: {subpath}:'
                    f' malformed ba_meta statement on line {lindex + 1}.')
            elif (len(mline) == 4 and mline[1] == 'require'
                  and mline[2] == 'api'):
                # Ignore 'require api X' lines in this pass.
                pass
            elif len(mline) != 3 or mline[1] != 'export':
                # Currently we only support 'ba_meta export FOO';
                # complain for anything else we see.
                self.results.warnings.append(
                    f'Warning: {subpath}'
                    f': unrecognized ba_meta statement on line {lindex + 1}.')
            else:
                # Looks like we've got a valid export line!
                modulename = '.'.join(subpath.parts)
                if subpath.name.endswith('.py'):
                    modulename = modulename[:-3]
                exporttypestr = mline[2]
                export_class_name = self._get_export_class_name(
                    subpath, flines, lindex)
                if export_class_name is not None:
                    classname = modulename + '.' + export_class_name

                    # If export type is one of our shortcuts, sub in the
                    # actual class path. Otherwise assume its a classpath
                    # itself.
                    exporttype = EXPORT_CLASS_NAME_SHORTCUTS.get(exporttypestr)
                    if exporttype is None:
                        exporttype = exporttypestr
                    self.results.exports.setdefault(exporttype,
                                                    []).append(classname)

    def _get_export_class_name(self, subpath: Path, lines: list[str],
                               lindex: int) -> str | None:
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
            self.results.warnings.append(
                f'Warning: {subpath}: class definition not found below'
                f' "ba_meta export" statement on line {lindexorig + 1}.')
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
            l for l in meta_lines.values() if len(l) == 4 and l[0] == 'ba_meta'
            and l[1] == 'require' and l[2] == 'api' and l[3].isdigit()
        ]

        # We're successful if we find exactly one properly formatted line.
        if len(lines) == 1:
            return int(lines[0][3])

        # Ok; not successful. lets issue warnings for a few error cases.
        if len(lines) > 1:
            self.results.warnings.append(
                f'Warning: {subpath}: multiple'
                ' "# ba_meta require api <NUM>" lines found;'
                ' ignoring module.')
        elif not lines and toplevel and meta_lines:
            # If we're a top-level module containing meta lines but
            # no valid "require api" line found, complain.
            self.results.warnings.append(
                f'Warning: {subpath}:'
                ' no valid "# ba_meta require api <NUM>" line found;'
                ' ignoring module.')
        return None
