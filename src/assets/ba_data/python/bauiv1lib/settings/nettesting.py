# Released under the MIT License. See LICENSE for details.
#
"""Provides ui for network related testing."""

from __future__ import annotations

import time
import copy
import weakref
from threading import Thread
from typing import TYPE_CHECKING, override

from efro.error import CleanError
from bauiv1lib.settings.testing import TestingWindow
import bauiv1 as bui

if TYPE_CHECKING:
    from typing import Callable, Any

# We generally want all net tests to timeout on their own, but we add
# sort of sane max in case they don't.
MAX_TEST_SECONDS = 60 * 2


class NetTestingWindow(bui.MainWindow):
    """Window that runs a networking test suite to help diagnose issues."""

    def __init__(
        self,
        transition: str | None = 'in_right',
        origin_widget: bui.Widget | None = None,
    ):
        uiscale = bui.app.ui_v1.uiscale
        self._width = 820
        self._height = 500 if uiscale is bui.UIScale.SMALL else 500
        yoffs = -50 if uiscale is bui.UIScale.SMALL else 0

        self._printed_lines: list[str] = []
        assert bui.app.classic is not None
        super().__init__(
            root_widget=bui.containerwidget(
                size=(self._width, self._height),
                scale=(
                    1.75
                    if uiscale is bui.UIScale.SMALL
                    else 1.2 if uiscale is bui.UIScale.MEDIUM else 0.8
                ),
                stack_offset=(0, -4 if uiscale is bui.UIScale.SMALL else 0.0),
                toolbar_visibility=(
                    'menu_minimal'
                    if uiscale is bui.UIScale.SMALL
                    else 'menu_full'
                ),
            ),
            transition=transition,
            origin_widget=origin_widget,
        )
        self._done_button: bui.Widget | None
        if uiscale is bui.UIScale.SMALL:
            bui.containerwidget(
                edit=self._root_widget, on_cancel_call=self.main_window_back
            )
            self._done_button = None
        else:
            self._done_button = bui.buttonwidget(
                parent=self._root_widget,
                position=(46, self._height - 77 + yoffs),
                size=(60, 60),
                scale=0.9,
                label=bui.charstr(bui.SpecialChar.BACK),
                button_type='backSmall',
                autoselect=True,
                on_activate_call=self.main_window_back,
            )
            bui.containerwidget(
                edit=self._root_widget, cancel_button=self._done_button
            )

        # Avoid squads button on small mode.
        xinset = -50 if uiscale is bui.UIScale.SMALL else 0

        self._copy_button = bui.buttonwidget(
            parent=self._root_widget,
            position=(self._width - 200 + xinset, self._height - 77 + yoffs),
            size=(100, 60),
            scale=0.8,
            autoselect=True,
            label=bui.Lstr(resource='copyText'),
            on_activate_call=self._copy,
        )

        self._settings_button = bui.buttonwidget(
            parent=self._root_widget,
            position=(self._width - 100 + xinset, self._height - 77 + yoffs),
            size=(60, 60),
            scale=0.8,
            autoselect=True,
            label=bui.Lstr(value='...'),
            on_activate_call=self._show_val_testing,
        )

        twidth = self._width - 540
        bui.textwidget(
            parent=self._root_widget,
            position=(self._width * 0.5, self._height - 55 + yoffs),
            size=(0, 0),
            text=bui.Lstr(resource='settingsWindowAdvanced.netTestingText'),
            color=(0.8, 0.8, 0.8, 1.0),
            h_align='center',
            v_align='center',
            maxwidth=twidth,
        )

        self._scroll = bui.scrollwidget(
            parent=self._root_widget,
            position=(
                50,
                (140 if uiscale is bui.UIScale.SMALL else 50) + yoffs,
            ),
            size=(
                self._width - 100,
                self._height - (220 if uiscale is bui.UIScale.SMALL else 140),
            ),
            capture_arrows=True,
            autoselect=True,
        )
        self._rows = bui.columnwidget(parent=self._scroll)

        # Now kick off the tests.
        # Pass a weak-ref to this window so we don't keep it alive
        # if we back out before it completes. Also set is as daemon
        # so it doesn't keep the app running if the user is trying to quit.
        Thread(
            daemon=True,
            target=bui.Call(_run_diagnostics, weakref.ref(self)),
        ).start()

    @override
    def get_main_window_state(self) -> bui.MainWindowState:
        # Support recreating our window for back/refresh purposes.
        cls = type(self)
        return bui.BasicMainWindowState(
            create_call=lambda transition, origin_widget: cls(
                transition=transition, origin_widget=origin_widget
            )
        )

    def print(self, text: str, color: tuple[float, float, float]) -> None:
        """Print text to our console thingie."""
        for line in text.splitlines():
            txt = bui.textwidget(
                parent=self._rows,
                color=color,
                text=line,
                scale=0.75,
                flatness=1.0,
                shadow=0.0,
                size=(0, 20),
            )
            bui.containerwidget(edit=self._rows, visible_child=txt)
            self._printed_lines.append(line)

    def _copy(self) -> None:
        if not bui.clipboard_is_supported():
            bui.screenmessage(
                'Clipboard not supported on this platform.', color=(1, 0, 0)
            )
            return
        bui.clipboard_set_text('\n'.join(self._printed_lines))
        bui.screenmessage(f'{len(self._printed_lines)} lines copied.')

    def _show_val_testing(self) -> None:
        assert bui.app.classic is not None

        # no-op if we're not in control.
        if not self.main_window_has_control():
            return

        self.main_window_replace(get_net_val_testing_window())


