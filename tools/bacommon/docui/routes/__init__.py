# Released under the MIT License. See LICENSE for details.
#
"""Type-safe routes and local-actions layered over doc-ui v2.

The doc-ui wire format is string based (request paths, arg dicts,
local-action names). The classes here let first-party code work purely
in dataclasses instead; the modules alongside define the routes for
individual doc-ui domains and are shared by whichever ends (client
and/or server) author or handle that domain's pages.
"""

from bacommon.docui.routes._base import (
    DocUIRoute,
    DocUILocalActionBase,
    NoLocalActions,
    DocUIRouteError,
    PressSound,
    family_members,
)
from bacommon.docui.routes._state import (
    DocUIState,
    DocUIStateAssign,
    validate_page_state,
)

__all__ = [
    'family_members',
    'DocUIRoute',
    'DocUILocalActionBase',
    'NoLocalActions',
    'DocUIRouteError',
    'PressSound',
    'DocUIState',
    'DocUIStateAssign',
    'validate_page_state',
]
