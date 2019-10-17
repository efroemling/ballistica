# Copyright (c) 2011-2019 Eric Froemling
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
# -----------------------------------------------------------------------------
"""Functionality related to dynamic discoverability of classes."""

from __future__ import annotations

import os
import pathlib
import threading
from typing import TYPE_CHECKING

import _ba

if TYPE_CHECKING:
    from typing import (Any, Dict, List, Tuple, Union, Optional, Type, Set)
    import ba

# The API version of this build of the game.
# Only packages and modules requiring this exact api version
# will be considered when scanning directories.
# See bombsquadgame.com/apichanges for differences between api versions.
CURRENT_API_VERSION = 6


def startscan() -> None:
    """Begin scanning script directories for scripts containing metadata.

    Should be called only once at launch."""
    app = _ba.app
    if app.metascan is not None:
        print('WARNING: meta scan run more than once.')
    scriptdirs = [app.system_scripts_directory, app.user_scripts_directory]
    thread = ScanThread(scriptdirs)
    thread.start()


def handle_scan_results(results: Dict[str, Any]) -> None:
    """Called in the game thread with results of a completed scan."""
    from ba import _lang

    # Warnings generally only get printed locally for users' benefit
    # (things like out-of-date scripts being ignored, etc.)
    # Errors are more serious and will get included in the regular log
    warnings = results.get('warnings', '')
    errors = results.get('errors', '')
    if warnings != '' or errors != '':
        _ba.screenmessage(_lang.Lstr(resource='scanScriptsErrorText'),
                          color=(1, 0, 0))
        _ba.playsound(_ba.getsound('error'))
        if warnings != '':
            _ba.log(warnings, to_server=False)
        if errors != '':
            _ba.log(errors)


class ScanThread(threading.Thread):
    """Thread to scan script dirs for metadata."""

    def __init__(self, dirs: List[str]):
        super().__init__()
        self._dirs = dirs

    def run(self) -> None:
        from ba import _general
        try:
            scan = DirectoryScan(self._dirs)
            scan.scan()
            results = scan.results
        except Exception as exc:
            results = {'errors': 'Scan exception: ' + str(exc)}

        # Push a call to the game thread to print warnings/errors
        # or otherwise deal with scan results.
        _ba.pushcall(_general.Call(handle_scan_results, results),
                     from_other_thread=True)

        # We also, however, immediately make results available.
        # This is because the game thread may be blocked waiting
        # for them so we can't push a call or we'd get deadlock.
        _ba.app.metascan = results