def _run_diagnostics(weakwin: weakref.ref[NetTestingWindow]) -> None:
    # pylint: disable=too-many-statements
    # pylint: disable=too-many-branches

    from efro.util import utc_now

    have_error = [False]

    # We're running in a background thread but UI stuff needs to run
    # in the logic thread; give ourself a way to pass stuff to it.
    def _print(
        text: str, color: tuple[float, float, float] | None = None
    ) -> None:
        def _print_in_logic_thread() -> None:
            win = weakwin()
            if win is not None:
                win.print(text, (1.0, 1.0, 1.0) if color is None else color)

        bui.pushcall(_print_in_logic_thread, from_other_thread=True)

    def _print_test_results(call: Callable[[], Any]) -> bool:
        """Run the provided call, print result, & return success."""
        starttime = time.monotonic()
        try:
            call()
            duration = time.monotonic() - starttime
            _print(f'Succeeded in {duration:.2f}s.', color=(0, 1, 0))
            return True
        except Exception as exc:
            import traceback

            duration = time.monotonic() - starttime
            msg = (
                str(exc)
                if isinstance(exc, CleanError)
                else traceback.format_exc()
            )
            _print(msg, color=(1.0, 1.0, 0.3))
            _print(f'Failed in {duration:.2f}s.', color=(1, 0, 0))
            have_error[0] = True
            return False

    try:
        plus = bui.app.plus
        assert plus is not None

        assert bui.app.classic is not None

        _print(
            f'Running network diagnostics...\n'
            f'ua: {bui.app.classic.legacy_user_agent_string}\n'
            f'time: {utc_now()}.'
        )

        if bool(False):
            _print('\nRunning dummy success test...')
            _print_test_results(_dummy_success)

            _print('\nRunning dummy fail test...')
            _print_test_results(_dummy_fail)

        # V1 ping
        baseaddr = plus.get_master_server_address(source=0, version=1)
        _print(f'\nContacting V1 master-server src0 ({baseaddr})...')
        v1worked = _print_test_results(lambda: _test_fetch(baseaddr))

        # V1 alternate ping (only if primary fails since this often fails).
        if v1worked:
            _print('\nSkipping V1 master-server src1 test since src0 worked.')
        else:
            baseaddr = plus.get_master_server_address(source=1, version=1)
            _print(f'\nContacting V1 master-server src1 ({baseaddr})...')
            _print_test_results(lambda: _test_fetch(baseaddr))

        if 'none succeeded' in bui.app.net.v1_test_log:
            _print(
                f'\nV1-test-log failed: {bui.app.net.v1_test_log}',
                color=(1, 0, 0),
            )
            have_error[0] = True
        else:
            _print(f'\nV1-test-log ok: {bui.app.net.v1_test_log}')

        for srcid, result in sorted(bui.app.net.v1_ctest_results.items()):
            _print(f'\nV1 src{srcid} result: {result}')

        curv1addr = plus.get_master_server_address(version=1)
        _print(f'\nUsing V1 address: {curv1addr}')

        if plus.get_v1_account_state() == 'signed_in':
            _print('\nRunning V1 transaction...')
            _print_test_results(_test_v1_transaction)
        else:
            _print('\nSkipping V1 transaction (Not signed into V1).')

        # V2 ping
        baseaddr = plus.get_master_server_address(version=2)
        _print(f'\nContacting V2 master-server ({baseaddr})...')
        _print_test_results(lambda: _test_fetch(baseaddr))

        _print('\nComparing local time to V2 server...')
        _print_test_results(_test_v2_time)

        # Get V2 nearby zone
        with bui.app.net.zone_pings_lock:
            zone_pings = copy.deepcopy(bui.app.net.zone_pings)
        nearest_zone = (
            None
            if not zone_pings
            else sorted(zone_pings.items(), key=lambda i: i[1])[0]
        )

        if nearest_zone is not None:
            nearstr = f'{nearest_zone[0]}: {nearest_zone[1]:.0f}ms'
        else:
            nearstr = '-'
        _print(f'\nChecking nearest V2 zone ping ({nearstr})...')
        _print_test_results(lambda: _test_nearby_zone_ping(nearest_zone))

        _print('\nSending V2 cloud message...')
        _print_test_results(_test_v2_cloud_message)

        if have_error[0]:
            _print(
                '\nDiagnostics complete. Some diagnostics failed.',
                color=(10, 0, 0),
            )
        else:
            _print(
                '\nDiagnostics complete. Everything looks good!',
                color=(0, 1, 0),
            )
    except Exception:
        import traceback

        _print(
            f'An unexpected error occurred during testing;'
            f' please report this.\n'
            f'{traceback.format_exc()}',
            color=(1, 0, 0),
        )


