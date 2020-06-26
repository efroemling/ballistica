# Copyright (c) 2011-2020 Eric Froemling
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
"""Utility functionality related to the overall operation of the app."""
from __future__ import annotations

import os
from typing import TYPE_CHECKING

import _ba

if TYPE_CHECKING:
    from typing import List, Any, Callable, Optional
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
    from ba import _lang
    return _lang.Lstr(resource='remote_app.app_name')


def should_submit_debug_info() -> bool:
    """(internal)"""
    return _ba.app.config.get('Submit Debug Info', True)


def handle_log() -> None:
    """Called on debug log prints.

    When this happens, we can upload our log to the server
    after a short bit if desired.
    """
    from ba._netutils import master_server_post
    from ba._enums import TimeType
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
                'log': _ba.getlog(),
                'version': app.version,
                'build': app.build_number,
                'userAgentString': app.user_agent_string,
                'session': sessionname,
                'activity': activityname,
                'fatal': 0,
                'userRanCommands': _ba.has_user_run_commands(),
                'time': _ba.time(TimeType.REAL),
                'userModded': _ba.has_user_mods(),
                'newsShow': _ba.get_news_show(),
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
                handle_log()

        if not _ba.is_log_full():
            with _ba.Context('ui'):
                _ba.timer(600.0,
                          _reset,
                          timetype=TimeType.REAL,
                          suppress_format_warning=True)


def handle_leftover_log_file() -> None:
    """Handle an un-uploaded log from a previous run."""
    try:
        import json
        from ba._netutils import master_server_post

        if os.path.exists(_ba.get_log_file_path()):
            with open(_ba.get_log_file_path()) as infile:
                info = json.loads(infile.read())
            infile.close()
            do_send = should_submit_debug_info()
            if do_send:

                def response(data: Any) -> None:
                    # Non-None response means we were successful;
                    # lets kill it.
                    if data is not None:
                        try:
                            os.remove(_ba.get_log_file_path())
                        except FileNotFoundError:
                            # Saw this in the wild. The file just existed
                            # a moment ago but I suppose something could have
                            # killed it since. ¯\_(ツ)_/¯
                            pass

                master_server_post('bsLog', info, response)
            else:
                # If they don't want logs uploaded just kill it.
                os.remove(_ba.get_log_file_path())
    except Exception:
        from ba import _error
        _error.print_exception('Error handling leftover log file.')


def garbage_collect(session_end: bool = True) -> None:
    """Run an explicit pass of garbage collection."""
    import gc
    gc.collect()

    # Can be handy to print this to check for leaks between games.
    if bool(False):
        print('PY OBJ COUNT', len(gc.get_objects()))
    if gc.garbage:
        print('PYTHON GC FOUND', len(gc.garbage), 'UNCOLLECTIBLE OBJECTS:')
        for i, obj in enumerate(gc.garbage):
            print(str(i) + ':', obj)
    if session_end:
        print_live_object_warnings('after session shutdown')


def print_live_object_warnings(when: Any,
                               ignore_session: ba.Session = None,
                               ignore_activity: ba.Activity = None) -> None:
    """Print warnings for remaining objects in the current context."""
    # pylint: disable=cyclic-import
    import gc
    from ba._session import Session
    from ba._actor import Actor
    from ba._activity import Activity
    sessions: List[ba.Session] = []
    activities: List[ba.Activity] = []
    actors: List[ba.Actor] = []

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
    from ba._lang import get_resource
    from ba._general import Call
    from ba._enums import TimeType
    _ba.timer(
        2.0,
        lambda: _ba.screenmessage(get_resource('internal.corruptFileText').
                                  replace('${EMAIL}', 'support@froemling.net'),
                                  color=(1, 0, 0)),
        timetype=TimeType.REAL)
    _ba.timer(2.0,
              Call(_ba.playsound, _ba.getsound('error')),
              timetype=TimeType.REAL)


def show_ad(purpose: str,
            on_completion_call: Callable[[], Any] = None) -> None:
    """(internal)"""
    _ba.app.last_ad_purpose = purpose
    _ba.show_ad(purpose, on_completion_call)


def show_ad_2(purpose: str,
              on_completion_call: Callable[[bool], Any] = None) -> None:
    """(internal)"""
    _ba.app.last_ad_purpose = purpose
    _ba.show_ad_2(purpose, on_completion_call)


