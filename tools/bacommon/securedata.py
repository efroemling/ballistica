# Released under the MIT License. See LICENSE for details.
#
"""Functionality related to verifying server generated data.

.. warning::

  This is an internal api and subject to change at any time. Do not use
  it in mod code.
"""

import datetime
from dataclasses import dataclass
from typing import TYPE_CHECKING, Annotated

from efro.util import utc_now
from efro.dataclassio import ioprepped, IOAttrs

if TYPE_CHECKING:
    pass


#: Minimum ballistica-internal client build number known to support
#: cert-bearing verification via :meth:`Reader.check`.
#: Older clients only have the legacy ``check(data, signature)`` path
#: and would silently fail to verify ``(data, signature, cert)``
#: triples — server code must therefore skip the delegate-signed
#: path for clients reporting a build below this threshold.
#:
#: Bump in lockstep with the ballistica-internal release that ships
#: the matching client code. Tracks the build at the moment the cert
#: path was added; ratchets upward only when a protocol change
#: requires it.
MIN_CLIENT_BUILD_FOR_DELEGATE_VERIFY: int = 22843


#: Public halves of long-lived Ed25519 keypairs the master server uses
#: to sign static data that clients must verify offline — without any
#: network round trip to fetch a :class:`Reader`. Compiled
#: into the client binary, so a MITM cannot swap them.
#:
#: Multiple entries let us rotate: add the new key (as a second entry)
#: in a client release, wait for that release to propagate to the
#: installed base, switch the server to sign with the new key, then
#: later drop the old key in a subsequent client release. On verify,
#: a signature is considered valid if ANY listed key verifies it.
#:
#: The matching private halves live on the master server in svals
#: under ``static_data_private_key`` (current signing key). basn nodes
#: fetch the current private key from the master at startup over the
#: secure inter-node channel.
STATIC_DATA_PUBLIC_KEYS: tuple[bytes, ...] = (
    b'\x98\xc0\xb3{\xea\n\t\x0f\xfb\xcbN\x1c\x03A\xd7\xd6'
    b'd\x95{.\xdc\xda\x9b\xf6\xe0\x7f\x0bM\x84^\x15b',
)


@ioprepped
@dataclass
class CertPayload:
    """Unsigned content of a :class:`Cert`.

    Master signs the canonical JSON encoding of this; recipients
    re-decode after signature verification to access the fields.
    """

    #: Public half of the keypair this cert authorizes.
    publickey: Annotated[bytes, IOAttrs('k')]

    #: Validity window during which signatures made by the matching
    #: private key should be honored.
    starttime: Annotated[datetime.datetime, IOAttrs('s')]
    endtime: Annotated[datetime.datetime, IOAttrs('e')]

    #: Identifier of the delegate (e.g. basn node id) for accountability
    #: and debugging. Not used for verification.
    issuer: Annotated[str, IOAttrs('i')]


@ioprepped
@dataclass
class Cert:
    """Master-signed delegation certificate.

    Asserts that the public key embedded in :attr:`payload` is
    authorized to sign on the master's behalf for the validity window
    in the payload. Verifiable by anyone holding a current
    :class:`Reader` (server-side) or the static public
    keys baked into the client binary (client-side, once a future
    client version supports the cert path).

    Carries an opaque ``payload`` (canonical JSON of
    :class:`CertPayload`) plus the master signature over
    those bytes. Mirrors the
    ``InsecureDirective`` pattern — re-encoding the
    dataclass on every verify would risk canonicalization drift.
    """

    #: Canonical JSON encoding of :class:`CertPayload`. Signed
    #: as-is and re-decoded by recipients via
    #: :meth:`decoded_payload`.
    payload: Annotated[bytes, IOAttrs('p')]

    #: Signature of :attr:`payload` made with the master signing key.
    signature: Annotated[bytes, IOAttrs('s')]

    def decoded_payload(self) -> CertPayload:
        """Decode :attr:`payload` to a :class:`CertPayload`.

        Does not verify the signature. Callers are expected to be
        operating on a cert that's already been chain-verified via
        :meth:`Reader.check`.
        """
        from efro.dataclassio import dataclass_from_json

        return dataclass_from_json(CertPayload, self.payload.decode())


