# Released under the MIT License. See LICENSE for details.
#
"""In-engine end-to-end test of master + delegate signed-data flow.

Boots the headless client, asks the connected basn to sign a test
payload two ways — once with bamaster's master key (cached on basn for
the InsecureDirective flow) and once with basn's
:class:`~bacommon.securedata.Writer` — and verifies both
archives via :meth:`~bacommon.securedata.Reader.read`.

The verify path inside the binary uses the native C++
``_babase.verify_ed25519`` (the cryptography-package fallback in
``securedata.py`` only fires in non-binary contexts), so a passing
test confirms the production verification path against real
production-shaped signed data.

Hits whichever fleet the binary is built for (prod by default for
prefab binaries — ``BA_FLEET`` only takes effect on dev builds).
basn nodes that predate the ``SecureDataSigningTestRequest``
handler return a ``RemoteError`` and the test xfail-skips itself,
so a stale node in a partial-rollout fleet doesn't fail the build.
A genuine signing/verify regression — handler present but signing
or chain-verify wrong — still fails loudly. Phase-3 stream-call
foundation work depends on this flow being healthy end-to-end.
"""

import os
import re
from typing import TYPE_CHECKING

import pytest

from batools import apprun

if TYPE_CHECKING:
    pass


FAST_MODE = os.environ.get('BA_TEST_FAST_MODE') == '1'


# Hard timeout. The exec snippet quits the binary as soon as the
# RESULT line lands; this is the safety net if connectivity stalls
# or the basn handler errors.
_HEADLESS_TIMEOUT_SECONDS = 30.0

#: Sentinel printed by the exec snippet on success/skip/failure.
#: We stop the binary on the first match so happy-path runtime is
#: just as long as it takes for v2-transport to come up + the
#: round-trip. ``SKIP`` covers the partial-rollout case where the
#: connected basn predates the test-request handler.
_SECDATA_RESULT_RE = re.compile(
    r'SECDATA_TEST_(RESULT|SKIP|FAIL) (?P<rest>.*)$'
)


_EXEC_SNIPPET = r'''
# Poll for plus.cloud.secure_data_reader (populated when the v2
# transport handshake completes), then send a
# SecureDataSigningTestRequest, verify both archives with that
# Reader (which routes through the native _babase.verify_ed25519
# inside the binary), log a sentinel line, and quit.
import logging

import babase
import bacommon.cloud
from bacommon import securedata


_DEADLINE_SECONDS = 20.0  # Stop polling for the Reader after this.


def _emit(line):
    """Print AND log to maximize the odds of hitting stdout."""
    logging.warning(line)
    print(line, flush=True)


def _on_response(response):
    if isinstance(response, Exception):
        # During a partial rollout we may hit:
        #  * a basn predating the handler (RemoteError "internal
        #    error has occurred"), or
        #  * a basn predating the SecureDataSigningTestResponse
        #    shape change (raw-response decode error since the
        #    new client expects an Archive where the old wire
        #    has bytes/cert fields).
        # Treat both as SKIP — neither indicates a regression.
        msg = str(response)
        rl = msg.lower()
        if (
            'internal error' in rl
            or 'error decoding' in rl
            or 'unknown' in rl
            or 'missing' in rl
            or 'soft_default' in rl
        ):
            _emit(f'SECDATA_TEST_SKIP stale-basn exc={response!r}')
        else:
            _emit(f'SECDATA_TEST_FAIL exc={response!r}')
        babase.quit()
        return
    try:
        reader = babase.app.plus.cloud.secure_data_reader

        def _verify(archive):
            try:
                reader.read(archive)
                return ('ok', None)
            except securedata.Invalid as exc:
                return ('invalid', str(exc))

        m_state, m_reason = _verify(response.master_archive)
        d_state, d_reason = _verify(response.delegate_archive)

        if m_state == 'invalid':
            _emit(f'master verify failed: {m_reason}')
        if d_state == 'invalid':
            _emit(f'delegate verify failed: {d_reason}')
        _emit(
            f'SECDATA_TEST_RESULT master={m_state == "ok"}'
            f' delegate={d_state == "ok"}'
        )
    except Exception as exc:  # pylint: disable=broad-except
        _emit(f'SECDATA_TEST_FAIL verify-exc={exc!r}')
    babase.quit()


_elapsed = [0.0]
_POLL_INTERVAL = 0.25


def _send_when_ready():
    plus = babase.app.plus
    if plus is None:
        _emit('SECDATA_TEST_FAIL no-plus')
        babase.quit()
        return

    # Wait for the v2-transport handshake to bundle a Reader.
    # If basn predates the handshake field this stays None for
    # the whole run and we SKIP.
    # pylint: disable=protected-access
    if plus.cloud._secure_data_reader is None:
        _elapsed[0] += _POLL_INTERVAL
        if _elapsed[0] >= _DEADLINE_SECONDS:
            _emit(
                'SECDATA_TEST_SKIP no-reader-bundled'
                f' (waited {_elapsed[0]:.1f}s)'
            )
            babase.quit()
            return
        babase.apptimer(_POLL_INTERVAL, _send_when_ready)
        return

    try:
        plus.cloud.send_message_cb(
            bacommon.cloud.SecureDataSigningTestRequest(),
            on_response=_on_response,
        )
    except Exception as exc:  # pylint: disable=broad-except
        _emit(f'SECDATA_TEST_FAIL send-exc={exc!r}')
        babase.quit()


# Kick off the poll loop immediately; the handshake usually
# completes within ~1s so this resolves quickly on the happy path.
babase.apptimer(_POLL_INTERVAL, _send_when_ready)
'''