def call_after_ad(call: Callable[[], Any]) -> None:
    """Run a call after potentially showing an ad."""
    # pylint: disable=too-many-statements
    # pylint: disable=too-many-branches
    # pylint: disable=too-many-locals
    from ba._account import have_pro
    from ba._enums import TimeType
    import time
    app = _ba.app
    show = True

    # No ads without net-connections, etc.
    if not _ba.can_show_ad():
        show = False
    if have_pro():
        show = False  # Pro disables interstitials.
    try:
        session = _ba.get_foreground_host_session()
        assert session is not None
        is_tournament = session.tournament_id is not None
    except Exception:
        is_tournament = False
    if is_tournament:
        show = False  # Never show ads during tournaments.

    if show:
        interval: Optional[float]
        launch_count = app.config.get('launchCount', 0)

        # If we're seeing short ads we may want to space them differently.
        interval_mult = (_ba.get_account_misc_read_val(
            'ads.shortIntervalMult', 1.0) if app.last_ad_was_short else 1.0)
        if app.ad_amt is None:
            if launch_count <= 1:
                app.ad_amt = _ba.get_account_misc_read_val(
                    'ads.startVal1', 0.99)
            else:
                app.ad_amt = _ba.get_account_misc_read_val(
                    'ads.startVal2', 1.0)
            interval = None
        else:
            # So far we're cleared to show; now calc our ad-show-threshold and
            # see if we should *actually* show (we reach our threshold faster
            # the longer we've been playing).
            base = 'ads' if _ba.has_video_ads() else 'ads2'
            min_lc = _ba.get_account_misc_read_val(base + '.minLC', 0.0)
            max_lc = _ba.get_account_misc_read_val(base + '.maxLC', 5.0)
            min_lc_scale = (_ba.get_account_misc_read_val(
                base + '.minLCScale', 0.25))
            max_lc_scale = (_ba.get_account_misc_read_val(
                base + '.maxLCScale', 0.34))
            min_lc_interval = (_ba.get_account_misc_read_val(
                base + '.minLCInterval', 360))
            max_lc_interval = (_ba.get_account_misc_read_val(
                base + '.maxLCInterval', 300))
            if launch_count < min_lc:
                lc_amt = 0.0
            elif launch_count > max_lc:
                lc_amt = 1.0
            else:
                lc_amt = ((float(launch_count) - min_lc) / (max_lc - min_lc))
            incr = (1.0 - lc_amt) * min_lc_scale + lc_amt * max_lc_scale
            interval = ((1.0 - lc_amt) * min_lc_interval +
                        lc_amt * max_lc_interval)
            app.ad_amt += incr
        assert app.ad_amt is not None
        if app.ad_amt >= 1.0:
            app.ad_amt = app.ad_amt % 1.0
            app.attempted_first_ad = True

        # After we've reached the traditional show-threshold once,
        # try again whenever its been INTERVAL since our last successful show.
        elif (app.attempted_first_ad
              and (app.last_ad_completion_time is None or
                   (interval is not None
                    and _ba.time(TimeType.REAL) - app.last_ad_completion_time >
                    (interval * interval_mult)))):
            # Reset our other counter too in this case.
            app.ad_amt = 0.0
        else:
            show = False

    # If we're *still* cleared to show, actually tell the system to show.
    if show:
        # As a safety-check, set up an object that will run
        # the completion callback if we've returned and sat for 10 seconds
        # (in case some random ad network doesn't properly deliver its
        # completion callback).
        class _Payload:

            def __init__(self, pcall: Callable[[], Any]):
                self._call = pcall
                self._ran = False

            def run(self, fallback: bool = False) -> None:
                """Run the fallback call (and issues a warning about it)."""
                if not self._ran:
                    if fallback:
                        print((
                            'ERROR: relying on fallback ad-callback! '
                            'last network: ' + app.last_ad_network + ' (set ' +
                            str(int(time.time() -
                                    app.last_ad_network_set_time)) +
                            's ago); purpose=' + app.last_ad_purpose))
                    _ba.pushcall(self._call)
                    self._ran = True

        payload = _Payload(call)
        with _ba.Context('ui'):
            _ba.timer(5.0,
                      lambda: payload.run(fallback=True),
                      timetype=TimeType.REAL)
        show_ad('between_game', on_completion_call=payload.run)
    else:
        _ba.pushcall(call)  # Just run the callback without the ad.
