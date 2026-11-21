# Released under the MIT License. See LICENSE for details.
#
"""Host-ui messages: encoding, decoding and vetting what peers send.

Helpers for :class:`baclassic.HostUISubsystem` (see
``baclassic._hostui``).
"""

import logging
from typing import TYPE_CHECKING

from efro.util import strip_exception_tracebacks
from efro.dataclassio import dataclass_to_json, dataclass_from_dict
import bacommon.hostui as hui
import bacommon.docui.v2 as dui2
from bacommon.langstr import collect_apvernums as collect_langstr_apvernums

import babase
import bascenev1

from baclassic._hostuiparts import host_ui_text
from baclassic._hostuihandler import status_response

if TYPE_CHECKING:
    from typing import Callable

    from bacommon.assetpackage import ApverNum
    from bacommon.langstr import LangStrSpec
    from bacommon.docui.routes import DocUIRoute

logger = logging.getLogger('ba.net')


def find_id_arg(
    req_a: dui2.Request, req_b: dui2.Request, id_a: int, id_b: int, what: str
) -> str:
    """Which arg of a page's request takes an id.

    ``req_a`` and ``req_b`` are the page's requests for ``id_a`` and
    ``id_b``; the arg is the one holding those, and everything else must
    match. ``what`` names the page for the error.

    :meta private:
    """
    keys: list[str] = [
        k
        for k, v in req_a.args.items()
        if v == id_a and req_b.args.get(k) == id_b
    ]
    others_a = {k: v for k, v in req_a.args.items() if k not in keys}
    others_b = {k: v for k, v in req_b.args.items() if k not in keys}
    if (
        len(keys) != 1
        or req_a.path != req_b.path
        or req_a.method is not req_b.method
        or others_a != others_b
    ):
        raise ValueError(
            f'A {what} must be the same page for every client, with the'
            ' client id in one of its fields.'
        )
    return keys[0]


#: Client ids for finding which arg of a page's request takes one (by
#: building it for both and seeing which arg changes).
#:
#: :meta private:
PROBE_IDS = (1000001, 1000002)


def kick_target(route_a: DocUIRoute, route_b: DocUIRoute) -> hui.KickTarget:
    """Describe a kick page to clients: a request plus its client-id arg.

    ``route_a``/``route_b`` are the page for the two :data:`PROBE_IDS`.

    :meta private:
    """
    req_a = route_a.request()
    req_b = route_b.request()
    return hui.KickTarget(
        request=req_a,
        client_id_arg=find_id_arg(req_a, req_b, *PROBE_IDS, 'kick page'),
    )


def client_page_target(
    get_browse: Callable[[int], dui2.Browse],
) -> hui.ClientPageTarget:
    """Describe a client page to clients: a browse plus its client-id arg.

    :meta private:
    """
    browse_a = get_browse(PROBE_IDS[0])
    browse_b = get_browse(PROBE_IDS[1])
    return hui.ClientPageTarget(
        browse=browse_a,
        client_id_arg=find_id_arg(
            browse_a.request, browse_b.request, *PROBE_IDS, 'client page'
        ),
    )


async def send_response(
    client_id: int, request_id: int, response: dui2.Response
) -> None:
    """Encode a response (in the background) and send it to a client.

    :meta private:
    """
    try:
        data = await babase.app.asyncio_loop.run_in_executor(
            babase.app.threadpool, hui.encode_response, response
        )
    except hui.ResponseTooLargeError as exc:
        logger.warning(
            'Host-ui response to client %d too large: %s', client_id, exc
        )
        strip_exception_tracebacks(exc)
        data = hui.encode_response(
            status_response(dui2.ResponseStatus.UNKNOWN_ERROR)
        )
    except Exception as exc:
        # (A page that can't be serialized, say; the client still gets
        # an answer rather than waiting out its timeout.)
        logger.exception(
            'Error encoding host-ui response to client %d.', client_id
        )
        strip_exception_tracebacks(exc)
        data = hui.encode_response(
            status_response(dui2.ResponseStatus.UNKNOWN_ERROR)
        )
    msg = dataclass_to_json(
        hui.DocUIResponseMessage(request_id=request_id, data=data)
    )
    if len(msg) > hui.MAX_RESPONSE_BYTES:
        logger.warning(
            'Host-ui response to client %d too large (%d bytes compressed;'
            ' max %d); sending an error instead.',
            client_id,
            len(msg),
            hui.MAX_RESPONSE_BYTES,
        )
        msg = dataclass_to_json(
            hui.DocUIResponseMessage(
                request_id=request_id,
                data=hui.encode_response(
                    status_response(dui2.ResponseStatus.UNKNOWN_ERROR)
                ),
            )
        )
    bascenev1.host_ui_send_to_client(client_id, msg)


