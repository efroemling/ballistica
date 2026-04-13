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


class LeaguePresidencyUIController(DocUIController):
    """DocUI setup for store."""

    @override
    def fulfill_request(self, request: DocUIRequest) -> DocUIResponse:
        return self.fulfill_request_cloud(request, 'classicleaguepresidency')

    @override
    def local_action(self, action: DocUILocalAction) -> None:
        if action.name == 'get_tokens':
            self._get_tokens(action)
        else:
            bui.screenmessage(
                f'Invalid local-action "{action.name}".', color=(1, 0, 0)
            )
            bui.getsound('error').play()

    def _get_tokens(self, action: DocUILocalAction) -> None:
        from bauiv1lib.gettokens import show_get_tokens_window

        bui.getsound('swish').play()
        show_get_tokens_window(origin_widget=bui.existing(action.widget))
