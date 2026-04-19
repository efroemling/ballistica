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


#: Public halves of long-lived Ed25519 keypairs the master server uses
#: to sign static data that clients must verify offline — without any
#: network round trip to fetch a :class:`SecureDataChecker`. Compiled
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
class SecureDataChecker:
    """Verifies data as being signed by our master server."""

    # Time period this checker is valid for.
    starttime: Annotated[datetime.datetime, IOAttrs('s')]
    endtime: Annotated[datetime.datetime, IOAttrs('e')]

    # Current set of public keys.
    publickeys: Annotated[list[bytes], IOAttrs('k')]

    def check(self, data: bytes, signature: bytes) -> bool:
        """Verify data, returning True if successful.

        Uses the ballistica native ``_babase.verify_ed25519`` when
        available (inside the app binary). On contexts without it
        (server, pytest, tools scripts) falls back to the
        ``cryptography`` package, which those contexts already have.
        """
        now = utc_now()

        # Make sure we seem valid based on local time.
        if now < self.starttime:
            raise RuntimeError('SecureDataChecker starttime is in the future.')
        if now > self.endtime:
            raise RuntimeError('SecureDataChecker endtime is in the past.')

        # Try our keys from newest to oldest. Most stuff will be using
        # the newest key so this should be most efficient.
        try:
            # Only importable inside the ballistica app binary —
            # server and pytest contexts fall through to
            # ``cryptography`` below.
            import _babase  # type: ignore[import-not-found,unused-ignore]

            for key in reversed(self.publickeys):
                if _babase.verify_ed25519(
                    public_key=key, signature=signature, message=data
                ):
                    return True
            return False
        except ImportError:
            # Ballistica native module not present — fall back to the
            # cryptography package. Both server and test contexts have
            # it available via pip.
            from cryptography.hazmat.primitives.asymmetric import ed25519
            from cryptography.exceptions import InvalidSignature

            for key in reversed(self.publickeys):
                try:
                    publickey = ed25519.Ed25519PublicKey.from_public_bytes(key)
                    publickey.verify(signature, data)
                    return True
                except InvalidSignature:
                    continue
            return False
