# Released under the MIT License. See LICENSE for details.
#
"""Public types for assets-v1 workspaces.

While this module is currently only used server-side, its source code
can be useful as reference when setting workspace config data by hand or
for use in client-side workspace modification tools. There may be
advanced settings that are not accessible through the UI/etc.
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


class WrapperType(Enum):
    """Python wrapper-module flavor for an asset-package version.

    Selects which feature-set's loader API the generated wrapper
    delegates to. Members today correspond 1:1 with feature-sets, but
    the type is deliberately named ``WrapperType`` (not
    ``WrapperFeatureset``) to leave room for non-featureset-shaped
    variants (e.g. tooling-only or future loader APIs) without a
    rename.
    """

    BASCENEV1 = 'bascenev1'
    BAUIV1 = 'bauiv1'


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


class AssetsV1StringFileTypeID(Enum):
    """Type ID for each of our subclasses."""

    V1 = 'v1'


class AssetsV1StringFile(IOMultiType[AssetsV1StringFileTypeID]):
    """Top level class for our multitype."""

    @override
    @classmethod
    def get_type_id_storage_name(cls) -> str:
        return 'string_file_version'

    @override
    @classmethod
    def get_type_id(cls) -> AssetsV1StringFileTypeID:
        # Require child classes to supply this themselves. If we did a
        # full type registry/lookup here it would require us to import
        # everything and would prevent lazy loading.
        raise NotImplementedError()

    @override
    @classmethod
    def get_type(
        cls, type_id: AssetsV1StringFileTypeID
    ) -> type[AssetsV1StringFile]:
        """Return the subclass for each of our type-ids."""
        # pylint: disable=cyclic-import

        t = AssetsV1StringFileTypeID
        if type_id is t.V1:
            return AssetsV1StringFileV1

        # Important to make sure we provide all types.
        assert_never(type_id)


@ioprepped
@dataclass
class AssetsV1StringFileV1(AssetsV1StringFile):
    """Our initial version of string file data."""

    class StylePreset(Enum):
        """Preset for general styling in translated strings."""

        NONE = 'none'
        TITLE = 'title'
        LOUD = 'loud'
        SOFT = 'soft'

    @override
    @classmethod
    def get_type_id(cls) -> AssetsV1StringFileTypeID:
        return AssetsV1StringFileTypeID.V1

    @dataclass
    class Output:
        """Represents a single localized output."""

        #: When this output was last changed.
        modtime: Annotated[
            datetime.datetime, IOAttrs('modtime', time_format='float')
        ]

        #: Default value (no counts involved).
        value: Annotated[str, IOAttrs('value')]

    input: Annotated[str, IOAttrs('input')]
    input_modtime: Annotated[
        datetime.datetime, IOAttrs('input_modtime', time_format='float')
    ]
    style_preset: Annotated[
        StylePreset, IOAttrs('style_preset', store_default=False)
    ] = StylePreset.NONE
    outputs: Annotated[dict[Locale, Output], IOAttrs('outputs')] = field(
        default_factory=dict
    )


class AssetsV1PathValsTypeID(Enum):
    """Types of vals we can store for paths."""

    TEX_V1 = 'tex_v1'
    STR_V1 = 'str_v1'


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

        if type_id is t.STR_V1:
            return AssetsV1PathValsStrV1

        # Important to make sure we provide all types.
        assert_never(type_id)


class TextureQuality(Enum):
    """Per-texture authoring quality knob (decision #19).

    ``DEFAULT`` is the normal case (the vast majority of textures);
    ``LOW`` and ``HIGH`` are deliberate per-texture overrides for
    special cases (e.g. ``HIGH`` for a hero texture that must stay
    crisp, ``LOW`` for one that can afford to be cheap). Named
    ``DEFAULT`` rather than ``MEDIUM`` to communicate that — it's the
    baseline, not a middle setting you'd routinely reach past.

    ``LOW``/``DEFAULT``/``HIGH`` are blanket settings that map to a
    sensible value for whichever encoder a profile uses (ASTC block
    size on mobile, BC7 RDO lambda on desktop). ``CUSTOM`` instead
    defers to the per-format :class:`AstcSettings` / :class:`Bc7Settings`
    so a texture can be tuned independently per encoder (e.g. ASTC
    ``HIGH`` while BC7 ``DEFAULT``). Distinct from the bucket-level
    ``TextureTier``.
    """

    LOW = 'low'
    DEFAULT = 'default'
    HIGH = 'high'
    CUSTOM = 'custom'


class Role(Enum):
    """What a texture is for (its authoring intent).

    Drives mip-filtering math and encoder flags (asset-packages
    initiative decisions #19/#23). Intent-based rather than a bundle
    of low-level mechanical flags — the recipe maps each role to a
    concrete filtering/encoding behavior. ``normal_map`` / ``data``
    are reserved slots for when such content (and the compressed-
    profile recipes) land.
    """

    #: sRGB color with straight opacity alpha. The pipeline
    #: premultiplies it by its alpha for storage (decision #23):
    #: premult-weighted, halo-free mip filtering in the requested
    #: render_space, premult output bytes, ``ALPHA_PREMULTIPLIED``
    #: DFD flag set. The common case for color sprites. Renders
    #: correctly only with premult-blend (the renderer wiring lands
    #: in a later step; until then ``DEFAULT`` output shows darkened
    #: edges under the legacy straight-blend path).
    DEFAULT = 'default'

    #: sRGB color whose SOURCE RGB is already premultiplied by its
    #: alpha (e.g. glow sprites — they carry additive ``RGB > alpha``
    #: values that straight alpha cannot represent). The pipeline does
    #: NOT re-multiply; mips filter the premultiplied RGB directly (in
    #: the requested render_space) and the flag is set. Renders
    #: identically to ``DEFAULT`` (both premult-blend); they differ
    #: only in whether the pipeline applies the multiply.
    SOURCE_PREMULTIPLIED = 'source_premultiplied'

    #: sRGB color with straight alpha whose RGB channels carry
    #: meaningful color even in transparent regions, so they must be
    #: preserved (decision #23). The pipeline does NOT premultiply:
    #: mips filter RGB and alpha INDEPENDENTLY (color still filtered
    #: in the requested render_space, but with no premult round-trip,
    #: which would zero — and fail to recover — the transparent-region
    #: color). Straight output bytes; ``ALPHA_PREMULTIPLIED`` flag
    #: clear. Renders with ordinary straight-alpha blending.
    STRAIGHT_ALPHA = 'straight_alpha'


class AstcBlockSize(Enum):
    """ASTC square block size — the mobile bitrate lever.

    Smaller block = more bits per texel = higher quality + larger
    output. Consulted only when an :class:`AstcSettings` has its
    ``texture_quality`` set to ``CUSTOM``; otherwise the blanket
    ``LOW``/``DEFAULT``/``HIGH`` map to a value in this range
    (``LOW`` = ``TWELVE_BY_TWELVE``, ``HIGH`` = ``FOUR_BY_FOUR``).
    """

    FOUR_BY_FOUR = '4x4'
    FIVE_BY_FIVE = '5x5'
    SIX_BY_SIX = '6x6'
    EIGHT_BY_EIGHT = '8x8'
    TEN_BY_TEN = '10x10'
    TWELVE_BY_TWELVE = '12x12'


class Bc7Rdo(Enum):
    """BC7 RDO (rate-distortion optimization) lambda — the desktop lever.

    BC7 is a fixed 8bpp block format, so its size lever is RDO: higher
    lambda steers the encoder toward more zlib/LZ-compressible output
    (smaller on-disk) at the cost of quality. ``OFF`` disables RDO
    (best quality, largest). Consulted only when a :class:`Bc7Settings`
    has its ``texture_quality`` set to ``CUSTOM``; otherwise the blanket
    ``LOW``/``DEFAULT``/``HIGH`` map to a value in this range
    (``LOW`` = ``FOUR``, ``HIGH`` = ``OFF``).
    """

    OFF = 'off'
    ZERO_POINT_ONE_TWO_FIVE = '0.125'
    ZERO_POINT_TWO_FIVE = '0.25'
    ZERO_POINT_FIVE = '0.5'
    ONE = '1'
    TWO = '2'
    FOUR = '4'


@ioprepped
@dataclass
class AstcSettings:
    """Per-texture ASTC (mobile) encode settings.

    Consulted only when the texture's top-level ``texture_quality`` is
    ``CUSTOM``. Its own ``texture_quality`` may in turn be ``CUSTOM``
    to use the explicit ``block_size``; otherwise ``LOW``/``DEFAULT``/
    ``HIGH`` map to the encoder's block-size range. Fully defaulted so
    a texture never has to store it explicitly.
    """

    texture_quality: Annotated[
        TextureQuality, IOAttrs('tq', store_default=False)
    ] = TextureQuality.DEFAULT

    block_size: Annotated[AstcBlockSize, IOAttrs('bs', store_default=False)] = (
        AstcBlockSize.SIX_BY_SIX
    )


@ioprepped
@dataclass
class Bc7Settings:
    """Per-texture BC7 (desktop) encode settings.

    Consulted only when the texture's top-level ``texture_quality`` is
    ``CUSTOM``. Its own ``texture_quality`` may in turn be ``CUSTOM``
    to use the explicit ``rdo`` lambda; otherwise ``LOW``/``DEFAULT``/
    ``HIGH`` map to the encoder's RDO range. Fully defaulted so a
    texture never has to store it explicitly.
    """

    texture_quality: Annotated[
        TextureQuality, IOAttrs('tq', store_default=False)
    ] = TextureQuality.DEFAULT

    rdo: Annotated[Bc7Rdo, IOAttrs('rdo', store_default=False)] = Bc7Rdo.ONE


@ioprepped
@dataclass
class AssetsV1PathValsTexV1(AssetsV1PathVals):
    """Path-specific values for an assets_v1 workspace path.

    The per-texture quality knobs (:class:`TextureQuality`,
    :class:`Role`, :class:`AstcSettings`, :class:`Bc7Settings`) are
    module-level types in this module.
    """

    texture_quality: Annotated[
        TextureQuality, IOAttrs('texture_quality', store_default=False)
    ] = TextureQuality.DEFAULT

    texture_role: Annotated[
        Role, IOAttrs('texture_role', store_default=False)
    ] = Role.DEFAULT

    #: Per-format encode settings, consulted only when
    #: ``texture_quality`` is ``CUSTOM``. Fully defaulted so a texture
    #: never has to store them explicitly.
    astc_settings: Annotated[
        AstcSettings, IOAttrs('astc', store_default=False)
    ] = field(default_factory=AstcSettings)

    bc7_settings: Annotated[
        Bc7Settings, IOAttrs('bc7', store_default=False)
    ] = field(default_factory=Bc7Settings)

    @override
    @classmethod
    def get_type_id(cls) -> AssetsV1PathValsTypeID:
        return AssetsV1PathValsTypeID.TEX_V1

    def normalize(self) -> None:
        """Reset redundant/unused settings to defaults, in place.

        A pure tidiness pass to run before storing: it never changes the
        resolved result, only drops dead data so ``store_default=False``
        can strip it from workspace.json. Resolution consults the
        per-format settings only when the top-level ``texture_quality``
        is ``CUSTOM``, and a format's explicit ``block_size``/``rdo`` only
        when that format's own ``texture_quality`` is ``CUSTOM`` -- so
        anything outside those paths is unused and gets cleared here.
        """
        astc_defaults = AstcSettings()
        bc7_defaults = Bc7Settings()

        # A non-CUSTOM format quality ignores the explicit value: clear it.
        if self.astc_settings.texture_quality is not TextureQuality.CUSTOM:
            self.astc_settings.block_size = astc_defaults.block_size
        if self.bc7_settings.texture_quality is not TextureQuality.CUSTOM:
            self.bc7_settings.rdo = bc7_defaults.rdo

        # Both formats on the same non-CUSTOM blanket value is identical to
        # just setting the top-level knob: collapse to it.
        if (
            self.texture_quality is TextureQuality.CUSTOM
            and self.astc_settings.texture_quality
            is self.bc7_settings.texture_quality
            and self.astc_settings.texture_quality is not TextureQuality.CUSTOM
        ):
            self.texture_quality = self.astc_settings.texture_quality

        # A non-CUSTOM top-level quality never consults per-format settings:
        # clear them entirely.
        if self.texture_quality is not TextureQuality.CUSTOM:
            self.astc_settings = astc_defaults
            self.bc7_settings = bc7_defaults


@ioprepped
@dataclass
class AssetsV1PathValsStrV1(AssetsV1PathVals):
    """Path-specific values for an assets_v1 workspace path."""

    #: Hash generated when all translations for this entry are complete.
    #: Used as a fast-out for checking whether updates are needed.
    up_to_date_state: Annotated[
        str | None, IOAttrs('up_to_date_state', store_default=False)
    ] = None

    @override
    @classmethod
    def get_type_id(cls) -> AssetsV1PathValsTypeID:
        return AssetsV1PathValsTypeID.STR_V1
