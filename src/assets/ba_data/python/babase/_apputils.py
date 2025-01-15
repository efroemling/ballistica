# Released under the MIT License. See LICENSE for details.
#
"""Utility functionality related to the overall operation of the app."""
from __future__ import annotations

import gc
import os
import logging
from threading import Thread
from functools import partial
from dataclasses import dataclass
from typing import TYPE_CHECKING, override

from efro.util import utc_now
from efro.logging import LogLevel
from efro.dataclassio import ioprepped, dataclass_to_json, dataclass_from_json

import _babase
from babase._appsubsystem import AppSubsystem

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

    category: General Utility Functions

    If this returns False you may want to avoid calling babase.open_url()
    with any lengthy addresses. (babase.open_url() will display an address
    as a string in a window if unable to bring up a browser, but that
    is only useful for simple URLs.)
    """
    app = _babase.app

    if app.classic is None:
        logging.warning(
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


def get_remote_app_name() -> babase.Lstr:
    """(internal)"""
    from babase import _language

    return _language.Lstr(resource='remote_app.app_name')


def should_submit_debug_info() -> bool:
    """(internal)"""
    val = _babase.app.config.get('Submit Debug Info', True)
    assert isinstance(val, bool)
    return val


def handle_v1_cloud_log() -> None:
    """Called when new messages have been added to v1-cloud-log.

    When this happens, we can upload our log to the server after a short
    bit if desired.
    """

    app = _babase.app
    classic = app.classic
    plus = app.plus

    if classic is None or plus is None:
        if _babase.do_once():
            logging.warning(
                'handle_v1_cloud_log should not be getting called'
                ' without classic and plus present.'
            )
        return

    classic.log_have_new = True
    if not classic.log_upload_timer_started:

        def _put_log() -> None:
            assert plus is not None
            assert classic is not None
            try:
                sessionname = str(classic.get_foreground_host_session())
            except Exception:
                sessionname = 'unavailable'
            try:
                activityname = str(classic.get_foreground_host_activity())
            except Exception:
                activityname = 'unavailable'

            info = {
                'log': _babase.get_v1_cloud_log(),
                'version': app.env.engine_version,
                'build': app.env.engine_build_number,
                'userAgentString': classic.legacy_user_agent_string,
                'session': sessionname,
                'activity': activityname,
                'fatal': 0,
                'userRanCommands': _babase.has_user_run_commands(),
                'time': _babase.apptime(),
                'userModded': _babase.workspaces_in_use(),
                'newsShow': plus.get_classic_news_show(),
            }

            def response(data: Any) -> None:
                assert classic is not None
                # A non-None response means success; lets
                # take note that we don't need to report further
                # log info this run
                if data is not None:
                    classic.log_have_new = False
                    _babase.mark_log_sent()

            classic.master_server_v1_post('bsLog', info, response)

        classic.log_upload_timer_started = True

        # Delay our log upload slightly in case other
        # pertinent info gets printed between now and then.
        with _babase.ContextRef.empty():
            _babase.apptimer(3.0, _put_log)

        # After a while, allow another log-put.
        def _reset() -> None:
            assert classic is not None
            classic.log_upload_timer_started = False
            if classic.log_have_new:
                handle_v1_cloud_log()

        if not _babase.is_log_full():
            with _babase.ContextRef.empty():
                _babase.apptimer(600.0, _reset)


def handle_leftover_v1_cloud_log_file() -> None:
    """Handle an un-uploaded v1-cloud-log from a previous run."""

    # Only applies with classic present.
    if _babase.app.classic is None:
        return
    try:
        import json

        if os.path.exists(_babase.get_v1_cloud_log_file_path()):
            with open(
                _babase.get_v1_cloud_log_file_path(), encoding='utf-8'
            ) as infile:
                info = json.loads(infile.read())
            infile.close()
            do_send = should_submit_debug_info()
            if do_send:

                def response(data: Any) -> None:
                    # Non-None response means we were successful;
                    # lets kill it.
                    if data is not None:
                        try:
                            os.remove(_babase.get_v1_cloud_log_file_path())
                        except FileNotFoundError:
                            # Saw this in the wild. The file just existed
                            # a moment ago but I suppose something could have
                            # killed it since. ¯\_(ツ)_/¯
                            pass

                _babase.app.classic.master_server_v1_post(
                    'bsLog', info, response
                )
            else:
                # If they don't want logs uploaded just kill it.
                os.remove(_babase.get_v1_cloud_log_file_path())
    except Exception:
        from babase import _error

        _error.print_exception('Error handling leftover log file.')


def garbage_collect_session_end() -> None:
    """Run explicit garbage collection with extra checks for session end."""
    gc.collect()

    # Can be handy to print this to check for leaks between games.
    if bool(False):
        print('PY OBJ COUNT', len(gc.get_objects()))
    if gc.garbage:
        print('PYTHON GC FOUND', len(gc.garbage), 'UNCOLLECTIBLE OBJECTS:')
        for i, obj in enumerate(gc.garbage):
            print(str(i) + ':', obj)

    # NOTE: no longer running these checks. Perhaps we can allow
    # running them with an explicit flag passed, but we should never
    # run them by default because gc.get_objects() can mess up the app.
    # See notes at top of efro.debug.
    # if bool(False):
    #     print_live_object_warnings('after session shutdown')


def garbage_collect() -> None:
    """Run an explicit pass of garbage collection.

    category: General Utility Functions

    May also print warnings/etc. if collection takes too long or if
    uncollectible objects are found (so use this instead of simply
    gc.collect().
    """
    gc.collect()


def print_corrupt_file_error() -> None:
    """Print an error if a corrupt file is found."""

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
        _babase.apptimer(2.0, _babase.getsimplesound('error').play)


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
        logging.exception('Error writing app state dump metadata.')
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
            logging.log(metadata.log_level.python_logging_level, out)
    except Exception:
        logging.exception('Error logging dumped app state.')


class AppHealthMonitor(AppSubsystem):
    """Logs things like app-not-responding issues."""

    def __init__(self) -> None:
        assert _babase.in_logic_thread()
        super().__init__()
        self._running = True
        self._thread = Thread(target=self._app_monitor_thread_main, daemon=True)
        self._thread.start()
        self._response = False
        self._first_check = True

    @override
    def on_app_loading(self) -> None:
        # If any traceback dumps happened last run, log and clear them.
        log_dumped_app_state(from_previous_run=True)

    def _app_monitor_thread_main(self) -> None:
        _babase.set_thread_name('ballistica app-monitor')
        try:
            self._monitor_app()
        except Exception:
            logging.exception('Error in AppHealthMonitor thread.')

    def _set_response(self) -> None:
        assert _babase.in_logic_thread()
        self._response = True

    def _check_running(self) -> bool:
        # Workaround for the fact that mypy assumes _running
        # doesn't change during the course of a function.
        return self._running

    def _monitor_app(self) -> None:
        import time

        while bool(True):
            # Always sleep a bit between checks.
            time.sleep(1.234)

            # Do nothing while backgrounded.
            while not self._running:
                time.sleep(2.3456)

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

                time.sleep(1.042)

            self._first_check = False

    @override
    def on_app_suspend(self) -> None:
        assert _babase.in_logic_thread()
        self._running = False

    @override
    def on_app_unsuspend(self) -> None:
        assert _babase.in_logic_thread()
        self._running = True
