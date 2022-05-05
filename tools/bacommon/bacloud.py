# Released under the MIT License. See LICENSE for details.
#
"""Functionality related to the bacloud tool."""

from __future__ import annotations
from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional

from efro.dataclassio import ioprepped

if TYPE_CHECKING:
    pass


@ioprepped
@dataclass
class Response:
    # noinspection PyUnresolvedReferences
    """Response sent from the bacloud server to the client.

    Attributes:
      message: If present, client should print this message before any other
        response processing (including error handling) occurs.
      message_end: end arg for message print() call.
      error: If present, client should abort with this error message.
      delay_seconds: How long to wait before proceeding with remaining
        response (can be useful when waiting for server progress in a loop).
      login: If present, a token that should be stored client-side and passed
        with subsequent commands.
      logout: If True, any existing client-side token should be discarded.
      dir_manifest: If present, client should generate a manifest of this dir.
        It should be added to end_command args as 'manifest'.
      uploads: If present, client should upload the requested files (arg1)
        individually to a server command (arg2) with provided args (arg3).
      uploads_inline: If present, a list of pathnames that should be base64
        gzipped and uploaded to an 'uploads_inline' dict in end_command args.
        This should be limited to relatively small files.
      downloads_inline: If present, pathnames mapped to base64 gzipped data to
        be written to the client. This should only be used for relatively
        small files as they are all included inline as part of the response.
      deletes: If present, file paths that should be deleted on the client.
      dir_prune_empty: If present, all empty dirs under this one should be
        removed.
      open_url: If present, url to display to the user.
      input_prompt: If present, a line of input is read and placed into
        end_command args as 'input'. The first value is the prompt printed
        before reading and the second is whether it should be read as a
        password (without echoing to the terminal).
      end_message: If present, a message that should be printed after all other
        response processing is done.
      end_message_end: end arg for end_message print() call.
      end_command: If present, this command is run with these args at the end
        of response processing.
    """
    message: Optional[str] = None
    message_end: str = '\n'
    error: Optional[str] = None
    delay_seconds: float = 0.0
    login: Optional[str] = None
    logout: bool = False
    dir_manifest: Optional[str] = None
    uploads: Optional[tuple[list[str], str, dict]] = None
    uploads_inline: Optional[list[str]] = None
    downloads_inline: Optional[dict[str, str]] = None
    deletes: Optional[list[str]] = None
    dir_prune_empty: Optional[str] = None
    open_url: Optional[str] = None
    input_prompt: Optional[tuple[str, bool]] = None
    end_message: Optional[str] = None
    end_message_end: str = '\n'
    end_command: Optional[tuple[str, dict]] = None
