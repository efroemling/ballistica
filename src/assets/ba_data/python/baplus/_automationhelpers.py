# Released under the MIT License. See LICENSE for details.
#
"""Standalone helpers for our end of the automation channel.

Split out of :mod:`baplus._automationsession` (which holds the session
manager itself) to keep both under the module-size limit.
"""

import json
import base64
import logging
from typing import TYPE_CHECKING

import babase

from efro.util import break_websocket_logger_cycle, strip_exception_tracebacks
from bacommon.automationchannel import HelloEvent

if TYPE_CHECKING:
    from typing import Any

logger = logging.getLogger('ba.automationsession')


def exec_code(code: str) -> tuple[str | None, list[tuple[str, str, str]]]:
    """Run driver-supplied code on the logic thread.

    Runs in ``__main__``'s namespace, as the cloud console does: one
    dict for globals and locals, so functions and lambdas the code
    defines see the names it imports (a bare ``exec()`` in here would
    put those in this function's locals, invisible to them), and names
    persist from one exec to the next like a REPL. Driver-supplied code
    runs with the same freedom a dev-console line does -- including
    running in the foreground context (see ``_handle_exec``), so UI
    calls need a ``with babase.ContextRef.empty():`` around them.

    Returns a description of the exception the code raised (None if it
    didn't) and the ``[automation]`` results it emitted while running,
    both for sending back to the driver.
    """
    import __main__

    from babase import _automation

    _automation.begin_exec_result_capture()
    error: str | None = None
    try:
        # pylint: disable=exec-used
        exec(compile(code, '<automation>', 'exec'), vars(__main__))
    except Exception as exc:  # pylint: disable=broad-except
        logger.exception('error in automation exec')
        error = _describe_exec_error(exc)
        strip_exception_tracebacks(exc)
    finally:
        results = _automation.end_exec_result_capture()
    return error, results


def _describe_exec_error(exc: Exception) -> str:
    """One line for the driver: the exception and where in its code."""
    import traceback

    line: int | None = None
    for frame in traceback.extract_tb(exc.__traceback__):
        if frame.filename == '<automation>':
            line = frame.lineno
    desc = f'{type(exc).__name__}: {exc}'
    return desc if line is None else f'{desc} (line {line})'


def hello_event(app_instance_id: str) -> HelloEvent:
    """Describe ourselves for whoever attaches."""
    env = babase.app.env
    return HelloEvent(
        build_number=env.engine_build_number,
        platform=str(env.platform),
        app_instance_id=app_instance_id,
        gui=env.gui,
    )


def ws_url_for(node_base_url: str) -> str:
    """Turn the node's http base url into our attach url."""
    if node_base_url.startswith('https://'):
        return 'wss://' + node_base_url[len('https://') :] + '/automationdevice'
    if node_base_url.startswith('http://'):
        return 'ws://' + node_base_url[len('http://') :] + '/automationdevice'
    return node_base_url + '/automationdevice'


def report_online(key: str, channel_id: str) -> None:
    """Tell the cloud which channel this registered device offers.

    Carries only the non-secret device id and the channel id; the
    cloud takes our node from the forwarding envelope, never from us.
    Best-effort: a lost report just means a driver finds us on our
    next channel instead. Called from our asyncio loop's thread, but
    cloud sends belong to the logic thread, so we hop there.
    """
    import bacommon.cloud
    from babase import _automation

    msg = bacommon.cloud.AutomationDeviceOnlineMessage(
        automation_device_id=_automation.automation_device_id_for_key(key),
        channel_id=channel_id,
    )

    def _on_response(response: None | Exception) -> None:
        if isinstance(response, Exception):
            logger.info(
                'automation: could not report device online: %s', response
            )

    def _send() -> None:
        plus = babase.app.plus
        if plus is None:
            return
        try:
            plus.cloud.send_message_cb(msg, on_response=_on_response)
        except Exception:  # pylint: disable=broad-except
            logger.exception('automation: error reporting device online')

    babase.pushcall(_send, from_other_thread=True)


def log_locator(
    ws_url: str, channel_id: str, key: str | None, device_id: str | None
) -> None:
    """Log the one string a driver needs to reach us.

    A single opaque handle rather than a URL plus fields: the driver
    side is ``connect(handle)`` and the encoding can grow without
    teaching anyone a new line format. An ephemeral key rides inside
    it so the logged line is a complete copy-paste; a persistent key
    (passed here as ``None``) never does -- it would outlive the log
    line it leaked into. A registered device carries its non-secret
    ``device_id`` instead, so a driver holding the device's key (in
    its localconfig) can match the line to it.

    A registered device is normally driven by name (``automation_drive
    --device``), so its line is only wanted when a tool launched us to
    read it: it logs at INFO only with ``BA_AUTOMATION_LOG_LOCATOR=1``
    (``test_game_run`` sets that), and quietly otherwise, keeping a
    hand-run terminal clean. An ephemeral-key line always logs, since
    it is the only way to reach that channel.
    """
    import os

    payload = {
        'v': 1,
        'kind': 'auto',
        'url': ws_url,
        'session_id': channel_id,
    }
    if key is not None:
        payload['key'] = key
    if device_id is not None:
        payload['device'] = device_id
    encoded = (
        base64.urlsafe_b64encode(json.dumps(payload).encode())
        .decode()
        .rstrip('=')
    )
    if key is None and os.environ.get('BA_AUTOMATION_LOG_LOCATOR') != '1':
        logger.debug('automation-channel: %s', encoded)
        return
    # On ba.app, not our own logger: this is the one line a human has
    # to be able to read out of the log to drive us, and ba.app is
    # the only logger at INFO by default. (Same reason the
    # ``[automation]`` result lines use it.) A locator on a
    # suppressed logger is a locator nobody can find.
    logging.getLogger('ba.app').info('automation-channel: %s', encoded)


async def connect(ws_url: str, channel_id: str, key_hash: str) -> Any:
    """Dial the node for one attach.

    We present our channel id and the hash of our key; the node
    registers them on first contact and checks them on every
    reattach, so a channel is only ever fed by whoever created it.
    """
    import websockets

    from baplus._consolesession import _WsTransport

    sock = await websockets.connect(
        ws_url,
        # ssl only for a wss:// node. When the transport is in insecure
        # mode (the 'Insecure Connections' config / a server downgrade
        # directive for a broken-TLS region) the node url comes through
        # as ws://, and passing an ssl context to a ws:// uri raises.
        # We mirror the transport's own scheme (see v2transport
        # get_connected_node_base_url + its ssl=None-when-insecure).
        ssl=(
            babase.app.net.sslcontext if ws_url.startswith('wss://') else None
        ),
        subprotocols=[websockets.Subprotocol('basmartsocket')],
        additional_headers={
            'User-Agent': babase.user_agent_string(),
            'X-BA-Automation-Id': channel_id,
            'X-BA-Automation-Key-Hash': key_hash,
        },
        open_timeout=10.0,
        # SmartSocket runs its own app-level ping/pong; a second
        # liveness mechanism would only cost us garbage.
        ping_interval=None,
    )
    break_websocket_logger_cycle(sock)
    return _WsTransport(sock)
