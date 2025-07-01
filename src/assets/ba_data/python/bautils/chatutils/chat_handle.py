# Released under the MIT License. See LICENSE for details.
#
"""
A chat interpreter to manage chat related thingsand combining other utilities.
"""

from __future__ import annotations
from .cmd_manager import CommandManager


def filter_chat_message(msg: str, client_id: int) -> str | None:
    """Hook for accessing live chat messages."""

    cmd_filter = CommandManager.listen(msg, client_id)
    return cmd_filter
