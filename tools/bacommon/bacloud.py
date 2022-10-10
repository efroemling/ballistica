# Released under the MIT License. See LICENSE for details.
#
"""Functionality related to the bacloud tool."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Annotated

from efro.dataclassio import ioprepped, IOAttrs

if TYPE_CHECKING:
    pass

# Version is sent to the master-server with all commands. Can be incremented
# if we need to change behavior server-side to go along with client changes.
BACLOUD_VERSION = 8


@ioprepped
@dataclass
class RequestData:
    """Request sent to bacloud server."""

    command: Annotated[str, IOAttrs('c')]
    token: Annotated[str | None, IOAttrs('t')]
    payload: Annotated[dict, IOAttrs('p')]
    tzoffset: Annotated[float, IOAttrs('z')]
    isatty: Annotated[bool, IOAttrs('y')]


@ioprepped
@dataclass
class ResponseData:
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
      deletes: If present, file paths that should be deleted on the client.
      downloads_inline: If present, pathnames mapped to base64 gzipped data to
        be written to the client. This should only be used for relatively
        small files as they are all included inline as part of the response.
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
    message: Annotated[str | None, IOAttrs('m', store_default=False)] = None
    message_end: Annotated[str, IOAttrs('m_end', store_default=False)] = '\n'
    error: Annotated[str | None, IOAttrs('e', store_default=False)] = None
    delay_seconds: Annotated[float, IOAttrs('d', store_default=False)] = 0.0
    login: Annotated[str | None, IOAttrs('l', store_default=False)] = None
    logout: Annotated[bool, IOAttrs('lo', store_default=False)] = False
    dir_manifest: Annotated[
        str | None, IOAttrs('man', store_default=False)
    ] = None
    uploads: Annotated[
        tuple[list[str], str, dict] | None, IOAttrs('u', store_default=False)
    ] = None
    uploads_inline: Annotated[
        list[str] | None, IOAttrs('uinl', store_default=False)
    ] = None
    deletes: Annotated[
        list[str] | None, IOAttrs('dlt', store_default=False)
    ] = None
    downloads_inline: Annotated[
        dict[str, str] | None, IOAttrs('dinl', store_default=False)
    ] = None
    dir_prune_empty: Annotated[
        str | None, IOAttrs('dpe', store_default=False)
    ] = None
    open_url: Annotated[str | None, IOAttrs('url', store_default=False)] = None
    input_prompt: Annotated[
        tuple[str, bool] | None, IOAttrs('inp', store_default=False)
    ] = None
    end_message: Annotated[
        str | None, IOAttrs('em', store_default=False)
    ] = None
    end_message_end: Annotated[str, IOAttrs('eme', store_default=False)] = '\n'
    end_command: Annotated[
        tuple[str, dict] | None, IOAttrs('ec', store_default=False)
    ] = None
