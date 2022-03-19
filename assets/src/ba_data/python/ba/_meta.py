# Released under the MIT License. See LICENSE for details.
#
"""Functionality related to dynamic discoverability of classes."""

from __future__ import annotations

import os
import time
import pathlib
import threading
from typing import TYPE_CHECKING
from dataclasses import dataclass, field

import _ba

if TYPE_CHECKING:
    from typing import Union, Optional
    import ba

# The meta api version of this build of the game.
# Only packages and modules requiring this exact api version
# will be considered when scanning directories.
# See: https://ballistica.net/wiki/Meta-Tags
CURRENT_API_VERSION = 6


@dataclass
class ScanResults:
    """Final results from a metadata scan."""
    games: list[str] = field(default_factory=list)
    plugins: list[str] = field(default_factory=list)
    keyboards: list[str] = field(default_factory=list)
    errors: str = ''
    warnings: str = ''


class MetadataSubsystem:
    """Subsystem for working with script metadata in the app.

    Category: **App Classes**

    Access the single shared instance of this class at 'ba.app.meta'.
    """

    def __init__(self) -> None:
        self.metascan: Optional[ScanResults] = None

    def on_app_launch(self) -> None:
        """Should be called when the app is done bootstrapping."""

        # Start scanning for things exposed via ba_meta.
        self.start_scan()

    def start_scan(self) -> None:
        """Begin scanning script directories for scripts containing metadata.

        Should be called only once at launch."""
        app = _ba.app
        if self.metascan is not None:
            print('WARNING: meta scan run more than once.')
        pythondirs = [app.python_directory_app, app.python_directory_user]
        thread = ScanThread(pythondirs)
        thread.start()

    def handle_scan_results(self, results: ScanResults) -> None:
        """Called in the game thread with results of a completed scan."""

        from ba._language import Lstr
        from ba._plugin import PotentialPlugin

        # Warnings generally only get printed locally for users' benefit
        # (things like out-of-date scripts being ignored, etc.)
        # Errors are more serious and will get included in the regular log
        # warnings = results.get('warnings', '')
        # errors = results.get('errors', '')
        if results.warnings != '' or results.errors != '':
            import textwrap
            _ba.screenmessage(Lstr(resource='scanScriptsErrorText'),
                              color=(1, 0, 0))
            _ba.playsound(_ba.getsound('error'))
            if results.warnings != '':
                _ba.log(textwrap.indent(results.warnings,
                                        'Warning (meta-scan): '),
                        to_server=False)
            if results.errors != '':
                _ba.log(textwrap.indent(results.errors, 'Error (meta-scan): '))

        # Handle plugins.
        plugs = _ba.app.plugins
        config_changed = False
        found_new = False
        plugstates: dict[str, dict] = _ba.app.config.setdefault('Plugins', {})
        assert isinstance(plugstates, dict)

        # Create a potential-plugin for each class we found in the scan.
        for class_path in results.plugins:
            plugs.potential_plugins.append(
                PotentialPlugin(display_name=Lstr(value=class_path),
                                class_path=class_path,
                                available=True))
            if class_path not in plugstates:
                if _ba.app.headless_mode:
                    # If we running in headless mode, enable plugin by default
                    # to allow server admins to get their modified build
                    # working 'out-of-the-box', without manually updating the
                    # config.
                    plugstates[class_path] = {'enabled': True}
                else:
                    # If we running in normal mode, disable plugin by default
                    # (user can enable it later).
                    plugstates[class_path] = {'enabled': False}
                config_changed = True
                found_new = True

        # Also add a special one for any plugins set to load but *not* found
        # in the scan (this way they will show up in the UI so we can disable
        # them)
        for class_path, plugstate in plugstates.items():
            enabled = plugstate.get('enabled', False)
            assert isinstance(enabled, bool)
            if enabled and class_path not in results.plugins:
                plugs.potential_plugins.append(
                    PotentialPlugin(display_name=Lstr(value=class_path),
                                    class_path=class_path,
                                    available=False))

        plugs.potential_plugins.sort(key=lambda p: p.class_path)

        if found_new:
            _ba.screenmessage(Lstr(resource='pluginsDetectedText'),
                              color=(0, 1, 0))
            _ba.playsound(_ba.getsound('ding'))

        if config_changed:
            _ba.app.config.commit()

    def get_scan_results(self) -> ScanResults:
        """Return meta scan results; block if the scan is not yet complete."""
        if self.metascan is None:
            print('WARNING: ba.meta.get_scan_results()'
                  ' called before scan completed.'
                  ' This can cause hitches.')

            # Now wait a bit for the scan to complete.
            # Eventually error though if it doesn't.
            starttime = time.time()
            while self.metascan is None:
                time.sleep(0.05)
                if time.time() - starttime > 10.0:
                    raise TimeoutError(
                        'timeout waiting for meta scan to complete.')
        return self.metascan

    def get_game_types(self) -> list[type[ba.GameActivity]]:
        """Return available game types."""
        from ba._general import getclass
        from ba._gameactivity import GameActivity
        gameclassnames = self.get_scan_results().games
        gameclasses = []
        for gameclassname in gameclassnames:
            try:
                cls = getclass(gameclassname, GameActivity)
                gameclasses.append(cls)
            except Exception:
                from ba import _error
                _error.print_exception('error importing ' + str(gameclassname))
        unowned = self.get_unowned_game_types()
        return [cls for cls in gameclasses if cls not in unowned]

    def get_unowned_game_types(self) -> set[type[ba.GameActivity]]:
        """Return present game types not owned by the current account."""
        try:
            from ba import _store
            unowned_games: set[type[ba.GameActivity]] = set()
            if not _ba.app.headless_mode:
                for section in _store.get_store_layout()['minigames']:
                    for mname in section['items']:
                        if not _ba.get_purchased(mname):
                            m_info = _store.get_store_item(mname)
                            unowned_games.add(m_info['gametype'])
            return unowned_games
        except Exception:
            from ba import _error
            _error.print_exception('error calcing un-owned games')
            return set()


