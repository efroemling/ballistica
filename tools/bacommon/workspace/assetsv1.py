# Released under the MIT License. See LICENSE for details.
#
"""Public types for assets-v1 workspaces.

While this module is currently only used server-side, its source code
can be useful as reference when setting workspace config data by hand or
for use in client-side workspace modification tools. There may be
advanced settings that are not accessible through the UI/etc.
"""

import datetime
from enum import Enum
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Annotated, override, assert_never

from efro.dataclassio import ioprepped, IOAttrs, IOMultiType
from bacommon.locale import Locale
from bacommon.loctext import StringSelector

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

    #: Optional free-form workspace documentation, appended to the
    #: generated wrapper module's docstring (after the auto-generated
    #: summary line). Empty string means none.
    docs: Annotated[str, IOAttrs('docs', store_default=False)] = ''

    #: Dev-team id granting resolve access to this workspace's
    #: dev/test asset-package versions. None (unset) means owner-only
    #: access — matching the semantics of the asset-package doc's
    #: ``dev_team_id`` (see ``AssetPackage.account_has_access``).
    dev_team: Annotated[
        str | None, IOAttrs('dev_team', store_default=False)
    ] = None

    #: The asset-package name this workspace publishes under. None
    #: means it is derived from the workspace's display name (see
    #: :func:`derive_asset_package_name`); set explicitly to decouple
    #: the published name from the display name (e.g. to keep a
    #: package lineage across a workspace rename, or to have a new
    #: workspace take over publishing an existing package name).
    asset_package_name: Annotated[
        str | None, IOAttrs('asset_package_name', store_default=False)
    ] = None


def derive_asset_package_name(workspace_name: str) -> str:
    """Derive a default asset-package name from a workspace name.

    Lowercases and strips spaces ('My Awesome Assets' ->
    'myawesomeassets'). The single source for this rule — publish
    paths, collision checks, and UI previews must all route through
    it. Note the result is not guaranteed to be a *valid*
    asset-package name (the workspace name may contain characters
    with no valid mapping); consumers validate at point of use.
    """
    return workspace_name.lower().replace(' ', '')


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

        #: The plain-string output. Set for plain entries; empty (and
        #: omitted from the wire) when ``selector`` is set -- the selector
        #: is then the authoritative value, with no separate fallback.
        value: Annotated[str, IOAttrs('value', store_default=False)] = ''

        #: Optional render-time selector (plural/select); set instead of
        #: ``value`` for an entry whose value is chosen at render time.
        selector: Annotated[
            StringSelector | None, IOAttrs('sel', store_default=False)
        ] = None

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


#: Placeholder value for a string with no generated output in its own locale
#: *or* in English. We deliberately do NOT fall back to the brief ``input``
#: here: that's the author's description of what the string should say (a
#: translator prompt), often a long-winded sentence -- not display text -- so
#: rendering it is worse than an obvious "untranslated" marker.
STRING_NOT_TRANSLATED = '<NOT-TRANSLATED>'


def complete_locale_values(
    string_files: dict[str, AssetsV1StringFileV1], locale: Locale
) -> dict[str, str | StringSelector]:
    """English-completed per-locale values for a set of string files.

    Maps each string's logical name to its value for ``locale``: the
    locale's own output, else the English output, else the
    ``STRING_NOT_TRANSLATED`` placeholder. So every locale's map carries the
    **complete key set** with graceful English fallback -- an untranslated
    string still renders (in English where available, else an obvious
    ``<NOT-TRANSLATED>`` marker) rather than failing, and every locale's key
    set is identical. The brief ``input`` is intentionally never used as a
    value: it's the author's prompt/description, not display text.

    The shared value-selection both the asset-build string recipe and the
    `langstr vendor` command route through (paired with
    :func:`~bacommon.langstr.serialize_language_blob`) so the built and
    vendored blobs can't drift.
    """
    out: dict[str, str | StringSelector] = {}
    for name, sfile in string_files.items():
        output = sfile.outputs.get(locale)
        if output is None:
            output = sfile.outputs.get(Locale.ENGLISH)
        if output is None:
            out[name] = STRING_NOT_TRANSLATED
        elif output.selector is not None:
            out[name] = output.selector
        else:
            out[name] = output.value
    return out


