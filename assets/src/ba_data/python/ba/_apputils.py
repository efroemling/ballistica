# Released under the MIT License. See LICENSE for details.
#
"""Utility functionality related to the overall operation of the app."""
from __future__ import annotations

import gc
import os
from typing import TYPE_CHECKING

import _ba

if TYPE_CHECKING:
    from typing import Any
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
