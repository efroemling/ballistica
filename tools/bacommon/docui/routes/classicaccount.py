# Released under the MIT License. See LICENSE for details.
#
"""Routes for the classic account doc-ui domain (``classicaccount``).

Pages about an account, served by the master server: the place to link
to whenever an account is shown (a party member's verified account, a
stats row, and so on). Other domains open them through local-actions of
their own (see ``TypedDocUIController.browse_from()`` on the client).
"""

from dataclasses import dataclass
from typing import Annotated, override

from efro.dataclassio import ioprepped, IOAttrs

import bacommon.docui.v2 as dui2
from bacommon.docui.routes import (
    DocUIRoute,
    DocUILocalActionBase,
    family_members,
)


class ClassicAccountRoute(DocUIRoute):
    """Family class for classic account routes."""

    @override
    @classmethod
    def get_route_types(cls) -> tuple[type[DocUIRoute], ...]:
        return family_members(AnyClassicAccountRoute)

    @override
    @classmethod
    def get_window_layout(cls) -> dui2.WindowLayout:
        return dui2.WindowLayout.WIDE_TALL


@ioprepped
@dataclass
class Account(ClassicAccountRoute, path='/account'):
    """About one account."""

    #: The account (``a-XXX``).
    account_id: Annotated[str, IOAttrs('a')]


# All routes in the family (just the one for now).
AnyClassicAccountRoute = Account


class ClassicAccountLocalAction(DocUILocalActionBase):
    """Family class for classic account local-actions."""

    @override
    @classmethod
    def get_action_types(cls) -> tuple[type[DocUILocalActionBase], ...]:
        return family_members(AnyClassicAccountLocalAction)


@ioprepped
@dataclass
class Placeholder(ClassicAccountLocalAction, name='placeholder'):
    """Does nothing; holds the family's place until it has real ones.

    (A family needs a member.)
    """


# All local-actions in the family.
AnyClassicAccountLocalAction = Placeholder
