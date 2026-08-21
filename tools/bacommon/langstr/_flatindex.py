# Released under the MIT License. See LICENSE for details.
#
"""Folding an indexed language-string into a single wire integer.

:class:`~bacommon.langstr.LangStrSpecResourceIndexed` already addresses
a string by two integers -- a package index into the payload's manifest
and a string index within that package. This folds that pair into one
integer the same way asset references are folded
(:mod:`bacommon.assetspec._index`): each package contributes its string
count, concatenated in manifest order, and a package's strings start at
the sum of the counts before it.

Only the *counts* are needed, not the names. Unfolding produces the
same two-integer form the native decoder already consumes, so nothing
downstream has to learn anything new -- which is what makes this a
small change rather than a parallel resolution path.

A string carrying substitutions cannot fold: the subs have nowhere to
live in a bare integer. Those keep the object form, and a payload
mixing the two is normal.
"""

import hashlib
from bisect import bisect_right
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Callable

    #: Supplies a package's language-string count, or None if this end
    #: has no language table for it.
    type CountSource = Callable[[str], 'int | None']


#: First engine build that understands folded (single-integer)
#: language-string references. Servers emit the two-integer form to
#: anything older; the forms are interchangeable, so this gate may move
#: freely. The folded form is not pinned until 1.8.0 ships; during the
#: alpha it can still be reshaped, prod included.
LANGSTR_FLAT_MIN_BUILD = 22993


class LangStrIndexError(Exception):
    """A language-string index could not be folded or unfolded.

    An authoring or wiring fault rather than a runtime condition: a
    package outside the manifest, or a flat index outside the domain.
    """


class LangStrFlatIndexContext:
    """Folds/unfolds indexed language-strings for one manifest.

    Built from the manifest's package list (in index order) and a way to
    obtain per-package string counts. The offset table is built once on
    first use.
    """

    def __init__(self, packages: list[str], counts: 'CountSource') -> None:
        self._packages = list(packages)
        self._counts = counts
        self._offsets: list[int] | None = None
        self._sizes: list[int] = []

    def _prepare(self) -> None:
        if self._offsets is not None:
            return
        offsets: list[int] = []
        total = 0
        for apverid in self._packages:
            count = self._counts(apverid)
            if count is None:
                # A package this end has no table for. Zero-width rather
                # than an error, so the failure lands on a reference
                # that actually needs it.
                count = 0
            offsets.append(total)
            self._sizes.append(count)
            total += count
        self._offsets = offsets

    def to_flat(self, pkg: int, index: int) -> int:
        """Fold a (package index, string index) pair into one integer."""
        self._prepare()
        assert self._offsets is not None
        if pkg < 0 or pkg >= len(self._offsets):
            raise LangStrIndexError(
                f'package index {pkg} is outside this manifest'
                f' ({len(self._offsets)} package(s))'
            )
        if index < 0 or index >= self._sizes[pkg]:
            raise LangStrIndexError(
                f'string index {index} is outside package {pkg}'
                f' ({self._sizes[pkg]} string(s))'
            )
        return self._offsets[pkg] + index

    def from_flat(self, flat: int) -> tuple[int, int]:
        """Unfold one integer back into (package index, string index)."""
        self._prepare()
        assert self._offsets is not None
        if flat < 0:
            raise LangStrIndexError(f'negative string index {flat}')
        # The package owning this index is the last one whose offset is
        # <= it. bisect_right lands one past that.
        pkg = bisect_right(self._offsets, flat) - 1
        if pkg < 0:
            raise LangStrIndexError(f'string index {flat} has no package')
        local = flat - self._offsets[pkg]
        if local >= self._sizes[pkg]:
            raise LangStrIndexError(
                f'string index {flat} is outside this manifest'
                f' (total {self.domain_size()})'
            )
        return (pkg, local)

    def domain_size(self) -> int:
        """Total number of addressable strings across the manifest."""
        self._prepare()
        assert self._offsets is not None
        if not self._sizes:
            return 0
        return self._offsets[-1] + self._sizes[-1]

    def domain_digest(self) -> str:
        """Short digest of the exact domain this context addresses.

        The string counterpart to
        :meth:`~bacommon.assetspec.AssetIndexContext.domain_digest`, and
        for the same reason: a folded index that lands in the wrong
        package still decodes to *a* string, so nothing downstream
        notices. A payload carries the producer's digest and the
        consumer refuses to unfold when its own does not match.

        Counts alone, since counts are all the layout depends on -- the
        names stay native at both ends.
        """
        self._prepare()
        hasher = hashlib.sha256()
        for apverid, size in zip(self._packages, self._sizes, strict=True):
            hasher.update(f'{apverid}:{size}\n'.encode())
        return hasher.hexdigest()[:16]

    def describe_domain(self) -> str:
        """Per-package string counts, for diagnosing a digest mismatch."""
        self._prepare()
        return ', '.join(
            f'{apverid}={size}'
            for apverid, size in zip(self._packages, self._sizes, strict=True)
        )