class DirectoryScan:
    """Handles scanning directories for metadata."""

    def __init__(self, paths: List[str]):
        """Given one or more paths, parses available meta information.

        It is assumed that these paths are also in PYTHONPATH.
        It is also assumed that any subdirectories are Python packages.
        The returned dict contains the following:
        'powerups': list of ba.Powerup classes found.
        'campaigns': list of ba.Campaign classes found.
        'modifiers': list of ba.Modifier classes found.
        'maps': list of ba.Map classes found.
        'games': list of ba.GameActivity classes found.
        'warnings': warnings from scan; should be printed for local feedback
        'errors': errors encountered during scan; should be fully logged
        """
        self.paths = [pathlib.Path(p) for p in paths]
        self.results: Dict[str, Any] = {
            'errors': '',
            'warnings': '',
            'games': []
        }

    def _get_path_module_entries(
            self, path: pathlib.Path, subpath: Union[str, pathlib.Path],
            modules: List[Tuple[pathlib.Path, pathlib.Path]]) -> None:
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
            self.results['errors'] += str(exc) + '\n'
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
        modules: List[Tuple[pathlib.Path, pathlib.Path]] = []
        for path in self.paths:
            self._get_path_module_entries(path, '', modules)
        for moduledir, subpath in modules:
            try:
                self.scan_module(moduledir, subpath)
            except Exception:
                from ba import _error
                self.results['warnings'] += ("Error scanning '" +
                                             str(subpath) + "': " +
                                             _error.exc_str() + '\n')

    def scan_module(self, moduledir: pathlib.Path,
                    subpath: pathlib.Path) -> None:
        """Scan an individual module and add the findings to results."""
        if subpath.name.endswith('.py'):
            fpath = pathlib.Path(moduledir, subpath)
            ispackage = False
        else:
            fpath = pathlib.Path(moduledir, subpath, '__init__.py')
            ispackage = True
        with fpath.open() as infile:
            flines = infile.readlines()
        meta_lines = {
            lnum: l[1:].split()
            for lnum, l in enumerate(flines) if 'bs_meta' in l
        }
        toplevel = len(subpath.parts) <= 1
        required_api = self.get_api_requirement(subpath, meta_lines, toplevel)

        # Top level modules with no discernible api version get ignored.
        if toplevel and required_api is None:
            return

        # If we find a module requiring a different api version, warn
        # and ignore.
        if required_api is not None and required_api != CURRENT_API_VERSION:
            self.results['warnings'] += ('Warning: ' + str(subpath) +
                                         ' requires api ' + str(required_api) +
                                         ' but we are running ' +
                                         str(CURRENT_API_VERSION) +
                                         '; ignoring module.\n')
            return

        # Ok; can proceed with a full scan of this module.
        self._process_module_meta_tags(subpath, flines, meta_lines)

        # If its a package, recurse into its subpackages.
        if ispackage:
            try:
                submodules: List[Tuple[pathlib.Path, pathlib.Path]] = []
                self._get_path_module_entries(moduledir, subpath, submodules)
                for submodule in submodules:
                    self.scan_module(submodule[0], submodule[1])
            except Exception:
                from ba import _error
                self.results['warnings'] += ("Error scanning '" +
                                             str(subpath) + "': " +
                                             _error.exc_str() + '\n')

    def _process_module_meta_tags(self, subpath: pathlib.Path,
                                  flines: List[str],
                                  meta_lines: Dict[int, List[str]]) -> None:
        """Pull data from a module based on its bs_meta tags."""
        for lindex, mline in meta_lines.items():
            # meta_lines is just anything containing 'bs_meta'; make sure
            # the bs_meta is in the right place.
            if mline[0] != 'bs_meta':
                self.results['warnings'] += (
                    'Warning: ' + str(subpath) +
                    ': malformed bs_meta statement on line ' +
                    str(lindex + 1) + '.\n')
            elif (len(mline) == 4 and mline[1] == 'require'
                  and mline[2] == 'api'):
                # Ignore 'require api X' lines in this pass.
                pass
            elif len(mline) != 3 or mline[1] != 'export':
                # Currently we only support 'bs_meta export FOO';
                # complain for anything else we see.
                self.results['warnings'] += (
                    'Warning: ' + str(subpath) +
                    ': unrecognized bs_meta statement on line ' +
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
                        self.results['games'].append(classname)
                    else:
                        self.results['warnings'] += (
                            'Warning: ' + str(subpath) +
                            ': unrecognized export type "' + exporttype +
                            '" on line ' + str(lindex + 1) + '.\n')

    def _get_export_class_name(self, subpath: pathlib.Path, lines: List[str],
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
                    break  # success!
        if classname is None:
            self.results['warnings'] += (
                'Warning: ' + str(subpath) + ': class definition not found'
                ' below "bs_meta export" statement on line ' +
                str(lindexorig + 1) + '.\n')
        return classname

    def get_api_requirement(self, subpath: pathlib.Path,
                            meta_lines: Dict[int, List[str]],
                            toplevel: bool) -> Optional[int]:
        """Return an API requirement integer or None if none present.

        Malformed api requirement strings will be logged as warnings.
        """
        lines = [
            l for l in meta_lines.values() if len(l) == 4 and l[0] == 'bs_meta'
            and l[1] == 'require' and l[2] == 'api' and l[3].isdigit()
        ]

        # we're successful if we find exactly one properly formatted line
        if len(lines) == 1:
            return int(lines[0][3])

        # Ok; not successful. lets issue warnings for a few error cases.
        if len(lines) > 1:
            self.results['warnings'] += (
                'Warning: ' + str(subpath) +
                ': multiple "# bs_meta api require <NUM>" lines found;'
                ' ignoring module.\n')
        elif not lines and toplevel and meta_lines:
            # If we're a top-level module containing meta lines but
            # no valid api require, complain.
            self.results['warnings'] += (
                'Warning: ' + str(subpath) +
                ': no valid "# bs_meta api require <NUM>" line found;'
                ' ignoring module.\n')
        return None


def getscanresults() -> Dict[str, Any]:
    """Return meta scan results; blocking if the scan is not yet complete."""
    import time
    app = _ba.app
    if app.metascan is None:
        print('WARNING: ba.meta.getscanresults() called before scan completed.'
              ' This can cause hitches.')

        # Now wait a bit for the scan to complete.
        # Eventually error though if it doesn't.
        starttime = time.time()
        while app.metascan is None:
            time.sleep(0.05)
            if time.time() - starttime > 10.0:
                raise Exception('timeout waiting for meta scan to complete.')
    return app.metascan


def get_game_types() -> List[Type[ba.GameActivity]]:
    """Return available game types."""
    from ba import _general
    from ba import _gameactivity
    gameclassnames = getscanresults().get('games', [])
    gameclasses = []
    for gameclassname in gameclassnames:
        try:
            cls = _general.getclass(gameclassname, _gameactivity.GameActivity)
            gameclasses.append(cls)
        except Exception:
            from ba import _error
            _error.print_exception('error importing ' + str(gameclassname))
    unowned = get_unowned_game_types()
    return [cls for cls in gameclasses if cls not in unowned]


def get_unowned_game_types() -> Set[Type[ba.GameActivity]]:
    """Return present game types not owned by the current account."""
    try:
        from ba import _store
        unowned_games: Set[Type[ba.GameActivity]] = set()
        if _ba.app.subplatform != 'headless':
            for section in _store.get_store_layout()['minigames']:
                for mname in section['items']:
                    if not _ba.get_purchased(mname):
                        m_info = _store.get_store_item(mname)
                        unowned_games.add(m_info['gametype'])
        return unowned_games
    except Exception:
        from ba import _error
        _error.print_exception("error calcing un-owned games")
        return set()
