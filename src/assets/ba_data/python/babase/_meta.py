# Released under the MIT License. See LICENSE for details.
#
"""Functionality related to dynamic discoverability of classes."""

from __future__ import annotations

import os
import time
import logging
from pathlib import Path
from threading import Thread
from functools import partial
from typing import TYPE_CHECKING
from dataclasses import dataclass, field

import _babase

if TYPE_CHECKING:
    from typing import Callable


# Meta export lines can use these names to represent these classes.
# This is purely a convenience; it is possible to use full class paths
# instead of these or to make the meta system aware of arbitrary classes.
EXPORT_CLASS_NAME_SHORTCUTS: dict[str, str] = {
    # DEPRECATED as of 6/2025. Currently am warning if finding these
    # but should take this out eventually.
    'plugin': 'babase.Plugin',
    # DEPRECATED as of 12/2023. Currently am warning if finding these
    # but should take this out eventually.
    'keyboard': 'bauiv1.Keyboard',
}


@dataclass
class ScanResults:
    """Final results from a meta-scan."""

    exports: dict[str, list[str]] = field(default_factory=dict)
    incorrect_api_modules: list[str] = field(default_factory=list)
    announce_errors_occurred: bool = False

    def exports_by_name(self, name: str) -> list[str]:
        """Return exports matching a given name."""
        return self.exports.get(name, [])