class ScanThread(threading.Thread):
    """Thread to scan script dirs for metadata."""

    def __init__(self, dirs: list[str]):
        super().__init__()
        self._dirs = dirs

    def run(self) -> None:
        from ba._general import Call
        try:
            scan = DirectoryScan(self._dirs)
            scan.scan()
            results = scan.results
        except Exception as exc:
            results = ScanResults(errors=f'Scan exception: {exc}')

        # Push a call to the game thread to print warnings/errors
        # or otherwise deal with scan results.
        _ba.pushcall(Call(_ba.app.meta.handle_scan_results, results),
                     from_other_thread=True)

        # We also, however, immediately make results available.
        # This is because the game thread may be blocked waiting
        # for them so we can't push a call or we'd get deadlock.
        _ba.app.meta.metascan = results


class DirectoryScan:
    """Handles scanning directories for metadata."""

    def __init__(self, paths: list[str]):
        """Given one or more paths, parses available meta information.

        It is assumed that these paths are also in PYTHONPATH.
        It is also assumed that any subdirectories are Python packages.
        """

        # Skip non-existent paths completely.
        self.paths = [pathlib.Path(p) for p in paths if os.path.isdir(p)]
        self.results = ScanResults()

    def _get_path_module_entries(
            self, path: pathlib.Path, subpath: Union[str, pathlib.Path],
            modules: list[tuple[pathlib.Path, pathlib.Path]]) -> None:
        """Scan provided path and add module entries to provided list."""
        try:
            # Special case: let's save some time and skip the whole 'ba'
            # package since we know it doesn't contain any meta tags.
            fullpath = pathlib.Path(path, subpath)
            entries = [(path, pathlib.Path(subpath, name))
                       for name in os.listdir(fullpath) if name != 'ba']
        except PermissionError:
            # Expected sometimes.
            entries = []
        except Exception as exc:
            # Unexpected; report this.
            self.results.errors += f'{exc}\n'
            entries = []

        # Now identify python packages/modules out of what we found.
        for entry in entries:
            if entry[1].name.endswith('.py'):
                modules.append(entry)
            elif (pathlib.Path(entry[0], entry[1]).is_dir() and pathlib.Path(
                    entry[0], entry[1], '__init__.py').is_file()):
                modules.append(entry)

    def scan(self) -> None:
        """Scan provided paths."""
        modules: list[tuple[pathlib.Path, pathlib.Path]] = []
        for path in self.paths:
            self._get_path_module_entries(path, '', modules)
        for moduledir, subpath in modules:
            try:
                self.scan_module(moduledir, subpath)
            except Exception:
                import traceback
                self.results.warnings += ("Error scanning '" + str(subpath) +
                                          "': " + traceback.format_exc() +
                                          '\n')
        # Sort our results
        self.results.games.sort()
        self.results.plugins.sort()

    def scan_module(self, moduledir: pathlib.Path,
                    subpath: pathlib.Path) -> None:
        """Scan an individual module and add the findings to results."""
        if subpath.name.endswith('.py'):
            fpath = pathlib.Path(moduledir, subpath)
            ispackage = False
        else:
            fpath = pathlib.Path(moduledir, subpath, '__init__.py')
            ispackage = True
        with fpath.open(encoding='utf-8') as infile:
            flines = infile.readlines()
        meta_lines = {
            lnum: l[1:].split()
            for lnum, l in enumerate(flines) if '# ba_meta ' in l
        }
        toplevel = len(subpath.parts) <= 1
        required_api = self.get_api_requirement(subpath, meta_lines, toplevel)

        # Top level modules with no discernible api version get ignored.
        if toplevel and required_api is None:
            return

        # If we find a module requiring a different api version, warn
        # and ignore.
        if required_api is not None and required_api != CURRENT_API_VERSION:
            self.results.warnings += (
                f'Warning: {subpath} requires api {required_api} but'
                f' we are running {CURRENT_API_VERSION}; ignoring module.\n')
            return

        # Ok; can proceed with a full scan of this module.
        self._process_module_meta_tags(subpath, flines, meta_lines)

        # If its a package, recurse into its subpackages.
        if ispackage:
            try:
                submodules: list[tuple[pathlib.Path, pathlib.Path]] = []
                self._get_path_module_entries(moduledir, subpath, submodules)
                for submodule in submodules:
                    if submodule[1].name != '__init__.py':
                        self.scan_module(submodule[0], submodule[1])
            except Exception:
                import traceback
                self.results.warnings += (
                    f"Error scanning '{subpath}': {traceback.format_exc()}\n")

    def _process_module_meta_tags(self, subpath: pathlib.Path,
                                  flines: list[str],
                                  meta_lines: dict[int, list[str]]) -> None:
        """Pull data from a module based on its ba_meta tags."""
        for lindex, mline in meta_lines.items():
            # meta_lines is just anything containing '# ba_meta '; make sure
            # the ba_meta is in the right place.
            if mline[0] != 'ba_meta':
                self.results.warnings += (
                    'Warning: ' + str(subpath) +
                    ': malformed ba_meta statement on line ' +
                    str(lindex + 1) + '.\n')
            elif (len(mline) == 4 and mline[1] == 'require'
                  and mline[2] == 'api'):
                # Ignore 'require api X' lines in this pass.
                pass
            elif len(mline) != 3 or mline[1] != 'export':
                # Currently we only support 'ba_meta export FOO';
                # complain for anything else we see.
                self.results.warnings += (
                    'Warning: ' + str(subpath) +
                    ': unrecognized ba_meta statement on line ' +
                    str(lindex + 1) + '.\n')
            else:
                # Looks like we've got a valid export line!
                modulename = '.'.join(subpath.parts)
                if subpath.name.endswith('.py'):
                    modulename = modulename[:-3]
                exporttype = mline[2]
                export_class_name = self._get_export_class_name(
                    subpath, flines, lindex)
                if export_class_name is not None:
                    classname = modulename + '.' + export_class_name
                    if exporttype == 'game':
                        self.results.games.append(classname)
                    elif exporttype == 'plugin':
                        self.results.plugins.append(classname)
                    elif exporttype == 'keyboard':
                        self.results.keyboards.append(classname)
                    else:
                        self.results.warnings += (
                            'Warning: ' + str(subpath) +
                            ': unrecognized export type "' + exporttype +
                            '" on line ' + str(lindex + 1) + '.\n')

    def _get_export_class_name(self, subpath: pathlib.Path, lines: list[str],
                               lindex: int) -> Optional[str]:
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
            self.results.warnings += (
                'Warning: ' + str(subpath) + ': class definition not found'
                ' below "ba_meta export" statement on line ' +
                str(lindexorig + 1) + '.\n')
        return classname

    def get_api_requirement(self, subpath: pathlib.Path,
                            meta_lines: dict[int, list[str]],
                            toplevel: bool) -> Optional[int]:
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
            self.results.warnings += (
                'Warning: ' + str(subpath) +
                ': multiple "# ba_meta api require <NUM>" lines found;'
                ' ignoring module.\n')
        elif not lines and toplevel and meta_lines:
            # If we're a top-level module containing meta lines but
            # no valid api require, complain.
            self.results.warnings += (
                'Warning: ' + str(subpath) +
                ': no valid "# ba_meta api require <NUM>" line found;'
                ' ignoring module.\n')
        return None
