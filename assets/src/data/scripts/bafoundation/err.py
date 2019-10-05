# Synced from bamaster.
# EFRO_SYNC_HASH=324606719817436157254454259763962378663
#
"""Error related functionality shared between all ba components."""

# Hmmmm - need to give this exception structure some thought...


class CommunicationError(Exception):
    """A communication-related error occurred."""


class RemoteError(Exception):
    """An error occurred on the other end of some connection."""

    def __str__(self) -> str:
        s = ''.join(str(arg) for arg in self.args)  # pylint: disable=E1133
        return f'Remote Exception Follows:\n{s}'
