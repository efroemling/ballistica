# Released under the MIT License. See LICENSE for details.
#
"""A chat interpreter to manage chat related things."""

from __future__ import annotations

import babase as ba


class IncorrectUsageError(Exception):
    """Error expressing incorrect usage of command."""


class NoArgumentsProvidedError(Exception):
    """Error expressing no argyments are provided in command."""


class IncorrectArgumentsError(Exception):
    """Error expressing incorrect arguemts are provided in command."""


class InvalidClientIDError(Exception):
    """Error expressing invalid client id is provided."""


class ActorNotFoundError(ba.ActivityNotFoundError):
    """Error expressing no actor found in command context"""