class MetadataSubsystem:
    """Subsystem for working with script metadata in the app.

    Access the single shared instance of this class via the
    :attr:`~babase.App.meta` attr on the :class:`~babase.App` class.
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
        installs should be the vast majority of the work). This should
        only be called once.

        :meta private:
        """
        assert self._scan_complete_cb is None
        assert self._scan is None
        env = _babase.app.env

        self._scan_complete_cb = scan_complete_cb
        self._scan = DirectoryScan(
            [
                path
                for path in [
                    env.python_directory_app,
                    env.python_directory_user,
                ]
                if path is not None
            ]
        )

        Thread(target=self._run_scan_in_bg).start()

    def start_extra_scan(self) -> None:
        """Proceed to the extra_scan_dirs portion of the scan.

        This is for parts of the scan that must be delayed until
        workspace sync completion or other such events. This must be
        called exactly once.

        :meta private:
        """
        assert self._scan is not None
        self._scan.set_extras(self.extra_scan_dirs)

    def load_exported_classes[T](
        self,
        exportname: str,
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
        loading work happens, pass ``completion_cb_in_bg_thread=True``.
        """
        Thread(
            target=partial(
                self._load_exported_classes,
                exportname,
                cls,
                completion_cb,
                completion_cb_in_bg_thread,
            )
        ).start()

    def _load_exported_classes[T](
        self,
        exportname: str,
        cls: type[T],
        completion_cb: Callable[[list[type[T]]], None],
        completion_cb_in_bg_thread: bool,
    ) -> None:
        from babase._general import getclass

        classes: list[type[T]] = []
        try:
            # classnames = self._wait_for_scan_results().exports_of_class(cls)
            classnames = self._wait_for_scan_results().exports.get(
                exportname, []
            )
            for classname in classnames:
                try:
                    classes.append(getclass(classname, cls))
                except Exception:
                    logging.exception('error importing %s', classname)

        except Exception:
            logging.exception('Error loading exported classes.')

        completion_call = partial(completion_cb, classes)
        if completion_cb_in_bg_thread:
            completion_call()
        else:
            _babase.pushcall(completion_call, from_other_thread=True)

    def _wait_for_scan_results(self) -> ScanResults:
        """Return scan results, blocking if the scan is not yet complete."""
        if self.scanresults is None:
            if _babase.in_logic_thread():
                logging.warning(
                    'babase.meta._wait_for_scan_results()'
                    ' called in logic thread before scan completed;'
                    ' this can cause hitches.'
                )

            # Now wait a bit for the scan to complete. Eventually error
            # though if it doesn't.
            starttime = time.time()
            while self.scanresults is None:
                time.sleep(0.05)
                if time.time() - starttime > 10.0:
                    raise TimeoutError(
                        'timeout waiting for meta scan to complete.'
                    )

        return self.scanresults

    def _run_scan_in_bg(self) -> None:
        """Runs a scan (for use in background thread)."""
        try:
            assert self._scan is not None
            self._scan.run()
            results = self._scan.results
            self._scan = None
        except Exception:
            logging.exception('metascan: Error running scan in bg.')
            results = ScanResults(announce_errors_occurred=True)

        # Place results and tell the logic thread they're ready.
        self.scanresults = results
        _babase.pushcall(self._handle_scan_results, from_other_thread=True)

    def _handle_scan_results(self) -> None:
        """Called in the logic thread with results of a completed scan."""
        from babase._language import Lstr

        assert _babase.in_logic_thread()

        results = self.scanresults
        assert results is not None

        do_play_error_sound = False

        # If we found modules needing to be updated to the newer api version,
        # mention that specifically.
        if results.incorrect_api_modules:
            if len(results.incorrect_api_modules) > 1:
                msg = Lstr(
                    resource='scanScriptsMultipleModulesNeedUpdatesText',
                    subs=[
                        ('${PATH}', results.incorrect_api_modules[0]),
                        (
                            '${NUM}',
                            str(len(results.incorrect_api_modules) - 1),
                        ),
                        ('${API}', str(_babase.app.env.api_version)),
                    ],
                )
            else:
                msg = Lstr(
                    resource='scanScriptsSingleModuleNeedsUpdatesText',
                    subs=[
                        ('${PATH}', results.incorrect_api_modules[0]),
                        ('${API}', str(_babase.app.env.api_version)),
                    ],
                )
            _babase.screenmessage(msg, color=(1, 0, 0))
            do_play_error_sound = True

        # Let the user know if there's warning/errors in their log
        # they may want to look at.
        if results.announce_errors_occurred:
            _babase.screenmessage(
                Lstr(resource='scanScriptsErrorText'), color=(1, 0, 0)
            )
            do_play_error_sound = True

        if do_play_error_sound:
            _babase.getsimplesound('error').play()

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
                    logging.exception("metascan: Error scanning '%s'.", subpath)

        # Sort our results.
        for exportlist in self.results.exports.values():
            exportlist.sort()

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

        # If we find a module requiring a different api version, warn
        # and ignore.
        if (
            required_api is not None
            and required_api != _babase.app.env.api_version
        ):
            logging.warning(
                'metascan: %s requires api %s but we are running'
                ' %s. Ignoring module.',
                subpath,
                required_api,
                _babase.app.env.api_version,
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
        self, subpath: Path, flines: list[str], meta_lines: dict[int, list[str]]
    ) -> None:
        """Pull data from a module based on its ba_meta tags."""
        for lindex, mline in meta_lines.items():
            # meta_lines is just anything containing '# ba_meta '; make sure
            # the ba_meta is in the right place.
            if mline[0] != 'ba_meta':
                # Make an exception for this specific file, otherwise we
                # get lots of warnings about ba_meta showing up in weird
                # places here.
                if subpath.as_posix() != 'babase/_meta.py':
                    logging.warning(
                        'metascan: %s:%d: malformed ba_meta statement.',
                        subpath,
                        lindex + 1,
                    )
                    self.results.announce_errors_occurred = True
            elif (
                len(mline) == 4 and mline[1] == 'require' and mline[2] == 'api'
            ):
                # Ignore 'require api X' lines in this pass.
                pass
            elif len(mline) != 3 or mline[1] != 'export':
                # Currently we only support 'ba_meta export FOO';
                # complain for anything else we see.
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

                    # Migrating away from the 'plugin' name shortcut;
                    # warn if we find it.
                    if exporttypestr == 'plugin':
                        logging.warning(
                            "metascan: %s:%d: '# ba_meta export"
                            " plugin' tag should be replaced by '# ba_meta"
                            " export babase.Plugin'.",
                            subpath,
                            lindex + 1,
                        )
                        self.results.announce_errors_occurred = True

                    # Migrating away from the 'keyboard' name shortcut;
                    # warn if we find it.
                    if exporttypestr == 'keyboard':
                        logging.warning(
                            "metascan: %s:%d: '# ba_meta export"
                            " keyboard' tag should be replaced by '# ba_meta"
                            " export bauiv1.Keyboard'.",
                            subpath,
                            lindex + 1,
                        )
                        self.results.announce_errors_occurred = True

                    # If export type is one of our shortcuts, sub in the
                    # actual class path. Otherwise assume its a classpath
                    # itself.
                    exporttype = EXPORT_CLASS_NAME_SHORTCUTS.get(exporttypestr)
                    if exporttype is None:
                        exporttype = exporttypestr
                    self.results.exports.setdefault(exporttype, []).append(
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
