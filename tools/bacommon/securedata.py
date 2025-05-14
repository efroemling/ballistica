# Released under the MIT License. See LICENSE for details.
#
"""Functionality related to verifying ballistica server generated data."""

import datetime
from dataclasses import dataclass
from typing import TYPE_CHECKING, Annotated

from efro.util import utc_now
from efro.dataclassio import ioprepped, IOAttrs

if TYPE_CHECKING:
    pass


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

        Note that this call imports and uses the cryptography module and
        can be slow; it generally should be done in a background thread
        or on a server.
        """
        from cryptography.hazmat.primitives.asymmetric import ed25519
        from cryptography.exceptions import InvalidSignature

        now = utc_now()

        # Make sure we seem valid based on local time.
        if now < self.starttime:
            raise RuntimeError('SecureDataChecker starttime is in the future.')
        if now > self.endtime:
            raise RuntimeError('SecureDataChecker endtime is in the past.')

        # Try our keys from newest to oldest. Most stuff will be using
        # the newest key so this should be most efficient.
        for key in reversed(self.publickeys):
            try:
                publickey = ed25519.Ed25519PublicKey.from_public_bytes(key)
                publickey.verify(signature, data)
                return True
            except InvalidSignature:
                pass

        return False
