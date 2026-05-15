# Released under the MIT License. See LICENSE for details.
#
"""Functionality related to dynamic discoverability of classes."""

from __future__ import annotations

import time
import logging
from threading import Thread
from functools import partial
from typing import TYPE_CHECKING

import _babase

from bacommon.metascan import DirectoryScan, ScanResults
from babase._logging import lifecyclelog

if TYPE_CHECKING:
    from typing import Callable


# Legacy export-type shortcut names. The scanner substitutes the
# canonical class path and emits a deprecation warning when it sees
# any of these.
_DEPRECATED_EXPORT_SHORTCUTS: dict[str, str] = {
    # DEPRECATED as of 6/2025.
    'plugin': 'babase.Plugin',
    # DEPRECATED as of 12/2023.
    'keyboard': 'bauiv1.Keyboard',
}


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
            paths=[
                path
                for path in [
                    env.python_directory_app,
                    env.python_directory_user,
                ]
                if path is not None
            ],
            expected_api_version=env.api_version,
            deprecated_export_shortcuts=_DEPRECATED_EXPORT_SHORTCUTS,
            expects_extras=True,
        )

        lifecyclelog.info('meta-scan bg thread kicked off')
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
        lifecyclelog.info('meta-scan bg thread done')
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
