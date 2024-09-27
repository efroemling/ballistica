# Released under the MIT License. See LICENSE for details.
#
"""Functionality for sending and responding to messages.
Supports static typing for message types and possible return types.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from efro.message._protocol import MessageProtocol

if TYPE_CHECKING:
    pass


def create_sender_module(
    basename: str,
    protocol_create_code: str,
    enable_sync_sends: bool,
    enable_async_sends: bool,
    *,
    private: bool = False,
    protocol_module_level_import_code: str | None = None,
    build_time_protocol_create_code: str | None = None,
) -> str:
    """Create a Python module defining a MessageSender subclass.

    This class is primarily for type checking and will contain overrides
    for the varieties of send calls for message/response types defined
    in the protocol.

    Code passed for 'protocol_create_code' should import necessary
    modules and assign an instance of the Protocol to a 'protocol'
    variable.

    Class names are based on basename; a basename 'FooSender' will
    result in classes FooSender and BoundFooSender.

    If 'private' is True, class-names will be prefixed with an '_'.

    Note: output code may have long lines and should generally be run
    through a formatter. We should perhaps move this functionality to
    efrotools so we can include that functionality inline.
    """
    protocol = _protocol_from_code(
        build_time_protocol_create_code
        if build_time_protocol_create_code is not None
        else protocol_create_code
    )
    return protocol.do_create_sender_module(
        basename=basename,
        protocol_create_code=protocol_create_code,
        enable_sync_sends=enable_sync_sends,
        enable_async_sends=enable_async_sends,
        private=private,
        protocol_module_level_import_code=protocol_module_level_import_code,
    )


def create_receiver_module(
    basename: str,
    protocol_create_code: str,
    is_async: bool,
    *,
    private: bool = False,
    protocol_module_level_import_code: str | None = None,
    build_time_protocol_create_code: str | None = None,
) -> str:
    """ "Create a Python module defining a MessageReceiver subclass.

    This class is primarily for type checking and will contain overrides
    for the register method for message/response types defined in
    the protocol.

    Class names are based on basename; a basename 'FooReceiver' will
    result in FooReceiver and BoundFooReceiver.

    If 'is_async' is True, handle_raw_message() will be an async method
    and the @handler decorator will expect async methods.

    If 'private' is True, class-names will be prefixed with an '_'.

    Note that line lengths are not clipped, so output may need to be
    run through a formatter to prevent lint warnings about excessive
    line lengths.
    """
    protocol = _protocol_from_code(
        build_time_protocol_create_code
        if build_time_protocol_create_code is not None
        else protocol_create_code
    )
    return protocol.do_create_receiver_module(
        basename=basename,
        protocol_create_code=protocol_create_code,
        is_async=is_async,
        private=private,
        protocol_module_level_import_code=protocol_module_level_import_code,
    )


def _protocol_from_code(protocol_create_code: str) -> MessageProtocol:
    env: dict = {}
    exec(protocol_create_code, env)  # pylint: disable=exec-used
    protocol = env.get('protocol')
    if not isinstance(protocol, MessageProtocol):
        raise RuntimeError(
            f'protocol_create_code yielded'
            f' a {type(protocol)}; expected a MessageProtocol instance.'
        )
    return protocol
