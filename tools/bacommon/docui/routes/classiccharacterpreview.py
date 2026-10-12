# Released under the MIT License. See LICENSE for details.
#
"""Routes for the classic character-preview doc-ui domain.

A character being tried out in a game (sent there from its builder
page; see the game's character-preview session): the profile editor
for it, as a player who picks the character will see it. Saving
changes nothing stored anywhere; it answers with the character as
edited for the preview session to carry on with.
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


class CharacterPreviewRoute(DocUIRoute):
    """Family class for classic character-preview routes."""

    @override
    @classmethod
    def get_route_types(cls) -> tuple[type[DocUIRoute], ...]:
        return family_members(AnyCharacterPreviewRoute)

    @override
    @classmethod
    def get_window_layout(cls) -> dui2.WindowLayout:
        # The profile editor's layout: controls in the column, the
        # character beside them.
        return dui2.WindowLayout.VIEWER


@ioprepped
@dataclass
class Edit(CharacterPreviewRoute, path='/'):
    """The profile editor for a previewed character.

    The draft being composed rides along as page state (the profile
    editor's own:
    :class:`~bacommon.docui.routes.classicstore.ProfileDraft`).
    """

    #: The preview's id, as the game was given it with the character.
    preview_id: Annotated[str, IOAttrs('r')]


@ioprepped
@dataclass
class Save(CharacterPreviewRoute, path='/save', method=dui2.RequestMethod.POST):
    """Save the editor's draft; answered with :class:`Saved`."""

    preview_id: Annotated[str, IOAttrs('r')]


# All character-preview routes.
AnyCharacterPreviewRoute = Edit | Save


class CharacterPreviewLocalAction(DocUILocalActionBase):
    """Family class for classic character-preview local-actions."""

    @override
    @classmethod
    def get_action_types(cls) -> tuple[type[DocUILocalActionBase], ...]:
        return family_members(AnyCharacterPreviewLocalAction)


@ioprepped
@dataclass
class Saved(CharacterPreviewLocalAction, name='saved'):
    """The previewed character was edited; here it is as it now stands."""

    preview_id: Annotated[str, IOAttrs('r')]

    #: The character, in the form the game was first given it.
    character: Annotated[str, IOAttrs('c')]


# All character-preview local-actions.
AnyCharacterPreviewLocalAction = Saved
