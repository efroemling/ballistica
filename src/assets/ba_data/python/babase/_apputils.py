# Released under the MIT License. See LICENSE for details.
#
"""Utility functionality related to the overall operation of the app."""

import os
import time
import asyncio
import threading
from functools import partial
from dataclasses import dataclass
from typing import TYPE_CHECKING, override

from efro.util import utc_now
from efro.logging import LogLevel
from efro.dataclassio import ioprepped, dataclass_to_json, dataclass_from_json

import _babase
from babase._appsubsystem import AppSubsystem
from babase._logging import balog

if TYPE_CHECKING:
    import datetime
    from typing import Any, TextIO, Callable

    import babase


def utc_now_cloud() -> datetime.datetime:
    """Returns estimated utc time regardless of local clock settings.

    Applies offsets pulled from server communication/etc.
    """
    # TODO: wire this up. Just using local time for now. Make sure that
    # BaseFeatureSet::TimeSinceEpochCloudSeconds() and this are synced
    # up.
    return utc_now()


def is_browser_likely_available() -> bool:
    """Return whether a browser likely exists on the current device.

    If this returns False, you may want to avoid calling
    :meth:`~babase.open_url()` with any lengthy addresses.
    (:meth:`~babase.open_url()` will display an address as a
    string/qr-code in a window if unable to bring up a browser, but that
    is only reasonable for small-ish URLs.)
    """
    app = _babase.app

    if app.classic is None:
        balog.warning(
            'is_browser_likely_available() needs to be updated'
            ' to work without classic.'
        )
        return True

    platform = app.classic.platform
    hastouchscreen = _babase.hastouchscreen()

    # If we're on a vr device or an android device with no touchscreen,
    # assume no browser.
    # FIXME: Might not be the case anymore; should make this definable
    #  at the platform level.
    if app.env.vr or (platform == 'android' and not hastouchscreen):
        return False

    # Anywhere else assume we've got one.
    return True


def should_submit_debug_info() -> bool:
    """:meta private:"""
    val = _babase.app.config.get('Submit Debug Info', True)
    assert isinstance(val, bool)
    return val


def print_corrupt_file_error() -> None:
    """Print an error if a corrupt file is found."""
    from babase import builtinassets

    if _babase.app.env.gui:
        _babase.apptimer(
            2.0,
            lambda: _babase.screenmessage(
                _babase.app.lang.get_resource(
                    'internal.corruptFileText'
                ).replace('${EMAIL}', 'support@froemling.net'),
                color=(1, 0, 0),
            ),
        )
        _babase.apptimer(2.0, builtinassets.audio.error.get().play)


_tb_held_files: list[TextIO] = []


@ioprepped
@dataclass
class DumpedAppStateMetadata:
    """High level info about a dumped app state."""

    reason: str
    app_time: float
    log_level: LogLevel


def dump_app_state(
    delay: float = 0.0,
    reason: str = 'Unspecified',
    log_level: LogLevel = LogLevel.WARNING,
) -> None:
    """Dump various app state for debugging purposes.

    This includes stack traces for all Python threads (and potentially
    other info in the future).

    This is intended for use debugging deadlock situations. It will dump
    to preset file location(s) in the app config dir, and will attempt to
    log and clear the results after dumping. If that should fail (due to
    a hung app, etc.), then the results will be logged and cleared on the
    next app run.

    Do not use this call during regular smooth operation of the app; it
    is should only be used for debugging or in response to confirmed
    problems as it can leak file descriptors, cause hitches, etc.
    """
    # pylint: disable=consider-using-with
    import faulthandler

    # Dump our metadata immediately. If a delay is passed, it generally
    # means we expect things to hang momentarily, so we should not delay
    # writing our metadata or it will likely not happen. Though we
    # should remember that metadata doesn't line up perfectly in time with
    # the dump in that case.
    try:
        mdpath = os.path.join(
            os.path.dirname(_babase.app.env.config_file_path),
            '_appstate_dump_md',
        )
        with open(mdpath, 'w', encoding='utf-8') as outfile:
            outfile.write(
                dataclass_to_json(
                    DumpedAppStateMetadata(
                        reason=reason,
                        app_time=_babase.apptime(),
                        log_level=log_level,
                    )
                )
            )
    except Exception:
        # Abandon whole dump if we can't write metadata.
        balog.exception('Error writing app state dump metadata.')
        return

    tbpath = os.path.join(
        os.path.dirname(_babase.app.env.config_file_path), '_appstate_dump_tb'
    )

    tbfile = open(tbpath, 'w', encoding='utf-8')

    # faulthandler needs the raw file descriptor to still be valid when
    # it fires, so stuff this into a global var to make sure it doesn't get
    # cleaned up.
    _tb_held_files.append(tbfile)

    if delay > 0.0:
        faulthandler.dump_traceback_later(delay, file=tbfile)
    else:
        faulthandler.dump_traceback(file=tbfile)

    # Attempt to log shortly after dumping.
    # Allow sufficient time since we don't know how long the dump takes.
    # We want this to work from any thread, so need to kick this part
    # over to the logic thread so timer works.
    _babase.pushcall(
        partial(_babase.apptimer, delay + 1.0, log_dumped_app_state),
        from_other_thread=True,
        suppress_other_thread_warning=True,
    )


