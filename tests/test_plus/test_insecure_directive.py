# Released under the MIT License. See LICENSE for details.
#
"""Live tests for the signed insecure-connections directive flow.

Exercises the end-to-end path against the prod master server:

- HTTPS servernodequery (no force arg) should return no directive.
- Plain-HTTP servernodequery with the force arg should return a
  signed directive that verifies against the embedded public key and
  carries ``use_insecure=True`` with a near-future expiry.
- The ``ws://`` WebSocket endpoint on one of the returned basn hosts
  should accept a plain-text connection and complete the transport
  handshake -- proof that insecure-mode is actually usable on real
  infra when the directive says so.

Only PROD serves HTTP (dev redirects to HTTPS at Apache, test is
Cloud-Run HTTPS-only), so these tests hardcode the prod bootstrap
host and skip otherwise.
"""

from __future__ import annotations

import os
import json
import asyncio
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    pass


FAST_MODE = os.environ.get('BA_TEST_FAST_MODE') == '1'

#: Prod bootstrap endpoint -- only fleet that serves HTTP directly.
_PROD_BOOTSTRAP_HOST = 'regional.ballistica.net'


def _servernodequery(scheme: str, *, force: bool) -> dict:
    """Hit /servernodequery on prod, return parsed JSON body."""
    import urllib.request
    import urllib.parse

    params = {'seed': '1', 'b': '22814'}
    if force:
        params['test_insecure_directive'] = 'force'
    qs = urllib.parse.urlencode(params)
    url = f'{scheme}://{_PROD_BOOTSTRAP_HOST}/servernodequery?{qs}'
    with urllib.request.urlopen(url, timeout=10.0) as resp:  # noqa: S310
        data: dict = json.loads(resp.read().decode())
        return data


@pytest.mark.skipif(FAST_MODE, reason='fast mode')
def test_no_directive_on_https() -> None:
    """HTTPS response should carry no insecure_directive."""
    response = _servernodequery('https', force=False)
    assert (
        'id' not in response
    ), f'Unexpected insecure_directive in HTTPS response: {response}'


@pytest.mark.skipif(FAST_MODE, reason='fast mode')
def test_signed_directive_on_http_force() -> None:
    """Plain-HTTP with the force arg should return a verifiable directive.

    Covers the full flow: server signs, client verifies against the
    embedded public key, payload decodes. Any of these breaking means
    the feature is broken.
    """
    pytest.importorskip('cryptography')

    import base64
    from cryptography.hazmat.primitives.asymmetric import ed25519
    from cryptography.exceptions import InvalidSignature
    from efro.dataclassio import dataclass_from_json
    from bacommon.net import InsecureDirectivePayload
    from bacommon.securedata import STATIC_DATA_PUBLIC_KEYS

    response = _servernodequery('http', force=True)
    directive = response.get('id')
    assert directive is not None, (
        f'Expected insecure_directive on HTTP response with force arg;'
        f' got {response}'
    )

    # Bytes fields round-trip through base64 in the JSON wire format.
    payload = base64.b64decode(directive['p'])
    signature = base64.b64decode(directive['s'])

    verified = False
    for pubkey_bytes in STATIC_DATA_PUBLIC_KEYS:
        pubkey = ed25519.Ed25519PublicKey.from_public_bytes(pubkey_bytes)
        try:
            pubkey.verify(signature, payload)
            verified = True
            break
        except InvalidSignature:
            continue
    if not verified:
        pytest.fail(
            'Directive signature failed to verify against any of the'
            ' embedded STATIC_DATA_PUBLIC_KEYS.'
        )

    parsed = dataclass_from_json(InsecureDirectivePayload, payload.decode())
    assert (
        parsed.use_insecure is True
    ), f'Expected use_insecure=True from force arg; got {parsed}'


@pytest.mark.skipif(FAST_MODE, reason='fast mode')
def test_ws_insecure_endpoint_accepts_handshake() -> None:
    """Open ws:// to a prod basn host, complete the transport handshake.

    Proves the insecure-transport path is actually usable end-to-end:
    basn serves ws://, completes the WebSocket upgrade, and returns
    the TransportAgentHandshakeResponse in response to a valid
    TransportAgentHandshakeMessage. Wire format is constructed as a
    raw dict using the IOAttrs short keys, since the pyembed
    dataclass definitions aren't importable from a pytest context.
    """
    pytest.importorskip('websockets')

    response = _servernodequery('http', force=True)
    hosts = response.get('h') or []
    assert hosts, f'No hosts returned in servernodequery response: {response}'
    host = hosts[0]

    # Handshake message. Keys match IOAttrs tags on
    # baplusmeta.pyembed.batocloud.TransportAgentHandshakeMessage;
    # providing the legacy 4 fields lets the server identify us
    # without needing the newer app_instance_info bundle.
    handshake_msg = {
        'b': 22814,  # ba_build
        'n': 'insecure-directive-test',  # device_name
        'u': 'test-private-device-uuid',  # private_device_uuid
        'au': 'test-local-app-instance-uuid',  # local_app_instance_uuid
        'i': None,  # app_instance_info
    }

    async def _run() -> dict:
        import websockets

        url = f'ws://{host}/ws_transport'
        async with websockets.connect(url, ssl=None, open_timeout=10.0) as ws:
            await ws.send(json.dumps(handshake_msg).encode())
            raw = await asyncio.wait_for(ws.recv(), timeout=10.0)
            assert isinstance(
                raw, bytes
            ), f'Expected bytes handshake response; got {type(raw)}'
            decoded: dict = json.loads(raw.decode())
            return decoded

    result = asyncio.run(_run())
    # Short-key 'b' is basn_build on TransportAgentHandshakeResponse.
    assert 'b' in result, f'Handshake response missing basn_build: {result}'
    assert isinstance(
        result['b'], int
    ), f'basn_build should be int; got {result}'
