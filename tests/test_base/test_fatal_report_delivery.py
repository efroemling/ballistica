# Released under the MIT License. See LICENSE for details.
#
"""Hermetic tests for fatal-error and unclean-shutdown report delivery.

The engine's low-level reporter posts to ``/fatalerror``; developer
builds can aim it elsewhere with ``BA_FATAL_REPORT_URL``. These tests
point it at a local listener (no network needed) and cover both ways
a report can arrive:

* **Live** - sent while the process goes down.
* **Next launch** - the live send fails (nothing listening), so the
  report is saved under ``<config-dir>/pending_reports/`` and the next
  launch on the same config dir delivers it, prefixed ``DEFERRED:``,
  and deletes it.

...for both report kinds: a fatal error (``_babase.fatal_error()``,
which fires after core is up so the report can be saved) and an
unclean shutdown (logic thread stalled via the
``BA_CRASH_TEST=shutdown_logic_stall`` hook, so the main thread gives
up on it and exits without finalizing).

The end-to-end versions against the real servers live in
``test_fatal_error_report.py``.
"""

import os
import glob
import uuid
import socket
import tempfile
import threading
from typing import override
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

from batools import apprun

FAST_MODE = os.environ.get('BA_TEST_FAST_MODE') == '1'

_RUN_TIMEOUT_SECONDS = 40

_FATAL_EXEC = '''
import _babase

_babase.apptimer(2.0, lambda: _babase.fatal_error('{msg}'))
'''

_QUIT_EXEC = '''
import _babase

_babase.apptimer(2.0, _babase.quit)
'''


class _Listener:
    """Collects bodies POSTed to /fatalerror on a local port."""

    def __init__(self) -> None:
        self.bodies: list[str] = []
        listener = self

        class _Handler(BaseHTTPRequestHandler):
            def do_POST(self) -> None:  # pylint: disable=invalid-name
                """Record the body and say ok."""
                length = int(self.headers.get('Content-Length', '0'))
                body = self.rfile.read(length).decode(errors='replace')
                if self.path == '/fatalerror':
                    listener.bodies.append(body)
                self.send_response(200)
                self.send_header('Content-Length', '0')
                self.end_headers()

            @override
            def log_message(self, format: str, *args: object) -> None:
                del format, args  # Keep test output quiet.

        self._server = ThreadingHTTPServer(('127.0.0.1', 0), _Handler)
        self.url = f'http://127.0.0.1:{self._server.server_address[1]}'
        self._thread = threading.Thread(
            target=self._server.serve_forever, name='fatalreportlistener'
        )
        self._thread.start()

    def close(self) -> None:
        """Shut down and join the server thread."""
        self._server.shutdown()
        self._server.server_close()
        self._thread.join()


def _dead_url() -> str:
    """A local url with nothing listening on it."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(('127.0.0.1', 0))
        port = sock.getsockname()[1]
    return f'http://127.0.0.1:{port}'


def _run(
    config_dir: str, purpose: str, exec_code: str, env: dict[str, str]
) -> tuple[int | None, str]:
    proc = apprun.run_headless_capture(
        purpose=purpose,
        config_dir=config_dir,
        exec_code=exec_code,
        env=env,
        timeout=_RUN_TIMEOUT_SECONDS,
    )
    return proc.returncode, proc.stdout.decode(errors='replace')


def _fail(desc: str, out: str) -> str:
    return f'{desc}\n--- output (tail) ---\n{out[-4000:]}'


def _pending_reports(config_dir: str) -> list[str]:
    return sorted(
        glob.glob(os.path.join(config_dir, 'pending_reports', '*.json'))
    )


def _failing_run(
    kind: str, config_dir: str, url: str, token: str
) -> tuple[int | None, str]:
    """Run the app so it ends in a report of the given kind."""
    if kind == 'fatal':
        return _run(
            config_dir,
            'fatal-report fatal',
            _FATAL_EXEC.format(msg=f'Fatal-Delivery-Test token={token}'),
            {'BA_FATAL_REPORT_URL': url},
        )
    assert kind == 'unclean'
    return _run(
        config_dir,
        'fatal-report unclean',
        _QUIT_EXEC,
        {
            'BA_FATAL_REPORT_URL': url,
            'BA_CRASH_TEST': 'shutdown_logic_stall',
            'BA_CRASH_TEST_TOKEN': token,
        },
    )


def _expected_prefix(kind: str) -> str:
    return 'FATAL ERROR:' if kind == 'fatal' else 'UNCLEAN-SHUTDOWN:'


_KINDS = ['fatal', 'unclean']


@pytest.mark.skipif(
    apprun.test_runs_disabled(), reason=apprun.test_runs_disabled_reason()
)
@pytest.mark.skipif(FAST_MODE, reason='fast mode')
@pytest.mark.parametrize('kind', _KINDS)
def test_live_report(kind: str) -> None:
    """The report arrives while the process goes down; it exits 1."""
    token = f'delivery-{uuid.uuid4().hex[:12]}'
    listener = _Listener()
    try:
        with tempfile.TemporaryDirectory(prefix=f'fatalrep_{kind}_') as tmp:
            code, out = _failing_run(kind, tmp, listener.url, token)
            pending = _pending_reports(tmp)
    finally:
        listener.close()

    matches = [b for b in listener.bodies if token in b]
    assert len(matches) == 1, _fail(
        f'Expected one live report with token {token};'
        f' got {len(matches)} (of {len(listener.bodies)} total).',
        out,
    )
    assert _expected_prefix(kind) in matches[0], matches[0][:2000]
    assert 'DEFERRED' not in matches[0], matches[0][:2000]
    assert not pending, f'Delivered live, but also saved: {pending}'
    assert code == 1, _fail(f'Unexpected exit code {code}.', out)


@pytest.mark.skipif(
    apprun.test_runs_disabled(), reason=apprun.test_runs_disabled_reason()
)
@pytest.mark.skipif(FAST_MODE, reason='fast mode')
@pytest.mark.parametrize('kind', _KINDS)
def test_next_launch_report(kind: str) -> None:
    """An undeliverable report is saved, then sent by the next launch."""
    token = f'delivery-{uuid.uuid4().hex[:12]}'
    with tempfile.TemporaryDirectory(prefix=f'fatalrep_{kind}_') as tmp:
        # First run: nobody listening, so the report must be saved.
        code, out = _failing_run(kind, tmp, _dead_url(), token)
        assert code == 1, _fail(f'Unexpected exit code {code}.', out)
        pending = _pending_reports(tmp)
        assert len(pending) == 1, _fail(
            f'Expected one saved report; found {pending}.', out
        )
        with open(pending[0], encoding='utf-8') as infile:
            saved = infile.read()
        assert token in saved and 'DEFERRED:' in saved, saved[:2000]

        # Second run: a clean launch delivers it and cleans up.
        listener = _Listener()
        try:
            code2, out2 = _run(
                tmp,
                f'fatal-report {kind} relaunch',
                _QUIT_EXEC,
                {'BA_FATAL_REPORT_URL': listener.url},
            )
        finally:
            listener.close()
        leftover = _pending_reports(tmp)

    matches = [b for b in listener.bodies if token in b]
    assert len(matches) == 1, _fail(
        f'Expected the relaunch to deliver one report with token {token};'
        f' got {len(matches)}.',
        out2,
    )
    assert 'DEFERRED: ' + _expected_prefix(kind) in matches[0], matches[0][
        :2000
    ]
    assert not leftover, f'Saved report not deleted: {leftover}'
    assert code2 == 0, _fail(f'Relaunch exit code {code2}.', out2)