def _dummy_success() -> None:
    """Dummy success test."""
    time.sleep(1.2)


def _dummy_fail() -> None:
    """Dummy fail test case."""
    raise RuntimeError('fail-test')


def _test_v1_transaction() -> None:
    """Dummy fail test case."""
    plus = bui.app.plus
    assert plus is not None

    if plus.get_v1_account_state() != 'signed_in':
        raise RuntimeError('Not signed in.')

    starttime = time.monotonic()

    # Gets set to True on success or string on error.
    results: list[Any] = [False]

    def _cb(cbresults: Any) -> None:
        # Simply set results here; our other thread acts on them.
        if not isinstance(cbresults, dict) or 'party_code' not in cbresults:
            results[0] = 'Unexpected transaction response'
            return
        results[0] = True  # Success!

    def _do_it() -> None:
        assert plus is not None
        # Fire off a transaction with a callback.
        plus.add_v1_account_transaction(
            {
                'type': 'PRIVATE_PARTY_QUERY',
                'expire_time': time.time() + 20,
            },
            callback=_cb,
        )
        plus.run_v1_account_transactions()

    bui.pushcall(_do_it, from_other_thread=True)

    while results[0] is False:
        time.sleep(0.01)
        if time.monotonic() - starttime > MAX_TEST_SECONDS:
            raise RuntimeError(
                f'test timed out after {MAX_TEST_SECONDS} seconds'
            )

    # If we got left a string, its an error.
    if isinstance(results[0], str):
        raise RuntimeError(results[0])


