# Released under the MIT License. See LICENSE for details.
#
"""Flat integer indexing for asset references.

A payload that already carries a manifest of asset-package-versions can
name an asset by a single integer instead of an apverid-plus-name pair.
The integer addresses one flat domain: every package in the manifest
contributes its canonical sorted logical-path list -- **all** of its
assets, whatever kind -- concatenated in manifest order.

Deliberately whole-package rather than per-bucket-kind. The two ends
partition a package's paths into buckets differently: a client's
registry splits collision meshes into the flavor-invariant ``constant``
bucket while the server's listing keeps every ``meshes/`` path
together. Measured on baclassicassets that is 360+30 against 390 --
the same 1115 paths overall, grouped differently, which would have
shifted every mesh index past the first collision mesh onto the wrong
asset. Indexing the whole package sidesteps the disagreement entirely,
since only the *union* has to match, and it does.

The union has to be the package's *built* assets, not the ones a
producer can name in Python. Those differ: cube maps are deliberately
wrapper-invisible (decision #24) and the legacy-language-data blob is
a build output with no source file, yet both sit in a client's
registry. Deriving the server's listing from its wrapper tree left it
short by exactly those seven on ``babuiltinassets``, and since that is
the first package in the manifest it moved every later package's slice
-- every store icon rendered as a neighbouring texture, silently. The
server now vendors the real listing per package instead.

The slot's bucket kind is therefore a *check*, not a domain selector:
it says what type the decoded path must be, and a mismatch is an error
rather than a silently wrong asset.

Two properties make this work without shipping any mapping:

* Within one asset-package version, every flavor manifest of a bucket
  kind lists an **identical key set** (asset-packages design, D23/D24).
  So an index means the same asset regardless of which texture profile,
  language or quality flavor an end resolved -- verified in practice: a
  headless run with the null texture profile still reports all 313
  classic textures.
* The manifest pins exact apverids, so a package's listing cannot drift
  underneath an index -- changing the content mints a new apverid, and
  the apverid is part of what the index resolves against.

Related but not identical to scene_v1's indexed wire refs (protocol
39+, ``kAddTextureIndexed``, resolved by
``ClientSession::ResolveIndexedAssetRef_``). That form keeps package and
asset as separate integers and indexes *per bucket kind* -- which is
safe there because both ends read their own resolved registry, so they
partition identically. Here the two ends derive from different sources,
so the domain has to be the one thing they agree on.

The arithmetic lives here, apart from either end's way of obtaining a
listing: the server reads a listing vendored alongside each package,
the client reads its resolved package registry, and neither concern
belongs in the indexing rules. That also makes the rules unit-testable
with no engine and no packages present.

Because the two ends obtain that listing differently they can disagree,
and a disagreement is invisible on its own -- an index that is wrong
but still in range names a different asset, so the page renders wrong
art and nothing raises. :meth:`AssetIndexContext.domain_digest` is what
makes it visible: a payload carries the producer's digest and the
consumer refuses to de-index when its own differs.
"""

# This module is the spec types' own addressing logic and lives in
# their package; reading their private parts here is the implementation,
# not a reach-in from outside.
# pylint: disable=protected-access

import hashlib
from enum import Enum
from bisect import bisect_right
from typing import TYPE_CHECKING, assert_never

from bacommon.assetspec._core import (
    TextureSpec,
    MeshSpec,
    SoundSpec,
    CollisionMeshSpec,
)

if TYPE_CHECKING:
    from typing import Callable

    #: Any of the four spec kinds.
    type AnySpec = TextureSpec | MeshSpec | SoundSpec | CollisionMeshSpec

    #: Supplies a package's canonical sorted logical paths -- every
    #: asset it holds, of every kind -- or None if this end knows
    #: nothing about that package.
    type ListingSource = Callable[[str], 'list[str] | None']


#: First engine build that understands flat-indexed asset references
#: (``Spec | int`` slots in doc-ui pages and client-effects, resolved
#: against the payload's package manifest). Servers emit the spec form
#: to anything older, which stays correct forever -- the two forms are
#: interchangeable, so this gate can be raised or retired freely. The
#: indexed form is not pinned until 1.8.0 ships; during the alpha it
#: can still be reshaped, prod included.
ASSET_INDEX_MIN_BUILD = 22993


class AssetIndexError(Exception):
    """An asset reference could not be indexed or de-indexed.

    Always an authoring or wiring fault rather than a runtime condition:
    a package missing from the manifest, an asset absent from its
    package, or an index outside its domain. Callers should fail
    visibly rather than substitute a placeholder -- a silently wrong
    texture is worse than a loud error.
    """


class AssetBucketKind(Enum):
    """Which bucket kind a spec's asset lives in.

    Values match the asset-package bucket names. Each kind is its own
    flat index domain, so an index is only meaningful alongside the kind
    of the slot holding it -- which the schema always fixes (a texture
    slot holds a texture).
    """

    TEXTURES = 'textures'
    MESHES = 'meshes'
    AUDIO = 'audio'
    CONSTANT = 'constant'


#: The bucket kind each spec type addresses. Collision meshes ride the
#: flavor-invariant ``constant`` bucket (asset-packages decision #26).
SPEC_KINDS: dict[type, AssetBucketKind] = {
    TextureSpec: AssetBucketKind.TEXTURES,
    MeshSpec: AssetBucketKind.MESHES,
    SoundSpec: AssetBucketKind.AUDIO,
    CollisionMeshSpec: AssetBucketKind.CONSTANT,
}


