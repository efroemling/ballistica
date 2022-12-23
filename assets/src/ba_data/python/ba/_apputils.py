# Released under the MIT License. See LICENSE for details.
#
"""Utility functionality related to the overall operation of the app."""
from __future__ import annotations

import gc
import os
import logging
from threading import Thread
from dataclasses import dataclass
from typing import TYPE_CHECKING

from efro.log import LogLevel
from efro.dataclassio import ioprepped, dataclass_to_json, dataclass_from_json
import _ba

if TYPE_CHECKING:
    from typing import Any, TextIO
    import ba


def is_browser_likely_available() -> bool:
    """Return whether a browser likely exists on the current device.

    category: General Utility Functions

    If this returns False you may want to avoid calling ba.show_url()
    with any lengthy addresses. (ba.show_url() will display an address
    as a string in a window if unable to bring up a browser, but that
    is only useful for simple URLs.)
    """
    app = _ba.app
    platform = app.platform
    touchscreen = _ba.getinputdevice('TouchScreen', '#1', doraise=False)

    # If we're on a vr device or an android device with no touchscreen,
    # assume no browser.
    # FIXME: Might not be the case anymore; should make this definable
    #  at the platform level.
    if app.vr_mode or (platform == 'android' and touchscreen is None):
        return False

    # Anywhere else assume we've got one.
    return True


def get_remote_app_name() -> ba.Lstr:
    """(internal)"""
    from ba import _language

    return _language.Lstr(resource='remote_app.app_name')


def should_submit_debug_info() -> bool:
    """(internal)"""
    return _ba.app.config.get('Submit Debug Info', True)


def handle_v1_cloud_log() -> None:
    """Called on debug log prints.

    When this happens, we can upload our log to the server
    after a short bit if desired.
    """
    from ba._net import master_server_post
    from ba._generated.enums import TimeType
    from ba._internal import get_news_show

    app = _ba.app
    app.log_have_new = True
    if not app.log_upload_timer_started:

        def _put_log() -> None:
            try:
                sessionname = str(_ba.get_foreground_host_session())
            except Exception:
                sessionname = 'unavailable'
            try:
                activityname = str(_ba.get_foreground_host_activity())
            except Exception:
                activityname = 'unavailable'

            info = {
                'log': _ba.get_v1_cloud_log(),
                'version': app.version,
                'build': app.build_number,
                'userAgentString': app.user_agent_string,
                'session': sessionname,
                'activity': activityname,
                'fatal': 0,
                'userRanCommands': _ba.has_user_run_commands(),
                'time': _ba.time(TimeType.REAL),
                'userModded': _ba.workspaces_in_use(),
                'newsShow': get_news_show(),
            }

            def response(data: Any) -> None:
                # A non-None response means success; lets
                # take note that we don't need to report further
                # log info this run
                if data is not None:
                    app.log_have_new = False
                    _ba.mark_log_sent()

            master_server_post('bsLog', info, response)

        app.log_upload_timer_started = True

        # Delay our log upload slightly in case other
        # pertinent info gets printed between now and then.
        with _ba.Context('ui'):
            _ba.timer(3.0, _put_log, timetype=TimeType.REAL)

        # After a while, allow another log-put.
        def _reset() -> None:
            app.log_upload_timer_started = False
            if app.log_have_new:
                handle_v1_cloud_log()

        if not _ba.is_log_full():
            with _ba.Context('ui'):
                _ba.timer(
                    600.0,
                    _reset,
                    timetype=TimeType.REAL,
                    suppress_format_warning=True,
                )


