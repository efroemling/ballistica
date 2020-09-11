# Released under the MIT License. See LICENSE for details.
#
"""Functionality for dealing with errors."""
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
