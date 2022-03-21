# Released under the MIT License. See LICENSE for details.
#
"""Message related tools functionality."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import TYPE_CHECKING

from efrotools.code import format_yapf_str

if TYPE_CHECKING:
    from typing import Optional


def standard_message_sender_gen_pcommand(
    projroot: Path,
    basename: str,
    source_module: str,
    enable_sync_sends: bool,
    enable_async_sends: bool,
    get_protocol_call: str = 'get_protocol',
    embedded: bool = False,
) -> None:
    """Used by pcommands taking a single filename argument."""
    # pylint: disable=too-many-locals
    import efro.message
    from efro.terminal import Clr
    from efro.error import CleanError

    if len(sys.argv) != 3:
        raise CleanError('Expected 1 arg: out-path.')
    dst = sys.argv[2]

    # Use wrapping-friendly form for long call names.
    get_protocol_import = (f'({get_protocol_call})' if
                           len(get_protocol_call) >= 14 else get_protocol_call)

    # In embedded situations we have to pass different code to import
    # the protocol at build time than we do in our runtime code (where
    # there is only a dummy import for type-checking purposes)
    protocol_module_level_import_code: Optional[str]
    build_time_protocol_create_code: Optional[str]
    if embedded:
        protocol_module_level_import_code = (
            f'\n# Dummy import for type-checking purposes.\n'
            f'if bool(False):\n'
            f'    from {source_module} import {get_protocol_import}')
        protocol_create_code = f'protocol = {get_protocol_call}()'
        build_time_protocol_create_code = (
            f'from {source_module} import {get_protocol_import}\n'
            f'protocol = {get_protocol_call}()')
    else:
        protocol_module_level_import_code = None
        protocol_create_code = (
            f'from {source_module} import {get_protocol_import}\n'
            f'protocol = {get_protocol_call}()')
        build_time_protocol_create_code = None

    module_code = efro.message.create_sender_module(
        basename,
        protocol_create_code=protocol_create_code,
        protocol_module_level_import_code=protocol_module_level_import_code,
        build_time_protocol_create_code=build_time_protocol_create_code,
        enable_sync_sends=enable_sync_sends,
        enable_async_sends=enable_async_sends,
    )
    out = format_yapf_str(projroot, module_code)

    print(f'Meta-building {Clr.BLD}{dst}{Clr.RST}')
    Path(dst).parent.mkdir(parents=True, exist_ok=True)
    with open(dst, 'w', encoding='utf-8') as outfile:
        outfile.write(out)


def standard_message_receiver_gen_pcommand(
    projroot: Path,
    basename: str,
    source_module: str,
    is_async: bool,
    get_protocol_call: str = 'get_protocol',
    embedded: bool = False,
) -> None:
    """Used by pcommands generating efro.message receiver modules."""
    # pylint: disable=too-many-locals

    import efro.message
    from efro.terminal import Clr
    from efro.error import CleanError

    if len(sys.argv) != 3:
        raise CleanError('Expected 1 arg: out-path.')

    dst = sys.argv[2]

    # Use wrapping-friendly form for long call names.
    get_protocol_import = (f'({get_protocol_call})' if
                           len(get_protocol_call) >= 14 else get_protocol_call)

    # In embedded situations we have to pass different code to import
    # the protocol at build time than we do in our runtime code (where
    # there is only a dummy import for type-checking purposes)
    protocol_module_level_import_code: Optional[str]
    build_time_protocol_create_code: Optional[str]
    if embedded:
        protocol_module_level_import_code = (
            f'\n# Dummy import for type-checking purposes.\n'
            f'if bool(False):\n'
            f'    from {source_module} import {get_protocol_import}')
        protocol_create_code = f'protocol = {get_protocol_call}()'
        build_time_protocol_create_code = (
            f'from {source_module} import {get_protocol_import}\n'
            f'protocol = {get_protocol_call}()')
    else:
        protocol_module_level_import_code = None
        protocol_create_code = (
            f'from {source_module} import {get_protocol_import}\n'
            f'protocol = {get_protocol_call}()')
        build_time_protocol_create_code = None

    module_code = efro.message.create_receiver_module(
        basename,
        protocol_create_code=protocol_create_code,
        protocol_module_level_import_code=protocol_module_level_import_code,
        build_time_protocol_create_code=build_time_protocol_create_code,
        is_async=is_async,
    )

    out = format_yapf_str(projroot, module_code)

    print(f'Meta-building {Clr.BLD}{dst}{Clr.RST}')
    Path(dst).parent.mkdir(parents=True, exist_ok=True)
    with open(dst, 'w', encoding='utf-8') as outfile:
        outfile.write(out)