class Invalid(Exception):
    """Raised by :meth:`Reader.read` and :meth:`Writer.write` when an
    operation cannot complete safely.

    For ``read``: the archive bytes are malformed, the master
    signature does not validate, the cert is expired or signed by
    an unknown master, or the delegate signature does not match.

    For ``write``: the writer's cert is past its validity window
    and would produce a signed archive a verifier would refuse.

    ``str(exc)`` carries a short reason suitable for logging.
    """


@ioprepped
@dataclass
class Archive:
    """Self-contained signed payload — verifiable on its own.

    Produced by :meth:`Writer.write` (delegate-signed) or
    :func:`make_master_archive` (master-signed; ``cert`` is
    ``None``). Verified via :meth:`Reader.read`, which returns the
    payload bytes on success.

    Embed directly as a field on dataclassio messages and
    responses (``Annotated[Archive, IOAttrs('x')]``); dataclassio
    nests the bytes-typed fields into the outer JSON without the
    extra base64-of-base64 round trip a bytes-blob field would
    incur. For the rare case that genuinely needs bytes
    (filesystem storage, etc.), serialize explicitly with
    :func:`efro.dataclassio.dataclass_to_json`.

    Per-field IOAttrs short keys are stable; new optional fields
    get ``soft_default`` rather than reusing or renaming existing
    ones — same as anywhere else dataclassio types travel.
    """

    data: Annotated[bytes, IOAttrs('d')]
    signature: Annotated[bytes, IOAttrs('s')]
    cert: Annotated[Cert | None, IOAttrs('c', store_default=False)] = None


def make_master_archive(data: bytes, master_priv_bytes: bytes) -> Archive:
    """Pack data + a master-key signature into an :class:`Archive`.

    Server-only — clients do not have access to a master private
    key. Verifiers (with master public keys) accept the resulting
    archive via :meth:`Reader.read` exactly the same way they
    accept Writer-produced archives, except the master path
    carries no cert.

    ``master_priv_bytes`` is the raw 32-byte Ed25519 seed. On
    bamaster, prefer
    ``UniversalGlobals.secure_data_archive_master`` which sources
    the key from svals.
    """
    from cryptography.hazmat.primitives.asymmetric import ed25519

    sig = ed25519.Ed25519PrivateKey.from_private_bytes(master_priv_bytes).sign(
        data
    )
    return Archive(data=data, signature=sig, cert=None)


@ioprepped
@dataclass
class Writer:
    """Delegated signing capability.

    Issued by the master to a delegate (typically a basn node) over
    a secure channel. The delegate calls :meth:`write` on data and
    distributes the resulting archive bytes; recipients chain-verify
    and recover the original bytes via :meth:`Reader.read`.

    Sensitive: contains a private key. Never traverses untrusted
    channels and should not be persisted to disk.

    The top-level ``starttime`` / ``endtime`` mirror the cert's
    validity window for ergonomic refresh-decision code (see basn's
    ``_update_secure_data_signer``). They are NOT authoritative for
    verification — :attr:`cert` is.

    Servers must consult
    :data:`MIN_CLIENT_BUILD_FOR_DELEGATE_VERIFY` before sending
    delegate-signed archives to a client; clients below the
    threshold do not understand the cert path and would reject the
    archive.
    """

    starttime: Annotated[datetime.datetime, IOAttrs('s')]
    endtime: Annotated[datetime.datetime, IOAttrs('e')]

    #: Raw Ed25519 private key bytes.
    privatekey: Annotated[bytes, IOAttrs('k')]

    #: Master-signed cert authorizing the public counterpart of
    #: :attr:`privatekey`.
    cert: Annotated[Cert, IOAttrs('c')]

    def write(self, data: bytes) -> Archive:
        """Sign ``data`` and return an :class:`Archive`.

        The archive carries the signature + the writer's cert;
        recipients pass it to :meth:`Reader.read` to verify and
        recover the original bytes.

        Raises :class:`Invalid` if the writer's cert has expired —
        an archive produced past expiry would be rejected by every
        verifier, so we fail fast at write time rather than at
        verify time.
        """
        from cryptography.hazmat.primitives.asymmetric import ed25519

        if utc_now() > self.endtime:
            raise Invalid('writer cert is expired')
        sig = ed25519.Ed25519PrivateKey.from_private_bytes(
            self.privatekey
        ).sign(data)
        return Archive(data=data, signature=sig, cert=self.cert)

    def sign(self, data: bytes) -> bytes:
        """Low-level: produce a raw signature over ``data``.

        Most callers should use :meth:`write` instead — it returns
        a self-contained archive that includes the signature, the
        cert, and the data, all verifiable in a single
        :meth:`Reader.read` call.
        """
        from cryptography.hazmat.primitives.asymmetric import ed25519

        return ed25519.Ed25519PrivateKey.from_private_bytes(
            self.privatekey
        ).sign(data)