def handle_leftover_v1_cloud_log_file() -> None:
    """Handle an un-uploaded v1-cloud-log from a previous run."""
    try:
        import json
        from ba._net import master_server_post

        if os.path.exists(_ba.get_v1_cloud_log_file_path()):
            with open(
                _ba.get_v1_cloud_log_file_path(), encoding='utf-8'
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
                            os.remove(_ba.get_v1_cloud_log_file_path())
                        except FileNotFoundError:
                            # Saw this in the wild. The file just existed
                            # a moment ago but I suppose something could have
                            # killed it since. ¯\_(ツ)_/¯
                            pass

                master_server_post('bsLog', info, response)
            else:
                # If they don't want logs uploaded just kill it.
                os.remove(_ba.get_v1_cloud_log_file_path())
    except Exception:
        from ba import _error

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
    if bool(False):
        print_live_object_warnings('after session shutdown')


def garbage_collect() -> None:
    """Run an explicit pass of garbage collection.

    category: General Utility Functions

    May also print warnings/etc. if collection takes too long or if
    uncollectible objects are found (so use this instead of simply
    gc.collect().
    """
    gc.collect()


def print_live_object_warnings(
    when: Any,
    ignore_session: ba.Session | None = None,
    ignore_activity: ba.Activity | None = None,
) -> None:
    """Print warnings for remaining objects in the current context.

    IMPORTANT - don't call this in production; usage of gc.get_objects()
    can bork Python. See notes at top of efro.debug module.
    """
    # pylint: disable=cyclic-import
    from ba._session import Session
    from ba._actor import Actor
    from ba._activity import Activity

    sessions: list[ba.Session] = []
    activities: list[ba.Activity] = []
    actors: list[ba.Actor] = []

    # Once we come across leaked stuff, printing again is probably
    # redundant.
    if _ba.app.printed_live_object_warning:
        return
    for obj in gc.get_objects():
        if isinstance(obj, Actor):
            actors.append(obj)
        elif isinstance(obj, Session):
            sessions.append(obj)
        elif isinstance(obj, Activity):
            activities.append(obj)

    # Complain about any remaining sessions.
    for session in sessions:
        if session is ignore_session:
            continue
        _ba.app.printed_live_object_warning = True
        print(f'ERROR: Session found {when}: {session}')

    # Complain about any remaining activities.
    for activity in activities:
        if activity is ignore_activity:
            continue
        _ba.app.printed_live_object_warning = True
        print(f'ERROR: Activity found {when}: {activity}')

    # Complain about any remaining actors.
    for actor in actors:
        _ba.app.printed_live_object_warning = True
        print(f'ERROR: Actor found {when}: {actor}')


def print_corrupt_file_error() -> None:
    """Print an error if a corrupt file is found."""
    from ba._general import Call
    from ba._generated.enums import TimeType

    _ba.timer(
        2.0,
        lambda: _ba.screenmessage(
            _ba.app.lang.get_resource('internal.corruptFileText').replace(
                '${EMAIL}', 'support@froemling.net'
            ),
            color=(1, 0, 0),
        ),
        timetype=TimeType.REAL,
    )
    _ba.timer(
        2.0, Call(_ba.playsound, _ba.getsound('error')), timetype=TimeType.REAL
    )


_tbfiles: list[TextIO] = []


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
    from ba._generated.enums import TimeType

    # Dump our metadata immediately. If a delay is passed, it generally
    # means we expect things to hang momentarily, so we should not delay
    # writing our metadata or it will likely not happen. Though we
    # should remember that metadata doesn't line up perfectly in time with
    # the dump in that case.
    try:
        mdpath = os.path.join(
            os.path.dirname(_ba.app.config_file_path), '_appstate_dump_md'
        )
        with open(mdpath, 'w', encoding='utf-8') as outfile:
            outfile.write(
                dataclass_to_json(
                    DumpedAppStateMetadata(
                        reason=reason,
                        app_time=_ba.time(TimeType.REAL),
                        log_level=log_level,
                    )
                )
            )
    except Exception:
        # Abandon whole dump if we can't write metadata.
        logging.exception('Error writing app state dump metadata.')
        return

    tbpath = os.path.join(
        os.path.dirname(_ba.app.config_file_path), '_appstate_dump_tb'
    )

    # faulthandler needs the raw file descriptor to still be valid when
    # it fires, so stuff this into a global var to make sure it doesn't get
    # cleaned up.
    tbfile = open(tbpath, 'w', encoding='utf-8')
    _tbfiles.append(tbfile)

    if delay > 0.0:
        faulthandler.dump_traceback_later(delay, file=tbfile)
    else:
        faulthandler.dump_traceback(file=tbfile)

    # Attempt to log shortly after dumping.
    # Allow sufficient time since we don't know how long the dump takes.
    # We want this to work from any thread, so need to kick this part
    # over to the logic thread so timer works.
    _ba.pushcall(
        lambda: _ba.timer(
            delay + 1.0, log_dumped_app_state, timetype=TimeType.REAL
        ),
        from_other_thread=True,
        suppress_other_thread_warning=True,
    )


def log_dumped_app_state() -> None:
    """If an app-state dump exists, log it and clear it. No-op otherwise."""

    try:
        out = ''
        mdpath = os.path.join(
            os.path.dirname(_ba.app.config_file_path), '_appstate_dump_md'
        )
        if os.path.exists(mdpath):
            with open(mdpath, 'r', encoding='utf-8') as infile:
                metadata = dataclass_from_json(
                    DumpedAppStateMetadata, infile.read()
                )
            os.unlink(mdpath)
            out += (
                f'App state dump:\nReason: {metadata.reason}\n'
                f'Time: {metadata.app_time:.2f}'
            )
            tbpath = os.path.join(
                os.path.dirname(_ba.app.config_file_path), '_appstate_dump_tb'
            )
            if os.path.exists(tbpath):
                with open(tbpath, 'r', encoding='utf-8') as infile:
                    out += '\nPython tracebacks:\n' + infile.read()
                os.unlink(tbpath)
            logging.log(metadata.log_level.python_logging_level, out)
    except Exception:
        logging.exception('Error logging dumped app state.')


class AppHealthMonitor:
    """Logs things like app-not-responding issues."""

    def __init__(self) -> None:
        assert _ba.in_logic_thread()
        self._running = True
        self._thread = Thread(target=self._app_monitor_thread_main, daemon=True)
        self._thread.start()
        self._response = False
        self._first_check = True

    def _app_monitor_thread_main(self) -> None:

        try:
            self._monitor_app()
        except Exception:
            logging.exception('Error in AppHealthMonitor thread.')

    def _set_response(self) -> None:
        assert _ba.in_logic_thread()
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
            _ba.pushcall(self._set_response, raw=True)
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

    def on_app_pause(self) -> None:
        """Should be called when the app pauses."""
        assert _ba.in_logic_thread()
        self._running = False

    def on_app_resume(self) -> None:
        """Should be called when the app resumes."""
        assert _ba.in_logic_thread()
        self._running = True


def on_too_many_file_descriptors() -> None:
    """Called when too many file descriptors are open; trying to debug."""
    from ba._generated.enums import TimeType

    real_time = _ba.time(TimeType.REAL)

    def _do_log() -> None:
        import subprocess

        pid = os.getpid()
        out = f'TOO MANY FDS at {real_time}.\nWe are pid {pid}\n'

        out += (
            'FD Count: '
            + subprocess.run(
                f'ls -l /proc/{pid}/fd | wc -l',
                shell=True,
                check=False,
                capture_output=True,
            ).stdout.decode()
            + '\n'
        )

        out += (
            'lsof output:\n'
            + subprocess.run(
                f'lsof -p {pid}',
                shell=True,
                check=False,
                capture_output=True,
            ).stdout.decode()
            + '\n'
        )

        logging.warning(out)

    Thread(target=_do_log, daemon=True).start()

    # import io
    # from efro.debug import printtypes

    # with io.StringIO() as fstr:
    #     fstr.write('Too many FDs.\n')
    #     printtypes(file=fstr)
    #     fstr.seek(0)
    #     logging.warning(fstr.read())
    # import socket

    # objs: list[Any] = []
    # for obj in gc.get_objects():
    #     if isinstance(obj, socket.socket):
    #         objs.append(obj)
    # test = open('/Users/ericf/.zshrc', 'r', encoding='utf-8')
    # reveal_type(test)
    # print('FOUND', len(objs))