def decode_message(msg: str, from_host: bool = False) -> hui.Message | None:
    """Decode a raw host-ui jmessage (from a peer; untrusted).

    :meta private:
    """
    try:
        return dataclass_from_dict(
            hui.Message, hui.loads_untrusted(msg)['d'], lossy=True
        )
    except Exception as exc:
        if from_host:
            # (Newer hosts' message types decode fine, so this is a
            # broken or hostile host; rare enough to be worth a look.)
            logger.warning('Invalid host-ui message from host: %s', exc)
        else:
            # Clients are many and untrusted; keep this quiet.
            logger.debug('Invalid host-ui message: %s', exc)
        strip_exception_tracebacks(exc)
        return None


def _host_universe() -> set[ApverNum]:
    scanresults = babase.app.meta.scanresults
    return set() if scanresults is None else set(scanresults.asset_packages)


def spec_packages(spec: LangStrSpec) -> set[ApverNum]:
    """The asset-packages a language-string spec references.

    :meta private:
    """
    acc: set[ApverNum] = set()
    collect_langstr_apvernums(spec, acc)
    return acc


def check_host_label(label: str | babase.LangStr | LangStrSpec) -> None:
    """Warn a host author about text clients will refuse.

    :meta private:
    """
    if isinstance(label, str):
        return
    outside = spec_packages(host_ui_text(label)) - _host_universe()
    if outside:
        logger.warning(
            'Host-ui text references asset-package(s) %s outside this'
            " host's universe; clients will not show it.",
            sorted(outside),
        )


def vet_state(state: hui.State) -> hui.State:
    """Drop what a (untrusted) host sent that we won't show.

    :meta private:
    """
    universe = bascenev1.get_joined_host_asset_packages() or frozenset()

    def _ok(spec: LangStrSpec, what: str) -> bool:
        outside = spec_packages(spec) - universe
        if outside:
            logger.warning(
                'Ignoring host-ui %s referencing asset-package(s) %s'
                " outside the host's universe.",
                what,
                sorted(outside),
            )
            return False
        return True

    def _small(spec: LangStrSpec, limit: int, what: str) -> bool:
        size = len(dataclass_to_json(spec))
        if size > limit:
            logger.warning(
                'Ignoring host-ui %s of %d bytes (max %d).', what, size, limit
            )
            return False
        return True

    buttons: list[hui.Button] = []
    per_placement: dict[hui.ButtonPlacement, int] = {}
    for button in state.buttons:
        if (
            button.placement is hui.ButtonPlacement.UNKNOWN
            or not _ok(button.label, 'button label')
            or not _small(button.label, hui.MAX_LABEL_BYTES, 'button label')
        ):
            continue
        count = per_placement.get(button.placement, 0)
        if count >= hui.MAX_BUTTONS_PER_PLACEMENT:
            if count == hui.MAX_BUTTONS_PER_PLACEMENT:
                logger.warning(
                    'Ignoring host-ui buttons past %d in %s.',
                    hui.MAX_BUTTONS_PER_PLACEMENT,
                    button.placement.name,
                )
                per_placement[button.placement] = count + 1
            continue
        per_placement[button.placement] = count + 1
        buttons.append(button)
    state.buttons = buttons
    if state.notice is not None and (
        not _ok(state.notice, 'notice')
        or not _small(state.notice, hui.MAX_NOTICE_BYTES, 'notice')
    ):
        state.notice = None
    return state
