# Released under the MIT License. See LICENSE for details.
"""zstd (de)compression for cloud-file blobs.

Holds the :class:`CompressionType` enum (how a stored blob is encoded)
plus the codec dispatch mapping each type to a concrete zstd operation --
including which pre-shared dictionary a dict-based type uses. Lives in
``bacommon`` so both server components (which compress on store) and
client components (which read the compression type from an asset manifest
and decompress on load) share one source of truth for the type->codec
mapping and load identical dictionary bytes.

Compression is always expressed relative to a cloud-file's *canonical*
(uncompressed) content: a blob's stored bytes are the canonical content
run through its :class:`CompressionType`. ``UNCOMPRESSED`` means the
stored bytes *are* the canonical content.
"""

from enum import Enum
from typing import assert_never


class CompressionType(Enum):
    """How a blob's stored bytes are compressed.

    New members can be added as we see fit. Each member must encode
    enough to decompress deterministically -- dictionary-based members
    bake in the exact dictionary *and* version, so a stored blob is
    always decodable by whatever holds that member. The enum *value* is a
    stable wire string: it travels in asset manifests for the client to
    read, so values must never change.
    """

    #: Stored bytes are the canonical content verbatim.
    UNCOMPRESSED = 'u'

    #: Stored bytes are the canonical content run through plain zstd.
    ZSTD = 'z'

    #: Stored bytes are the canonical content run through zstd using the
    #: v1 display-mesh (``.bob``) dictionary
    #: (:func:`bacommon.meshzstddict.display_mesh_dict_v1`). The dict and
    #: its version are fixed by this member.
    ZSTD_DICT_BOB_V1 = 'zb1'


def zstd_compress(data: bytes, level: int) -> bytes:
    """Compress ``data`` with plain zstd at the given level."""
    from compression import zstd

    return zstd.compress(data, level=level)


def zstd_decompress(data: bytes) -> bytes:
    """Decompress plain-zstd ``data`` produced by :func:`zstd_compress`."""
    from compression import zstd

    return zstd.decompress(data)


def zstd_compress_with_dict(
    data: bytes, dict_bytes: bytes, level: int
) -> bytes:
    """Compress ``data`` with zstd using a pre-shared dictionary."""
    from compression import zstd

    return zstd.compress(data, level=level, zstd_dict=zstd.ZstdDict(dict_bytes))


def zstd_decompress_with_dict(data: bytes, dict_bytes: bytes) -> bytes:
    """Decompress dict-zstd ``data`` using its pre-shared dictionary.

    ``dict_bytes`` must be the exact dictionary used to compress ``data``;
    a mismatch raises or yields garbage.
    """
    from compression import zstd

    return zstd.decompress(data, zstd_dict=zstd.ZstdDict(dict_bytes))


def compress_for_type(
    canonical: bytes, ctype: CompressionType, *, level: int
) -> bytes:
    """Encode ``canonical`` bytes per ``ctype``.

    The canonical (uncompressed) content identified by a cloud-file's
    ``cloud_file_id``. Inverse of :func:`decompress_for_type`. This is the
    single source of truth for which dictionary a dict-based type uses.
    """
    if ctype is CompressionType.UNCOMPRESSED:
        return canonical
    if ctype is CompressionType.ZSTD:
        return zstd_compress(canonical, level=level)
    if ctype is CompressionType.ZSTD_DICT_BOB_V1:
        from bacommon.meshzstddict import display_mesh_dict_v1

        return zstd_compress_with_dict(
            canonical, display_mesh_dict_v1(), level=level
        )
    assert_never(ctype)


def decompress_for_type(stored: bytes, ctype: CompressionType) -> bytes:
    """Decode ``stored`` bytes per ``ctype`` back to canonical content.

    Inverse of :func:`compress_for_type`.
    """
    if ctype is CompressionType.UNCOMPRESSED:
        return stored
    if ctype is CompressionType.ZSTD:
        return zstd_decompress(stored)
    if ctype is CompressionType.ZSTD_DICT_BOB_V1:
        from bacommon.meshzstddict import display_mesh_dict_v1

        return zstd_decompress_with_dict(stored, display_mesh_dict_v1())
    assert_never(ctype)
