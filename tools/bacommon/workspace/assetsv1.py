# Released under the MIT License. See LICENSE for details.
#
"""Public types for assets-v1 workspaces.

These types may only be used server-side, but they are exposed here
for reference when setting workspace config data by hand or for use
in client-side workspace modification tools. There may be advanced
settings that are not accessible through the UI/etc.
"""

from __future__ import annotations

import datetime
from enum import Enum
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Annotated, override, assert_never

from efro.dataclassio import ioprepped, IOAttrs, IOMultiType
from bacommon.locale import Locale


if TYPE_CHECKING:
    pass


@ioprepped
@dataclass
class AssetsV1GlobalVals:
    """Global values for an assets_v1 workspace."""

    base_assets: Annotated[
        str | None, IOAttrs('base_assets', store_default=False)
    ] = None

    base_assets_filter: Annotated[
        str, IOAttrs('base_assets_filter', store_default=False)
    ] = ''


class AssetsV1StrInputTypeID(Enum):
    """Type ID for each of our subclasses."""

    BASIC = 'b'


class AssetsV1StrInput(IOMultiType[AssetsV1StrInputTypeID]):
    """Top level class for our multitype."""

    @override
    @classmethod
    def get_type_id(cls) -> AssetsV1StrInputTypeID:
        # Require child classes to supply this themselves. If we did a
        # full type registry/lookup here it would require us to import
        # everything and would prevent lazy loading.
        raise NotImplementedError()

    @override
    @classmethod
    def get_type(
        cls, type_id: AssetsV1StrInputTypeID
    ) -> type[AssetsV1StrInput]:
        """Return the subclass for each of our type-ids."""
        # pylint: disable=cyclic-import

        t = AssetsV1StrInputTypeID
        if type_id is t.BASIC:
            return BasicV1StrInput

        # Important to make sure we provide all types.
        assert_never(type_id)


@ioprepped
@dataclass
class BasicV1StrInput(AssetsV1StrInput):
    """Just a test."""

    @override
    @classmethod
    def get_type_id(cls) -> AssetsV1StrInputTypeID:
        return AssetsV1StrInputTypeID.BASIC


@ioprepped
@dataclass
class AssetsV1StrData:
    """Data and output for a string asset."""

    @dataclass
    class Output:
        """Represents a single instance of localized output."""

        class Source(Enum):
            """Where localized output can come from."""

            AI_V1 = 'ai_v1'

        output_id: Annotated[int, IOAttrs('i')]
        created: Annotated[datetime.datetime, IOAttrs('c')]
        source: Annotated[Source, IOAttrs('s')]
        locale: Annotated[Locale, IOAttrs('l')]
        value_default: Annotated[
            str | None, IOAttrs('d', store_default=False)
        ] = None

    inputs: Annotated[list[AssetsV1StrInput], IOAttrs('i')] = field(
        default_factory=list
    )
    outputs: Annotated[list[Output], IOAttrs('o')] = field(default_factory=list)
    next_output_id: Annotated[int, IOAttrs('n')] = 0


class AssetsV1PathValsTypeID(Enum):
    """Types of vals we can store for paths."""

    TEX_V1 = 'tex_v1'
    # STR_V1 = 'str_v1'


class AssetsV1PathVals(IOMultiType[AssetsV1PathValsTypeID]):
    """Top level class for path vals classes."""

    @override
    @classmethod
    def get_type_id_storage_name(cls) -> str:
        return 'type'

    @override
    @classmethod
    def get_type_id(cls) -> AssetsV1PathValsTypeID:
        # Require child classes to supply this themselves. If we
        # did a full type registry/lookup here it would require us
        # to import everything and would prevent lazy loading.
        raise NotImplementedError()

    @override
    @classmethod
    def get_type(
        cls, type_id: AssetsV1PathValsTypeID
    ) -> type[AssetsV1PathVals]:
        # pylint: disable=cyclic-import
        t = AssetsV1PathValsTypeID

        if type_id is t.TEX_V1:
            return AssetsV1PathValsTexV1

        # Important to make sure we provide all types.
        assert_never(type_id)


@ioprepped
@dataclass
class AssetsV1PathValsTexV1(AssetsV1PathVals):
    """Path-specific values for an assets_v1 workspace path."""

    class TextureQuality(Enum):
        """Quality settings for our textures."""

        LOW = 'low'
        MEDIUM = 'medium'
        HIGH = 'high'

    # Just dummy testing values for now.
    texture_quality: Annotated[
        TextureQuality, IOAttrs('texture_quality', store_default=False)
    ] = TextureQuality.MEDIUM

    @override
    @classmethod
    def get_type_id(cls) -> AssetsV1PathValsTypeID:
        return AssetsV1PathValsTypeID.TEX_V1
