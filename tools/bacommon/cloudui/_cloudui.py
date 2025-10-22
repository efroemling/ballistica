# Released under the MIT License. See LICENSE for details.
#
"""Full UIs defined in the cloud - similar to a basic form of html"""

from __future__ import annotations

from enum import Enum
from dataclasses import dataclass
from typing import override, assert_never, TYPE_CHECKING

from efro.dataclassio import ioprepped, IOMultiType

if TYPE_CHECKING:
    pass


class CloudUITypeID(Enum):
    """Type ID for each of our subclasses."""

    UNKNOWN = 'u'
    V1 = 'v1'


class CloudUI(IOMultiType[CloudUITypeID]):
    """UI defined by the cloud.

    Conceptually similar to a basic html page, except using app UI.
    """

    @override
    @classmethod
    def get_type_id(cls) -> CloudUITypeID:
        # Require child classes to supply this themselves. If we did a
        # full type registry/lookup here it would require us to import
        # everything and would prevent lazy loading.
        raise NotImplementedError()

    @override
    @classmethod
    def get_type(cls, type_id: CloudUITypeID) -> type[CloudUI]:
        """Return the subclass for each of our type-ids."""
        # pylint: disable=cyclic-import

        t = CloudUITypeID
        if type_id is t.UNKNOWN:
            return UnknownCloudUI
        if type_id is t.V1:
            from bacommon.cloudui.v1 import UI

            return UI

        # Make sure we cover all types.
        assert_never(type_id)

    @override
    @classmethod
    def get_unknown_type_fallback(cls) -> CloudUI:
        # If we encounter some future type we don't know anything about,
        # drop in a placeholder.
        return UnknownCloudUI()

    @override
    @classmethod
    def get_type_id_storage_name(cls) -> str:
        return '_t'


@ioprepped
@dataclass
class UnknownCloudUI(CloudUI):
    """Fallback type for unrecognized UI types.

    Will show the client a 'cannot display this UI' placeholder page.
    """

    @override
    @classmethod
    def get_type_id(cls) -> CloudUITypeID:
        return CloudUITypeID.UNKNOWN