def log_dumped_app_state(from_previous_run: bool = False) -> None:
    """If an app-state dump exists, log it and clear it. No-op otherwise."""

    try:
        out = ''
        mdpath = os.path.join(
            os.path.dirname(_babase.app.env.config_file_path),
            '_appstate_dump_md',
        )
        if os.path.exists(mdpath):
            # We may be hanging on to open file descriptors for use by
            # faulthandler (see above). If we are, we need to clear them
            # now or else we'll get 'file in use' errors below when we
            # try to unlink it on windows.
            for heldfile in _tb_held_files:
                heldfile.close()
            _tb_held_files.clear()

            with open(mdpath, 'r', encoding='utf-8') as infile:
                appstatedata = infile.read()

            # Kill the file first in case we can't parse the data; don't
            # want to get stuck doing this repeatedly.
            os.unlink(mdpath)

            metadata = dataclass_from_json(DumpedAppStateMetadata, appstatedata)

            header = (
                'Found app state dump from previous app run'
                if from_previous_run
                else 'App state dump'
            )
            out += (
                f'{header}:\nReason: {metadata.reason}\n'
                f'Time: {metadata.app_time:.2f}'
            )
            tbpath = os.path.join(
                os.path.dirname(_babase.app.env.config_file_path),
                '_appstate_dump_tb',
            )
            if os.path.exists(tbpath):
                with open(tbpath, 'r', encoding='utf-8') as infile:
                    out += '\nPython tracebacks:\n' + infile.read()
                os.unlink(tbpath)
            balog.log(metadata.log_level.python_logging_level, out)
    except Exception:
        balog.exception('Error logging dumped app state.')


class AppHealthSubsystem(AppSubsystem):
    """Subsystem for monitoring app health; logs not-responding issues, etc.

    The single shared instance of this class can be found on the
    :attr:`~babase.App.health` attr on the :class:`~babase.App`
    class.
    """

    def __init__(self) -> None:
        assert _babase.in_logic_thread()
        super().__init__()
        self._running = True
        self._response = False
        self._first_check = True

        self.stop_event = threading.Event()
        self.stopped_event = threading.Event()

        self._thread = threading.Thread(target=self._app_monitor_thread_main)
        self._thread.start()

        # Kill our thread as part of app shutdown.
        _babase.app.add_shutdown_task(self._shutdown())

    async def _shutdown(self) -> None:
        self.stop_event.set()
        while not self.stopped_event.is_set():
            await asyncio.sleep(0.05)

    @override
    def on_app_loading(self) -> None:
        """:meta private:"""
        # If any traceback dumps happened last run, log and clear them.
        log_dumped_app_state(from_previous_run=True)

    @override
    def on_app_suspend(self) -> None:
        """:meta private:"""
        assert _babase.in_logic_thread()
        self._running = False

    @override
    def on_app_unsuspend(self) -> None:
        """:meta private:"""
        assert _babase.in_logic_thread()
        self._running = True

    def _app_monitor_thread_main(self) -> None:
        _babase.set_thread_name('ballistica app-monitor')
        try:
            self._monitor_app()
        except Exception:
            balog.exception('Error in AppHealthSubsystem thread.')

    def _set_response(self) -> None:
        assert _babase.in_logic_thread()
        self._response = True

    def _check_running(self) -> bool:
        # Workaround for the fact that mypy assumes _running
        # doesn't change during the course of a function.
        return self._running

    def _monitor_app(self) -> None:

        while not self.stop_event.is_set():

            # # Always sleep a bit between checks.
            self.stop_event.wait(1.234)

            # Do nothing while backgrounded.
            while not self._running:
                self.stop_event.wait(2.3456)

            # Wait for the logic thread to run something we send it.
            starttime = time.monotonic()
            self._response = False
            _babase.pushcall(self._set_response, raw=True)
            while not self._response:
                # Abort this check if we went into the background.
                if not self._check_running():
                    break

                # Wait a bit longer the first time through since the app
                # could still be starting up; we generally don't want to
                # report that.
                threshold = 10 if self._first_check else 5

                # If we've been waiting too long (and the app is running)
                # dump the app state and bail. Make an exception for the
                # first check though since the app could just be taking
                # a while to get going; we don't want to report that.
                duration = time.monotonic() - starttime
                if duration > threshold:
                    dump_app_state(
                        reason=f'Logic thread unresponsive'
                        f' for {threshold} seconds.'
                    )

                    # We just do one alert for now.
                    return

                self.stop_event.wait(1.042)

            self._first_check = False

        self.stopped_event.set()
