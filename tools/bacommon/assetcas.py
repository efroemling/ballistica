# Released under the MIT License. See LICENSE for details.
"""Shared content-addressed asset-blob download primitive.

Used by both the game client's asset subsystem and the ``bacloud`` CLI to
fetch content-addressed blobs from a basn node's ``/casblob`` endpoint,
verify them, and write them into a local content-addressed cache. The
logic here is engine-agnostic: the caller supplies the urllib3 pool, the
node base URL, the encoded capability token, and the destination cache
root, and owns concurrency, retry, and progress reporting itself.
"""

import os
import base64
import hashlib
import tempfile
from typing import TYPE_CHECKING

import urllib3
import urllib3.util

from efro.dataclassio import dataclass_to_json
from bacommon.cloudfilecodec import CompressionType, decompress_for_type

if TYPE_CHECKING:
    from bacommon import securedata


class CasDownloadError(Exception):
    """A CAS-blob fetch, hash-verify, or write failed."""


def encode_asset_token(token: securedata.Archive) -> str:
    """Encode a capability token for the ``X-Asset-Token`` header.

    Returns base64-urlsafe of the token's canonical JSON (HTTP headers
    don't carry raw JSON cleanly).
    """
    return (
        base64.urlsafe_b64encode(dataclass_to_json(token).encode())
        .rstrip(b'=')
        .decode('ascii')
    )


def cas_blob_path(root: str, filehash: str) -> str:
    """Return the path a CAS blob occupies under a cache root.

    Blobs are sharded 256 ways by the first two hex chars of the hash to
    keep per-directory counts low for cache scanning.
    """
    return os.path.join(root, filehash[:2], filehash[2:])


def blob_present(roots: list[str], filehash: str, size: int) -> bool:
    """Is this CAS blob already present at the expected size in any root?

    Present-but-wrong-size counts as absent (so it gets refetched and
    overwritten). The free ``st_size`` check is a cheap catch for external
    truncation or tampering, not a content proof.
    """
    for root in roots:
        try:
            st = os.stat(cas_blob_path(root, filehash))
        except OSError:
            continue
        if st.st_size == size:
            return True
        # Present but wrong size in this root; treat as absent.
    return False


def cas_write(dest_root: str, filehash: str, data: bytes) -> None:
    """sha256-verify ``data`` then atomically write it into ``dest_root``.

    Verify, write to a temp file in the destination directory, ``fsync``,
    then ``os.replace`` (atomic on the same filesystem). A file at its CAS
    path is therefore always whole-and-correct: a crash mid-write leaves
    only a temp file, never a partial blob at the final path. Raises
    :class:`CasDownloadError` on a hash mismatch.
    """
    actual = hashlib.sha256(data).hexdigest()
    if actual != filehash:
        raise CasDownloadError(
            f'CAS write hash mismatch for {filehash}: got {actual}.'
        )
    dest = cas_blob_path(dest_root, filehash)
    destdir = os.path.dirname(dest)
    os.makedirs(destdir, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=destdir, prefix='.tmp_')
    try:
        with os.fdopen(fd, 'wb') as outfile:
            outfile.write(data)
            outfile.flush()
            os.fsync(outfile.fileno())
        os.replace(tmp, dest)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def download_cas_blob(
    pool: urllib3.PoolManager,
    base_url: str,
    filehash: str,
    size: int,
    *,
    token_header: str,
    dest_root: str,
    timeout_seconds: float,
    compression: CompressionType = CompressionType.UNCOMPRESSED,
) -> None:
    """Fetch one CAS blob from a node and atomically write it.

    Issues ``GET {base_url}/casblob/{filehash}?size={size}`` with the
    capability token in the ``X-Asset-Token`` header. ``filehash`` and
    ``size`` are the blob's *canonical* (uncompressed) identity (from the
    manifest); ``compression`` is the encoding the node serves it in (also
    from the manifest). When compressed, the received bytes are
    decompressed back to canonical before :func:`cas_write` sha256-verifies
    them against ``filehash`` and writes them — so the local cache always
    holds uncompressed blobs and the hash check still validates content.
    One attempt only; the caller owns concurrency and retry. Raises
    :class:`CasDownloadError` on a non-200 response, a decompress failure,
    or a verify failure.
    """
    url = f'{base_url}/casblob/{filehash}?size={size}'
    response = pool.request(
        'GET',
        url,
        headers={'X-Asset-Token': token_header},
        timeout=urllib3.util.Timeout(total=timeout_seconds),
    )
    if response.status != 200:
        raise CasDownloadError(
            f'casblob GET for {filehash} failed: HTTP {response.status}.'
        )
    data = response.data
    if compression is not CompressionType.UNCOMPRESSED:
        try:
            data = decompress_for_type(data, compression)
        except Exception as exc:
            raise CasDownloadError(
                f'casblob decompress for {filehash} failed: {exc}'
            ) from exc
    cas_write(dest_root, filehash, data)