class AssetsV1PathValsTypeID(Enum):
    """Types of vals we can store for paths."""

    TEX_V1 = 'tex_v1'
    STR_V1 = 'str_v1'
    AUDIO_V1 = 'audio_v1'
    MESH_V1 = 'mesh_v1'
    GROUP_V1 = 'group_v1'
    CUBE_MAP_V1 = 'cube_map_v1'


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

        if type_id is t.AUDIO_V1:
            return AssetsV1PathValsAudioV1

        if type_id is t.MESH_V1:
            return AssetsV1PathValsMeshV1

        if type_id is t.GROUP_V1:
            return AssetsV1PathValsGroupV1

        if type_id is t.CUBE_MAP_V1:
            return AssetsV1PathValsCubeMapV1

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

    #: Optional free-form documentation for this asset, surfaced as a
    #: comment above the asset in generated wrapper modules (and in the
    #: Sphinx docs). Empty string means no docs.
    docs: Annotated[str, IOAttrs('docs', store_default=False)] = ''

    #: Halve the fallback flavor's level0 downsize divisor (2 instead
    #: of 4) so this asset's fallback carries a higher-res top mip. For
    #: the rare asset whose fallback bytes get consumed directly rather
    #: than just serving as a universal render fallback -- e.g. the
    #: engine cursor texture feeding OS hardware cursors, which wants a
    #: retina-res mip. Deliberately not exposed in the workspace web UI
    #: (it would be noise there); edit workspace.json directly for the
    #: odd asset that needs it.
    fallback_high_res: Annotated[
        bool, IOAttrs('fallback_high_res', store_default=False)
    ] = False

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


class AudioRole(Enum):
    """A sound's channel/encode contract (asset-packages decision #25).

    Names the *technical* contract, not a content category — "music"
    deliberately does not exist as a build-time concept (volume routing
    stays a runtime play-flag; streaming is a length-derived engine
    policy).

    - ``DEFAULT`` — spatialization-ready: downmixed to mono at encode
      (OpenAL only spatializes mono; a hard requirement, not a size
      optimization). The vast majority of sounds.
    - ``PRE_MIXED`` — an authored mix: channels preserved (≤2) and the
      sound always plays listener-space. The recipe stamps a
      ``BA_ROLE=pre_mixed`` vorbis comment tag so the engine knows at
      load time (channel count alone can't carry the bit — a mono
      pre-mixed source stays mono). Music, plus any intentionally
      stereo (or otherwise authored-mix) sound.
    """

    DEFAULT = 'default'
    PRE_MIXED = 'pre_mixed'


class AudioQuality(Enum):
    """Per-sound authoring quality knob (asset-packages decision #25).

    Mirrors the texture knob's LOW/DEFAULT/HIGH pattern. Defined from
    day one as the escape hatch for content whose default encode budget
    doesn't fit (e.g. a short pre-mixed UI sound sharing music's
    bitrate), but nothing consumes it yet — the recipe carries it in
    its cache key only, so wiring it up later rebuilds correctly.
    """

    LOW = 'low'
    DEFAULT = 'default'
    HIGH = 'high'


@ioprepped
@dataclass
class AssetsV1PathValsAudioV1(AssetsV1PathVals):
    """Path-specific values for an audio source in an assets_v1 workspace.

    The per-sound authoring knobs (:class:`AudioRole`,
    :class:`AudioQuality`) are module-level types in this module.
    """

    audio_role: Annotated[
        AudioRole, IOAttrs('audio_role', store_default=False)
    ] = AudioRole.DEFAULT

    audio_quality: Annotated[
        AudioQuality, IOAttrs('audio_quality', store_default=False)
    ] = AudioQuality.DEFAULT

    #: Optional free-form documentation for this asset, surfaced as a
    #: comment above the asset in generated wrapper modules (and in the
    #: Sphinx docs). Empty string means no docs.
    docs: Annotated[str, IOAttrs('docs', store_default=False)] = ''

    @override
    @classmethod
    def get_type_id(cls) -> AssetsV1PathValsTypeID:
        return AssetsV1PathValsTypeID.AUDIO_V1


