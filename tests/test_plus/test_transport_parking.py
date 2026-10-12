# Released under the MIT License. See LICENSE for details.
#
"""Live tests for v2transport message parking.

A message submitted while the transport has no *connected* primary
session is parked for up to ``MAX_PARKED_SECONDS`` (see
``bapluscodegen.pyembed.v2transport``) rather than failing on the
spot, so a click landing in a reconnect gap succeeds a moment later
instead of showing a communication error.

Both cases boot the headless binary, let it connect, then use the
``debug_drop_transport_session`` test hook on the cloud subsystem to
drop the session as if the connection had died. The hook's callback
runs once the session is gone and before any replacement can have
connected, so a ``PingMessage`` sent from it is guaranteed to take the
no-session path:

- **reconnect case**: the transport's normal sleep-and-launch brings a
  new session up within a couple of seconds; the parked ping is
  flushed to it and answered.
- **expiry case**: the drop is made with ``block_reconnect=True`` so
  every reconnect attempt fails; no session arrives inside the park
  limit and the ping fails with the parking deadline error. (A
  servernodequery reject preset is not enough here: the transport
  reuses its cached host list for 30s and never re-queries.)

Each run greps the binary's output for a ``PARKTEST`` marker line and
SIGTERMs on the first match. Runs against the live fleet (prod by
default, like the other live tests); the cost is one ping.

The exec snippet binds its module references as default args: the
``--exec`` namespace's top-level names are not real closure cells, so
a callback that runs later would otherwise die with ``NameError``.
"""

import re
from typing import TYPE_CHECKING

import pytest

from batools import apprun

if TYPE_CHECKING:
    from pathlib import Path

# Safety net if the marker never appears; the reconnect case takes a
# few seconds and the expiry case a bit over the 5s park limit.
_TIMEOUT = 60.0

# Runs once the app is up (an --exec becomes the app's initial
# intent): drops the transport session and pings from the drop
# callback, logging one marker line with the outcome. logging (not
# print) so it flushes immediately.
_EXEC_CODE = '''
import logging
import babase
import bacommon.cloud

BLOCK_RECONNECT = {block!r}

def _on_response(resp, logging=logging):
    if isinstance(resp, Exception):
        logging.warning('PARKTEST fail: %s', resp)
    else:
        logging.warning('PARKTEST ok')

def _send(babase=babase, bacommon=bacommon, cb=_on_response, logging=logging):
    plus = babase.app.plus
    assert plus is not None
    plus.cloud.send_message_cb(bacommon.cloud.PingMessage(), on_response=cb)
    logging.warning('PARKTEST sent')

plus = babase.app.plus
assert plus is not None
plus.cloud.debug_drop_transport_session(
    _send, block_reconnect=BLOCK_RECONNECT
)
'''

_MARKER = re.compile(r'PARKTEST (ok|fail: .*)')


def _run(tmp_path: Path, *, block_reconnect: bool) -> str:
    """Boot headless, run the drop-and-ping recipe, return its output."""
    config_dir = tmp_path / 'ba_root'
    config_dir.mkdir()
    proc = apprun.run_headless_capture(
        purpose='transport parking test',
        config_dir=str(config_dir),
        exec_code=_EXEC_CODE.format(block=block_reconnect),
        env={'BA_LOG_LEVELS': 'ba.v2transport=DEBUG'},
        timeout=_TIMEOUT,
        stop_pattern=_MARKER,
    )
    # The helper merges stderr into stdout.
    return proc.stdout.decode(errors='replace')


def _marker(output: str) -> str:
    match = _MARKER.search(output)
    assert match is not None, (
        'No PARKTEST marker in output (binary never answered the ping?):\n'
        + output[-4000:]
    )
    return match.group(0)


@pytest.mark.skipif(
    apprun.test_runs_disabled(), reason=apprun.test_runs_disabled_reason()
)
def test_parked_message_sent_once_session_reconnects(tmp_path: Path) -> None:
    """A ping sent right after a session drop succeeds once one is back."""
    output = _run(tmp_path, block_reconnect=False)
    assert 'msgio: park PingMessage' in output, output[-4000:]
    assert 'parked message(s) to session' in output, output[-4000:]
    assert _marker(output) == 'PARKTEST ok'


@pytest.mark.skipif(
    apprun.test_runs_disabled(), reason=apprun.test_runs_disabled_reason()
)
def test_parked_message_expires_without_session(tmp_path: Path) -> None:
    """With no session inside the park limit, the ping fails cleanly."""
    output = _run(tmp_path, block_reconnect=True)
    assert 'msgio: park PingMessage' in output, output[-4000:]
    marker = _marker(output)
    assert marker.startswith('PARKTEST fail: '), marker
    assert 'No transport session within' in marker, marker
