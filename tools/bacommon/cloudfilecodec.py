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
from functools import cache
from typing import TYPE_CHECKING, assert_never

if TYPE_CHECKING:
    from typing import Iterable

    from compression.zstd import ZstdDict


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


#: Request header on a CAS ``/casblob`` GET: a comma-separated list of
#: :class:`CompressionType` values the client can decode (e.g.
#: ``'zb1,z,u'``). Lets the server fulfill the request in any encoding the
#: client supports -- picking the smallest available -- rather than
#: assuming a fixed one. A client always includes ``u`` (it can always
#: handle uncompressed). Absent ⇒ a legacy client that decodes per its
#: manifest (back-compat).
CAS_ACCEPT_COMPRESSION_HEADER = 'X-Accept-Compression'

#: Response header on a CAS ``/casblob`` GET: the single
#: :class:`CompressionType` value the served bytes are encoded in. The
#: client decodes per THIS header (not its manifest), so whatever the node
#: actually serves -- even a re-negotiated or differently-cached encoding
#: -- is always decoded correctly. Absent ⇒ a legacy node; the client
#: falls back to its manifest's compression.
CAS_COMPRESSION_HEADER = 'X-Cas-Compression'


def format_compression_accept(types: 'Iterable[CompressionType]') -> str:
    """Encode a set of supported types for the accept header."""
    return ','.join(t.value for t in types)


def parse_compression_accept(value: str | None) -> set[CompressionType]:
    """Decode the accept header into a set of known types.

    Tolerant of unknown/empty entries (an unrecognized future value is
    skipped, not an error) so an old server reading a newer client's
    header simply ignores types it doesn't know.
    """
    result: set[CompressionType] = set()
    if value:
        by_value = {t.value: t for t in CompressionType}
        for part in value.split(','):
            ctype = by_value.get(part.strip())
            if ctype is not None:
                result.add(ctype)
    return result


def all_compression_types() -> set[CompressionType]:
    """All :class:`CompressionType` members this build can decode.

    What a client advertises in :data:`CAS_ACCEPT_COMPRESSION_HEADER` --
    every member is decodable here because the codecs (and any bundled
    dictionaries) ship with the build.
    """
    return set(CompressionType)


@cache
def _shared_zstd_dict(dict_bytes: bytes) -> ZstdDict:
    """Return a process-wide shared ``ZstdDict`` for a dictionary's bytes.

    Constructing a ``ZstdDict`` copies and digests the full dictionary,
    so build each distinct dictionary exactly once per process instead
    of once per (de)compress call — clients decompressing blobs and
    servers compressing them both funnel through here many times with
    the same dictionary. IMPORTANT: any *future* pre-shared dictionary
    added to this codec should likewise go through this helper rather
    than calling ``ZstdDict()`` directly. Cache keys are the dictionary
    bytes themselves; sources should hand us a stable cached bytes
    object (see :func:`bacommon.meshzstddict.display_mesh_dict_v1`) so
    the hash is computed once and entries never duplicate.
    """
    from compression import zstd

    return zstd.ZstdDict(dict_bytes)


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

    return zstd.compress(
        data, level=level, zstd_dict=_shared_zstd_dict(dict_bytes)
    )


def zstd_decompress_with_dict(data: bytes, dict_bytes: bytes) -> bytes:
    """Decompress dict-zstd ``data`` using its pre-shared dictionary.

    ``dict_bytes`` must be the exact dictionary used to compress ``data``;
    a mismatch raises or yields garbage.
    """
    from compression import zstd

    return zstd.decompress(data, zstd_dict=_shared_zstd_dict(dict_bytes))


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
