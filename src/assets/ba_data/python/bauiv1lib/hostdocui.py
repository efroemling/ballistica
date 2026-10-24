# Released under the MIT License. See LICENSE for details.
#
"""Doc-ui windows showing pages a game host serves (host doc-ui).

A host's pages arrive over the game connection and the host is
untrusted, so before showing one we refuse references outside the
host's package universe, drop client-effects untrusted sources may not
run, and drop local-actions entirely. Our own pages (when we're the
host) skip all that. Design: ``docs/initiatives/host-docui.md``.
"""

import concurrent.futures
from typing import TYPE_CHECKING, override

from efro.util import strip_exception_tracebacks
import bacommon.hostui as hui
import bacommon.docui.v2 as dui2
import bacommon.clienteffect as clfx
from bacommon.docui.walk import page_actions
import bauiv1 as bui
import bascenev1 as bs
from bauiv1lib.docui import DocUIController

if TYPE_CHECKING:
    from typing import Literal

    import bacommon.hostui
    import bacommon.docui.v2
    from bacommon.assetpackage import ApverNum
    from bacommon.docui import DocUIRequest, DocUIResponse

#: How long to wait for a host to answer (seconds). Doc-ui windows
#: share only a couple of background workers, so a silent host must
#: not hold one for long.
REQUEST_TIMEOUT = 10.0


class HostDocUIController(DocUIController):
    """Fulfills requests for host-served pages.

    Our own pages (when we're the host) arrive as response objects and
    are trusted; a host's arrive encoded, and get decoded and vetted
    here.
    """

    @override
    def fulfill_request(self, request: DocUIRequest) -> DocUIResponse:
        if not isinstance(request, dui2.Request):
            return self.error_response(request)
        classic = bui.app.classic
        assert classic is not None

        future: concurrent.futures.Future[dui2.Response | bytes | None] = (
            concurrent.futures.Future()
        )
        bui.pushcall(
            bui.CallStrict(classic.host_ui.submit_request, request, future),
            from_other_thread=True,
        )
        try:
            result = future.result(timeout=REQUEST_TIMEOUT)
        except concurrent.futures.TimeoutError:
            future.cancel()
            # Hosts answer quickly or not at all; worth knowing about.
            bui.uilog.warning(
                'Host never answered request for host page %r (%.0fs).',
                request.path,
                REQUEST_TIMEOUT,
            )
            result = None
        if result is None:
            return self.error_response(
                request, self.ErrorType.COMMUNICATION_ERROR
            )
        if isinstance(result, dui2.Response):
            # Our own page (we're the host).
            return result

        # A host's page, still as it came over the wire; we're in a
        # background thread, so decode it here.
        try:
            response = hui.decode_response(result)
        except Exception as exc:
            bui.uilog.warning('Invalid host page: %s', exc)
            strip_exception_tracebacks(exc)
            return self.error_response(request)
        if not isinstance(response, dui2.Response) or not vet_response(
            response
        ):
            return self.error_response(request)
        return response

    @override
    def get_cache_key_extra(self) -> str | None:
        # Pages depend on which host we're talking to (and change
        # under us); don't cache them.
        return None

    @override
    def get_window_toolbar_visibility(
        self,
    ) -> Literal['menu_full', 'menu_minimal']:
        return 'menu_full' if bui.in_main_menu() else 'menu_minimal'


def vet_response(response: bacommon.docui.v2.Response) -> bool:
    """Make a host's response safe to show, in place.

    Returns False if it can't be shown at all.

    :meta private:
    """
    from bauiv1lib.docui._resolve import collect_apvernums

    # Everything must come from the host's universe; we already have
    # all of that, and must never be made to fetch anything else.
    universe = bs.get_joined_host_asset_packages() or frozenset()
    apvernums: set[ApverNum] = set(response.packages)
    collect_apvernums(response.page, apvernums)
    clfx.collect_apvernums(response.client_effects, apvernums)
    outside = apvernums - universe
    if outside:
        bui.uilog.warning(
            'Refusing host page referencing asset-package(s) %s outside'
            " the host's universe.",
            sorted(outside),
        )
        return False

    response.client_effects = _allowed_effects(response.client_effects)
    if response.local_action is not None:
        bui.uilog.warning(
            'Ignoring local-action %r from host page.', response.local_action
        )
        response.local_action = None
        response.local_action_args = None
    for action in page_actions(response.page):
        if isinstance(action, dui2.Local):
            action.immediate_client_effects = _allowed_effects(
                action.immediate_client_effects
            )
            if action.immediate_local_action is not None:
                bui.uilog.warning(
                    'Ignoring local-action %r from host page.',
                    action.immediate_local_action,
                )
                action.immediate_local_action = None
                action.immediate_local_action_args = None
    return True


def _allowed_effects(effects: list[clfx.Effect]) -> list[clfx.Effect]:
    out: list[clfx.Effect] = []
    for effect in effects:
        if effect.allowed_in_untrusted():
            out.append(effect)
        else:
            # Warn so we can see what hosts want and widen the list.
            bui.uilog.warning(
                'Ignoring client-effect %s from host page'
                ' (not allowed from untrusted sources).',
                type(effect).__name__,
            )
    return out


def show_host_docui_window(
    button: bacommon.hostui.Button, origin_widget: bui.Widget | None = None
) -> None:
    """Open the page a host-defined button leads to.

    :meta private:
    """
    from bauiv1lib.docui import DocUIWindow, WindowOptions

    controller = HostDocUIController()
    bui.app.ui_v1.auxiliary_window_activate(
        win_type=DocUIWindow,
        win_create_call=bui.CallStrict(
            controller.create_window,
            button.request,
            origin_widget=origin_widget,
            options=WindowOptions(layout=button.layout),
        ),
        # Per page, so pressing one host button while another's page is
        # up goes there rather than toggling the open one away.
        win_extra_type_id=(
            f'{HostDocUIController.get_window_extra_type_id()}'
            f':{button.request.path}'
        ),
    )


def button_label(button: bacommon.hostui.Button) -> bui.LangStr:
    """The label to show for a host-defined button.

    :meta private:
    """
    from efro.dataclassio import dataclass_to_json

    return bui.LangStr(dataclass_to_json(button.label))
