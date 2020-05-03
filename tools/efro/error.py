# Copyright (c) 2011-2020 Eric Froemling
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
# -----------------------------------------------------------------------------
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
