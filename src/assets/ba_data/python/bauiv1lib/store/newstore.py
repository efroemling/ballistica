# Released under the MIT License. See LICENSE for details.
#
"""Shiny new doc-ui based store."""

from __future__ import annotations

from typing import override, TYPE_CHECKING


from bauiv1lib.docui import DocUIController

if TYPE_CHECKING:
    from bacommon.docui import DocUIRequest, DocUIResponse


class StoreUIController(DocUIController):
    """DocUI setup for store."""

    @override
    def fulfill_request(self, request: DocUIRequest) -> DocUIResponse:
        return self.fulfill_request_cloud(request, 'classicstore')