def spec_kind(spec: 'AnySpec') -> AssetBucketKind:
    """Return the bucket kind a spec addresses."""
    kind = SPEC_KINDS.get(type(spec))
    if kind is None:
        raise AssetIndexError(f'not an asset spec: {type(spec).__name__}')
    return kind


class AssetIndexContext:
    """Converts asset specs to and from flat indices for one manifest.

    Built from the manifest's package list (in index order) and a way to
    obtain each package's full logical-path listing. The offset table is
    built on first use and cached, since obtaining a listing can be the
    expensive part.
    """

    def __init__(self, packages: list[str], listings: 'ListingSource') -> None:
        self._packages = list(packages)
        self._listings = listings
        self._offsets: list[int] | None = None
        self._names: list[list[str]] = []
        self._lookup: list[dict[str, int]] = []

    @property
    def packages(self) -> list[str]:
        """The manifest's packages, in index order."""
        return list(self._packages)

    def _prepare(self) -> None:
        """Build (once) the offset table across the manifest."""
        if self._offsets is not None:
            return
        offsets: list[int] = []
        total = 0
        for apverid in self._packages:
            listing = self._listings(apverid)
            if listing is None:
                # A package this end knows nothing about. Its slice is
                # empty rather than an error: a payload may legitimately
                # reference other packages in the same manifest, and the
                # failure should land on the specific reference that
                # needs this package, not on preparing the table.
                listing = []
            offsets.append(total)
            self._names.append(listing)
            self._lookup.append({name: i for i, name in enumerate(listing)})
            total += len(listing)
        self._offsets = offsets

    def to_index(self, spec: 'AnySpec') -> int:
        """Return the flat index for a spec.

        Raises :class:`AssetIndexError` if the spec's package is not in
        the manifest or its asset is not in that package.
        """
        # Validates the spec is one we know how to address at all.
        spec_kind(spec)
        self._prepare()
        assert self._offsets is not None
        try:
            pkgidx = self._packages.index(spec._apverid)
        except ValueError:
            raise AssetIndexError(
                f'package {spec._apverid!r} is not in this manifest'
            ) from None
        local = self._lookup[pkgidx].get(spec._name)
        if local is None:
            raise AssetIndexError(
                f'asset {spec._name!r} not found in {spec._apverid}'
            )
        return self._offsets[pkgidx] + local

    def from_index(self, index: int, kind: AssetBucketKind) -> 'AnySpec':
        """Return the spec a flat index names.

        ``kind`` comes from the slot holding the index and decides which
        spec type is produced. It is not a domain selector -- there is
        one domain per manifest -- so it cannot shift which asset an
        index resolves to; it only decides how that asset is typed.

        Raises :class:`AssetIndexError` for an index outside the domain.
        """
        self._prepare()
        assert self._offsets is not None
        offsets = self._offsets
        if index < 0:
            raise AssetIndexError(f'negative asset index {index}')
        # The package owning this index is the last one whose offset is
        # <= it. bisect_right lands one past that.
        pkgidx = bisect_right(offsets, index) - 1
        if pkgidx < 0:
            raise AssetIndexError(f'asset index {index} has no package')
        local = index - offsets[pkgidx]
        if local >= len(self._names[pkgidx]):
            raise AssetIndexError(
                f'asset index {index} is outside this manifest'
                f' (total {self.domain_size()})'
            )
        apverid = self._packages[pkgidx]
        name = self._names[pkgidx][local]

        # The kind decides the spec type. Explicit rather than a
        # type-table lookup: a table returns ``type`` and so erases the
        # result to ``Any``, and this way a new bucket kind fails here
        # at build time.
        if kind is AssetBucketKind.TEXTURES:
            return TextureSpec(apverid, name)
        if kind is AssetBucketKind.MESHES:
            return MeshSpec(apverid, name)
        if kind is AssetBucketKind.AUDIO:
            return SoundSpec(apverid, name)
        if kind is AssetBucketKind.CONSTANT:
            return CollisionMeshSpec(apverid, name)
        assert_never(kind)

    def domain_size(self) -> int:
        """Total number of addressable assets across the manifest."""
        self._prepare()
        assert self._offsets is not None
        if not self._names:
            return 0
        return self._offsets[-1] + len(self._names[-1])

    def domain_digest(self) -> str:
        """Short digest of the exact domain this context addresses.

        The two ends derive their listings from different sources (the
        server from vendored package data, the client from its resolved
        registry), and nothing about a wrong-but-in-range index makes
        itself known: it simply names a different asset. So a payload
        carries the producer's digest and the consumer refuses to
        de-index when its own does not match -- turning a silent
        wrong-art render into a loud, locatable failure.

        Taken over the *effective* listings, i.e. the slices actually
        laid out, with an unknown package contributing an empty one
        exactly as it does when preparing the offset table. That is the
        right thing to compare: a package one end has no listing for
        still occupies zero width on both, and it is the widths and
        contents that decide what an index means.
        """
        self._prepare()
        hasher = hashlib.sha256()
        for apverid, names in zip(self._packages, self._names, strict=True):
            hasher.update(apverid.encode())
            hasher.update(b'\0')
            for name in names:
                hasher.update(name.encode())
                hasher.update(b'\n')
            hasher.update(b'\0')
        return hasher.hexdigest()[:16]

    def describe_domain(self) -> str:
        """Per-package slice widths, for diagnosing a digest mismatch.

        Names each package and how wide a slice it got here, which is
        what pins a mismatch to one package rather than to the payload
        as a whole.
        """
        self._prepare()
        return ', '.join(
            f'{apverid}={len(names)}'
            for apverid, names in zip(self._packages, self._names, strict=True)
        )
