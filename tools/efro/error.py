# Released under the MIT License. See LICENSE for details.
#
"""Common errors and related functionality."""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass


class CleanError(Exception):
    """An error that should be presented to the user as a simple message.

    These errors should be completely self-explanatory, to the point where
    a traceback or other context would not be useful.

    A CleanError with no message can be used to inform a script to fail
    without printing any message.

    This should generally be limited to errors that will *always* be
    presented to the user (such as those in high level tool code).
    Exceptions that may be caught and handled by other code should use
    more descriptive exception types.
    """

    def pretty_print(self, flush: bool = False) -> None:
        """Print the error to stdout, using red colored output if available.

        If the error has an empty message, prints nothing (not even a newline).
        """
        from efro.terminal import Clr
        errstr = str(self)
        if errstr:
            print(f'{Clr.SRED}{errstr}{Clr.RST}', flush=flush)


class CommunicationError(Exception):
    """A communication related error has occurred.

    This covers anything network-related going wrong in the sending
    of data or receiving of a response. This error does not imply
    that data was not received on the other end; only that a full
    response round trip was not completed.

    These errors should be gracefully handled whenever possible, as
    occasional network outages are generally unavoidable.
    """


class RemoteError(Exception):
    """An error occurred on the other end of some connection.

    This occurs when communication succeeds but another type of error
    occurs remotely. The error string can consist of a remote stack
    trace or a simple message depending on the context.

    Depending on the situation, more specific error types such as CleanError
    may be raised due to the remote error, so this one is considered somewhat
    of a catch-all.
    """

    def __str__(self) -> str:
        s = ''.join(str(arg) for arg in self.args)
        return f'Remote Exception Follows:\n{s}'
