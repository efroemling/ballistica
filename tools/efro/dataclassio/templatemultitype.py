# Released under the MIT License. See LICENSE for details.
#
"""Template for an IOMultitype setup.

To use this template, simply copy the contents of this module somewhere
and then replace 'TemplateMultiType' with 'YourType'.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, assert_never, override

from enum import Enum
from dataclasses import dataclass

from efro.dataclassio import ioprepped, IOMultiType

if TYPE_CHECKING:
    pass


class TemplateMultiTypeTypeID(Enum):
    """Type ID for each of our subclasses."""

    TEST = 'test'


class TemplateMultiType(IOMultiType[TemplateMultiTypeTypeID]):
    """Top level class for our multitype."""

    @override
    @classmethod
    def get_type_id(cls) -> TemplateMultiTypeTypeID:
        # Require child classes to supply this themselves. If we did a
        # full type registry/lookup here it would require us to import
        # everything and would prevent lazy loading.
        raise NotImplementedError()

    @override
    @classmethod
    def get_type(
        cls, type_id: TemplateMultiTypeTypeID
    ) -> type[TemplateMultiType]:
        """Return the subclass for each of our type-ids."""
        # pylint: disable=cyclic-import

        t = TemplateMultiTypeTypeID
        if type_id is t.TEST:
            return Test

        # Important to make sure we provide all types.
        assert_never(type_id)


@ioprepped
@dataclass
class Test(TemplateMultiType):
    """Just a test."""

    @override
    @classmethod
    def get_type_id(cls) -> TemplateMultiTypeTypeID:
        return TemplateMultiTypeTypeID.TEST
