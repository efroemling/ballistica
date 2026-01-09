# Released under the MIT License. See LICENSE for details.
#
"""Shiny new doc-ui based store."""

from __future__ import annotations

from typing import override, TYPE_CHECKING

from bauiv1lib.docui import DocUIController

import bauiv1 as bui

if TYPE_CHECKING:
    from bacommon.docui import DocUIRequest, DocUIResponse

    from bauiv1lib.docui import DocUILocalAction


class StoreUIController(DocUIController):
    """DocUI setup for store."""

    @override
    def fulfill_request(self, request: DocUIRequest) -> DocUIResponse:
        return self.fulfill_request_cloud(request, 'classicstore')

    @override
    def local_action(self, action: DocUILocalAction) -> None:

        if action.name == 'get_tokens':
            self._get_tokens(action)
        elif action.name == 'restore_purchases':
            self._restore_purchases()
        else:
            bui.screenmessage(
                f'Invalid local-action "{action.name}".', color=(1, 0, 0)
            )
            bui.getsound('error').play()

    def _restore_purchases(self) -> None:

        plus = bui.app.plus
        assert plus is not None

        # We should always be signed in here. Make noise if not.
        if plus.accounts.primary is None:
            bui.screenmessage(
                bui.Lstr(resource='notSignedInText'), color=(1, 0, 0)
            )
            bui.getsound('error').play()
            return

        plus.restore_purchases()

    def _get_tokens(self, action: DocUILocalAction) -> None:
        from bauiv1lib.gettokens import show_get_tokens_window

        bui.getsound('swish').play()

        show_get_tokens_window(origin_widget=bui.existing(action.widget))