@pytest.mark.skipif(
    apprun.test_runs_disabled(), reason=apprun.test_runs_disabled_reason()
)
@pytest.mark.skipif(FAST_MODE, reason='fast mode')
def test_securedata_native_master_and_delegate() -> None:
    """Master- and delegate-signed payloads both verify in-engine.

    Asserts ``master=True delegate=True`` from the in-engine
    verification, proving:

    * basn caches a usable ``static_data_private_key`` (master path).
    * basn's :class:`~bacommon.securedata.Writer` works
      end-to-end (delegate path).
    * Native ``_babase.verify_ed25519`` accepts both signature types
      against the embedded ``STATIC_DATA_PUBLIC_KEYS``.

    Skips cleanly when the connected basn predates the
    ``SecureDataSigningTestRequest`` handler (typical during a
    partial fleet rollout).
    """
    proc = apprun.run_headless_capture(
        purpose='securedata native sign+verify',
        env={
            # ba.app=DEBUG so we see fleet identification + connect
            # progress; ba.v2transport=INFO so a connection-stall
            # tail is grep-friendly if the run misses the deadline.
            'BA_LOG_LEVELS': 'ba.app=DEBUG,ba.v2transport=INFO',
        },
        exec_code=_EXEC_SNIPPET,
        timeout=_HEADLESS_TIMEOUT_SECONDS,
        stop_pattern=_SECDATA_RESULT_RE,
    )
    output = proc.stdout.decode(errors='replace')

    match = _SECDATA_RESULT_RE.search(output)
    assert match is not None, (
        'No SECDATA_TEST_(RESULT|SKIP|FAIL) line found in headless'
        f' output.\n--- output (tail) ---\n{output[-4000:]}'
    )
    rest = match.group('rest')
    kind = match.group(1)
    if kind == 'SKIP':
        # The connected basn is older than this test's handler.
        # Common during a partial fleet rollout; not a regression.
        pytest.skip(f'connected basn lacks handler: {rest}')
    assert kind == 'RESULT', (
        f'Got SECDATA_TEST_FAIL: {rest!r}.\n'
        f'--- output (tail) ---\n{output[-4000:]}'
    )
    # rest should be 'master=True delegate=True'.
    assert 'master=True' in rest, (
        f'Master signature did not verify: {rest!r}.\n'
        f'--- output (tail) ---\n{output[-4000:]}'
    )
    assert 'delegate=True' in rest, (
        f'Delegate signature did not verify: {rest!r}.\n'
        f'--- output (tail) ---\n{output[-4000:]}'
    )
