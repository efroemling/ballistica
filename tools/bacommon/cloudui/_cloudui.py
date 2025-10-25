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


class CloudUIPageTypeID(Enum):
    """Type ID for each of our subclasses."""

    UNKNOWN = 'u'
    V1 = 'v1'


class CloudUIPage(IOMultiType[CloudUIPageTypeID]):
    """UI defined by the cloud.

    Conceptually similar to a basic html page, except using app UI.
    """

    @override
    @classmethod
    def get_type_id(cls) -> CloudUIPageTypeID:
        # Require child classes to supply this themselves. If we did a
        # full type registry/lookup here it would require us to import
        # everything and would prevent lazy loading.
        raise NotImplementedError()

    @override
    @classmethod
    def get_type(cls, type_id: CloudUIPageTypeID) -> type[CloudUIPage]:
        """Return the subclass for each of our type-ids."""
        # pylint: disable=cyclic-import

        t = CloudUIPageTypeID
        if type_id is t.UNKNOWN:
            return UnknownCloudUIPage
        if type_id is t.V1:
            from bacommon.cloudui.v1 import Page

            return Page

        # Make sure we cover all types.
        assert_never(type_id)

    @override
    @classmethod
    def get_unknown_type_fallback(cls) -> CloudUIPage:
        # If we encounter some future type we don't know anything about,
        # drop in a placeholder.
        return UnknownCloudUIPage()

    @override
    @classmethod
    def get_type_id_storage_name(cls) -> str:
        return '_t'


@ioprepped
@dataclass
class UnknownCloudUIPage(CloudUIPage):
    """Fallback type for unrecognized UI types.

    Will show the client a 'cannot display this UI' placeholder page.
    """

    @override
    @classmethod
    def get_type_id(cls) -> CloudUIPageTypeID:
        return CloudUIPageTypeID.UNKNOWN