def _test_v2_cloud_message() -> None:
    from dataclasses import dataclass
    import bacommon.cloud

    @dataclass
    class _Results:
        errstr: str | None = None
        send_time: float | None = None
        response_time: float | None = None

    results = _Results()

    def _cb(response: bacommon.cloud.PingResponse | Exception) -> None:
        # Note: this runs in another thread so need to avoid exceptions.
        results.response_time = time.monotonic()
        if isinstance(response, Exception):
            results.errstr = str(response)
        if not isinstance(response, bacommon.cloud.PingResponse):
            results.errstr = f'invalid response type: {type(response)}.'

    def _send() -> None:
        # Note: this runs in another thread so need to avoid exceptions.
        results.send_time = time.monotonic()
        assert bui.app.plus is not None
        bui.app.plus.cloud.send_message_cb(bacommon.cloud.PingMessage(), _cb)

    # This stuff expects to be run from the logic thread.
    bui.pushcall(_send, from_other_thread=True)

    wait_start_time = time.monotonic()
    while True:
        if results.response_time is not None:
            break
        time.sleep(0.01)
        if time.monotonic() - wait_start_time > MAX_TEST_SECONDS:
            raise RuntimeError(
                f'Timeout ({MAX_TEST_SECONDS} seconds)'
                f' waiting for cloud message response'
            )
    if results.errstr is not None:
        raise RuntimeError(results.errstr)


def _test_v2_time() -> None:
    offset = bui.app.net.server_time_offset_hours
    if offset is None:
        raise RuntimeError(
            'no time offset found;'
            ' perhaps unable to communicate with v2 server?'
        )
    if abs(offset) >= 2.0:
        raise CleanError(
            f'Your device time is off from world time by {offset:.1f} hours.\n'
            'This may cause network operations to fail due to your device\n'
            ' incorrectly treating SSL certificates as not-yet-valid, etc.\n'
            'Check your device time and time-zone settings to fix this.\n'
        )


def _test_fetch(baseaddr: str) -> None:
    # pylint: disable=consider-using-with
    import urllib.request

    assert bui.app.classic is not None
    response = urllib.request.urlopen(
        urllib.request.Request(
            f'{baseaddr}/ping',
            None,
            {'User-Agent': bui.app.classic.legacy_user_agent_string},
        ),
        context=bui.app.net.sslcontext,
        timeout=MAX_TEST_SECONDS,
    )
    if response.getcode() != 200:
        raise RuntimeError(
            f'Got unexpected response code {response.getcode()}.'
        )
    data = response.read()
    if data != b'pong':
        raise RuntimeError('Got unexpected response data.')


def _test_nearby_zone_ping(nearest_zone: tuple[str, float] | None) -> None:
    """Try to ping nearest v2 zone."""
    if nearest_zone is None:
        raise RuntimeError('No nearest zone.')
    if nearest_zone[1] > 500:
        raise RuntimeError('Ping too high.')


def get_net_val_testing_window() -> TestingWindow:
    """Create a window for testing net values."""
    entries = [
        {'name': 'bufferTime', 'label': 'Buffer Time', 'increment': 1.0},
        {
            'name': 'delaySampling',
            'label': 'Delay Sampling',
            'increment': 1.0,
        },
        {
            'name': 'dynamicsSyncTime',
            'label': 'Dynamics Sync Time',
            'increment': 10,
        },
        {'name': 'showNetInfo', 'label': 'Show Net Info', 'increment': 1},
    ]
    return TestingWindow(
        title=bui.Lstr(resource='settingsWindowAdvanced.netTestingText'),
        entries=entries,
    )


# class NetValTestingWindow(TestingWindow):
#     """Window to test network related settings."""

#     def __init__(self, transition: str = 'in_right'):
#         entries = [
#             {'name': 'bufferTime', 'label': 'Buffer Time', 'increment': 1.0},
#             {
#                 'name': 'delaySampling',
#                 'label': 'Delay Sampling',
#                 'increment': 1.0,
#             },
#             {
#                 'name': 'dynamicsSyncTime',
#                 'label': 'Dynamics Sync Time',
#                 'increment': 10,
#             },
#             {'name': 'showNetInfo', 'label': 'Show Net Info', 'increment': 1},
#         ]
#         super().__init__(
#             title=bui.Lstr(resource='settingsWindowAdvanced.netTestingText'),
#             entries=entries,
#             transition=transition,
#         )
