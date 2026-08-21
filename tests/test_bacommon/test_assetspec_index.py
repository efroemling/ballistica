# Released under the MIT License. See LICENSE for details.
#
"""Tests for flat asset-reference indexing."""

import pytest

from bacommon.assetspec import (
    TextureSpec,
    MeshSpec,
    SoundSpec,
    CollisionMeshSpec,
)
from bacommon.assetspec._index import (
    AssetBucketKind,
    AssetIndexContext,
    AssetIndexError,
    spec_kind,
)

PKG_A = 'a-0.alpha.260101'
PKG_B = 'a-0.beta.260202'
PKG_C = 'a-0.gamma.260303'

#: Whole-package listings: every asset a package holds, sorted, of
#: whatever kind. Deliberately mixes kinds within a package, since that
#: is what a real listing looks like and what the single domain spans.
_LISTINGS: dict[str, list[str]] = {
    PKG_A: ['meshes/box', 'textures/ant', 'textures/bee'],
    PKG_B: [],
    PKG_C: [
        'audio/swish',
        'textures/cat',
        'textures/dog',
        'textures/emu',
    ],
}


def _listings(apverid: str) -> list[str] | None:
    return _LISTINGS.get(apverid)


def _ctx(packages: list[str] | None = None) -> AssetIndexContext:
    return AssetIndexContext(
        [PKG_A, PKG_B, PKG_C] if packages is None else packages, _listings
    )


def test_spec_kind_covers_every_spec_type() -> None:
    """Each spec kind maps to its bucket."""
    assert spec_kind(TextureSpec(PKG_A, 'x')) is AssetBucketKind.TEXTURES
    assert spec_kind(MeshSpec(PKG_A, 'x')) is AssetBucketKind.MESHES
    assert spec_kind(SoundSpec(PKG_A, 'x')) is AssetBucketKind.AUDIO
    assert spec_kind(CollisionMeshSpec(PKG_A, 'x')) is AssetBucketKind.CONSTANT


def test_indices_concatenate_in_manifest_order() -> None:
    """A package's slice follows every earlier package's."""
    ctx = _ctx()
    # PKG_A contributes 3 paths, PKG_B none, so PKG_C starts at 3.
    assert ctx.to_index(MeshSpec(PKG_A, 'meshes/box')) == 0
    assert ctx.to_index(TextureSpec(PKG_A, 'textures/ant')) == 1
    assert ctx.to_index(TextureSpec(PKG_A, 'textures/bee')) == 2
    assert ctx.to_index(SoundSpec(PKG_C, 'audio/swish')) == 3
    assert ctx.to_index(TextureSpec(PKG_C, 'textures/emu')) == 6


def test_one_domain_spans_every_kind() -> None:
    """Kinds share a domain; an index is unique across the manifest.

    This is the property that keeps the two ends in agreement. They
    group a package's paths into buckets differently -- a client files
    collision meshes under ``constant`` while a server's wrapper tree
    keeps them under ``meshes`` -- so a per-kind domain would have
    disagreed. Only the union is guaranteed to match.
    """
    ctx = _ctx()
    seen = {
        ctx.to_index(spec)
        for spec in (
            MeshSpec(PKG_A, 'meshes/box'),
            TextureSpec(PKG_A, 'textures/ant'),
            SoundSpec(PKG_C, 'audio/swish'),
            TextureSpec(PKG_C, 'textures/cat'),
        )
    }
    assert len(seen) == 4


def test_round_trip_every_path() -> None:
    """Every index decodes back to the path that produced it."""
    ctx = _ctx()
    for pkg in (PKG_A, PKG_C):
        for name in _LISTINGS[pkg]:
            spec = TextureSpec(pkg, name)
            back = ctx.from_index(ctx.to_index(spec), AssetBucketKind.TEXTURES)
            assert back == TextureSpec(pkg, name)


def test_kind_selects_the_spec_type_only() -> None:
    """Kind decides the produced type, never which asset."""
    ctx = _ctx()
    idx = ctx.to_index(MeshSpec(PKG_A, 'meshes/box'))
    astex = ctx.from_index(idx, AssetBucketKind.TEXTURES)
    asmesh = ctx.from_index(idx, AssetBucketKind.MESHES)
    # Same asset either way -- only the wrapper type differs.
    assert astex.name == asmesh.name == 'meshes/box'
    assert isinstance(astex, TextureSpec)
    assert isinstance(asmesh, MeshSpec)


def test_empty_package_slice_is_skipped() -> None:
    """A package contributing nothing does not consume an index."""
    ctx = _ctx()
    # PKG_B is empty; index 3 must land in PKG_C, not PKG_B. bisect on
    # equal offsets is the subtle part.
    assert ctx.from_index(3, AssetBucketKind.AUDIO).apverid == PKG_C


def test_package_order_changes_indices() -> None:
    """Indices are manifest-relative, not global."""
    ctx = _ctx([PKG_C, PKG_A])
    assert ctx.to_index(SoundSpec(PKG_C, 'audio/swish')) == 0
    assert ctx.to_index(MeshSpec(PKG_A, 'meshes/box')) == 4


def test_unknown_package_raises() -> None:
    """A spec naming a package outside the manifest is an error.

    This is the property that makes the manifest load-bearing: an
    indexed ref cannot name a package the manifest omits.
    """
    ctx = _ctx()
    with pytest.raises(AssetIndexError, match='not in this manifest'):
        ctx.to_index(TextureSpec('a-0.nope.260101', 'textures/x'))


def test_unknown_asset_raises() -> None:
    """A spec naming an absent asset is an error."""
    ctx = _ctx()
    with pytest.raises(AssetIndexError, match='not found'):
        ctx.to_index(TextureSpec(PKG_A, 'textures/nonexistent'))


def test_out_of_range_index_raises() -> None:
    """An index past the domain is an error, not a wrong asset."""
    ctx = _ctx()
    with pytest.raises(AssetIndexError):
        ctx.from_index(99, AssetBucketKind.TEXTURES)
    with pytest.raises(AssetIndexError, match='negative'):
        ctx.from_index(-1, AssetBucketKind.TEXTURES)


def test_unlistable_package_does_not_break_others() -> None:
    """A package this end cannot list contributes an empty slice.

    The failure should land on a reference that actually needs the
    unknown package, not on preparing the table for a payload that
    merely mentions it.
    """
    ctx = AssetIndexContext([PKG_A, 'a-0.unknown.260101', PKG_C], _listings)
    assert ctx.to_index(MeshSpec(PKG_A, 'meshes/box')) == 0
    assert ctx.to_index(SoundSpec(PKG_C, 'audio/swish')) == 3
    with pytest.raises(AssetIndexError, match='not found'):
        ctx.to_index(TextureSpec('a-0.unknown.260101', 'textures/x'))


def test_domain_size() -> None:
    """Domain size counts every addressable asset in the manifest."""
    assert _ctx().domain_size() == 7
    assert _ctx([PKG_A]).domain_size() == 3
    assert _ctx([PKG_B]).domain_size() == 0


def test_empty_manifest() -> None:
    """An empty manifest addresses nothing and errors cleanly."""
    ctx = AssetIndexContext([], _listings)
    assert ctx.domain_size() == 0
    with pytest.raises(AssetIndexError):
        ctx.from_index(0, AssetBucketKind.TEXTURES)