@ioprepped
@dataclass
class Reader:
    """Verifies data as being signed by our master server."""

    # Time period this checker is valid for.
    starttime: Annotated[datetime.datetime, IOAttrs('s')]
    endtime: Annotated[datetime.datetime, IOAttrs('e')]

    # Current set of public keys.
    publickeys: Annotated[list[bytes], IOAttrs('k')]

    def read(self, archive: Archive) -> bytes:
        """Verify ``archive`` and return its data on success.

        ``archive`` is the :class:`Archive` produced by
        :meth:`Writer.write` or :func:`make_master_archive`. Routes
        automatically: an archive without a cert is verified
        directly against this reader's master public keys; an
        archive with a cert is chain-verified (cert against master
        keys, then data against the cert's delegate pubkey).

        Raises :class:`Invalid` for any failure — expired/forged
        cert, bad signature.
        """
        if not self.check(archive.data, archive.signature, archive.cert):
            raise Invalid(
                'cert chain or signature did not verify'
                if archive.cert is not None
                else 'signature did not verify'
            )
        return archive.data

    def check(
        self,
        data: bytes,
        signature: bytes,
        cert: Cert | None = None,
    ) -> bool:
        """Verify data, returning True if successful.

        When ``cert`` is ``None`` (the default), ``signature`` is
        verified directly against the master public keys — used for
        anything bamaster signed itself.

        When ``cert`` is given, the chain is verified end-to-end:

        1. The cert's signature must validate against a master public
           key (proving the master authorized this delegate).
        2. The cert's validity window must include now.
        3. ``signature`` must then validate against the delegate
           public key embedded in the cert.

        Used for data signed by a delegate (typically a basn node)
        acting on the master's behalf. Older clients that predate the
        delegate-signing rollout will only ever be sent ``cert=None``
        triples; see ``bacommon/securedata.py`` design notes for the
        rollout discipline.

        Uses the ballistica native ``_babase.verify_ed25519`` when
        available (inside the app binary). On contexts without it
        (server, pytest, tools scripts) falls back to the
        ``cryptography`` package, which those contexts already have.
        """
        now = utc_now()

        # Make sure we seem valid based on local time.
        if now < self.starttime:
            raise RuntimeError('Reader starttime is in the future.')
        if now > self.endtime:
            raise RuntimeError('Reader endtime is in the past.')

        if cert is None:
            return self._verify_against_master_keys(data, signature)

        # Delegate path: prove the cert is master-signed, prove it's
        # in its validity window, then verify the data signature
        # against the delegate pubkey it carries.
        if not self._verify_against_master_keys(cert.payload, cert.signature):
            return False
        try:
            payload = cert.decoded_payload()
        except Exception:  # pylint: disable=broad-except
            # Malformed payload bytes — treat as verification failure
            # rather than propagating; callers expect bool.
            return False
        if now < payload.starttime or now > payload.endtime:
            return False
        return _verify_ed25519(payload.publickey, data, signature)

    def _verify_against_master_keys(
        self, data: bytes, signature: bytes
    ) -> bool:
        """Try each master public key newest-first; True on first hit."""
        # Newest key is most likely to be the active signer, so this
        # short-circuits common-case cost.
        for key in reversed(self.publickeys):
            if _verify_ed25519(key, data, signature):
                return True
        return False


def _verify_ed25519(publickey: bytes, data: bytes, signature: bytes) -> bool:
    """Single-key Ed25519 verify. ``True`` if signature validates."""
    try:
        # Only importable inside the ballistica app binary — server
        # and pytest contexts fall through to ``cryptography`` below.
        import _babase  # type: ignore[import-not-found,unused-ignore]

        return bool(
            _babase.verify_ed25519(
                public_key=publickey, signature=signature, message=data
            )
        )
    except ImportError:
        from cryptography.hazmat.primitives.asymmetric import ed25519
        from cryptography.exceptions import InvalidSignature

        try:
            ed25519.Ed25519PublicKey.from_public_bytes(publickey).verify(
                signature, data
            )
            return True
        except InvalidSignature:
            return False