class MeshRole(Enum):
    """What a mesh ``.obj`` source builds (asset-packages decision #26).

    - ``DEFAULT`` — a display mesh: compiled to the engine's binary
      ``.bob`` format (welded/quantized verts, vertex-cache-optimized
      index order) and served from the flavor-varying ``meshes`` bucket
      (headless builds get none).
    - ``COLLISION`` — a collision mesh: compiled to the engine's binary
      ``.cob`` format (positions + indices for the physics trimesh) and
      served from the flavor-invariant ``constant`` bucket — every
      build including headless gets it, and the bytes are identical
      across all flavors (networked sims/replays must agree on
      collision geometry).
    """

    DEFAULT = 'default'
    COLLISION = 'collision'


@ioprepped
@dataclass
class AssetsV1PathValsMeshV1(AssetsV1PathVals):
    """Path-specific values for a mesh source in an assets_v1 workspace.

    The per-mesh authoring knob (:class:`MeshRole`) is a module-level
    type in this module.
    """

    mesh_role: Annotated[
        MeshRole, IOAttrs('mesh_role', store_default=False)
    ] = MeshRole.DEFAULT

    #: Optional free-form documentation for this asset, surfaced as a
    #: comment above the asset in generated wrapper modules (and in the
    #: Sphinx docs). Empty string means no docs.
    docs: Annotated[str, IOAttrs('docs', store_default=False)] = ''

    @override
    @classmethod
    def get_type_id(cls) -> AssetsV1PathValsTypeID:
        return AssetsV1PathValsTypeID.MESH_V1


@ioprepped
@dataclass
class AssetsV1PathValsGroupV1(AssetsV1PathVals):
    """Path-specific values for a group (directory) in a workspace.

    A group builds no asset of its own; this exists purely to carry
    optional ``docs`` (decision #28) that become the generated wrapper
    group class's docstring. Keyed in ``workspace.json``'s ``path`` dict
    by the directory path (e.g. ``textures`` or ``mydir/subdir``).
    """

    #: Optional free-form documentation for this group, used as the
    #: generated wrapper group class's docstring (a trailing "See source
    #: for the full asset list." is always appended). Empty string means
    #: fall back to the auto-generated docstring.
    docs: Annotated[str, IOAttrs('docs', store_default=False)] = ''

    @override
    @classmethod
    def get_type_id(cls) -> AssetsV1PathValsTypeID:
        return AssetsV1PathValsTypeID.GROUP_V1


@ioprepped
@dataclass
class AssetsV1PathValsCubeMapV1(AssetsV1PathVals):
    """Path-specific values for a cube map (``.cubemap`` dir) in a workspace.

    Cube maps are reflection textures with no Python API (decision #24),
    so they aren't wrapper-visible. This currently carries only optional
    ``docs`` -- stored for completeness/consistency with other asset
    kinds, but not yet consumed by anything (it'll have a home if/when
    cube maps gain a Python surface). Keyed in ``workspace.json``'s
    ``path`` dict by the ``.cubemap`` directory path.
    """

    #: Optional free-form documentation for this cube map. Stored but not
    #: yet surfaced anywhere (cube maps have no wrapper entry). Empty
    #: string means no docs.
    docs: Annotated[str, IOAttrs('docs', store_default=False)] = ''

    @override
    @classmethod
    def get_type_id(cls) -> AssetsV1PathValsTypeID:
        return AssetsV1PathValsTypeID.CUBE_MAP_V1
