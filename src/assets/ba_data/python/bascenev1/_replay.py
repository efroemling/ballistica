# Released under the MIT License. See LICENSE for details.
#
"""Functionality related to replay playback."""

import logging
import asyncio

import babase

import _bascenev1

from bascenev1._net import resolve_asset_packages_with_dialog

netlog = logging.getLogger('ba.net')

# The in-flight pre-playback task, if any (see new_replay_session's
# latest-wins behavior).
_g_preplay_task: asyncio.Task[None] | None = None


async def prepare_replay(file_name: str) -> bool:
    """Resolve a replay's required asset-packages before playback.

    The requirements are read from the replay file's header (no stream
    decompression) and anything not present locally is downloaded, with
    a cancelable progress dialog. Returns True when the replay is ready
    to play, or False if the user cancelled or a download failed.

    Safe to call with the launching UI still visible: on a False result
    the caller should leave that UI in place (a cancel then just closes
    the dialog and returns the user to where they were).

    (internal)
    """
    # None => unreadable/incompatible file; let the launch surface it.
    # Empty => a pre-table replay with nothing to resolve.
    packages = _bascenev1.get_replay_asset_packages(file_name)
    if packages:
        netlog.debug(
            'Replay %s requires %d asset-package(s); resolving.',
            file_name,
            len(packages),
        )
        if not await resolve_asset_packages_with_dialog(
            packages, task=asyncio.current_task(), context=f'replay {file_name}'
        ):
            return False
    return True


def launch_replay(file_name: str) -> None:
    """Immediately start a session playing back a replay file.

    Assumes the replay's required asset-packages are already present
    locally; use :func:`new_replay_session` (or :func:`prepare_replay`)
    to resolve/download them first. This is the raw launch that the
    prep path hands off to.

    (internal)
    """
    _bascenev1.new_replay_session(file_name)


def new_replay_session(file_name: str) -> None:
    """Prepare and play a replay: resolve content, then start playback.

    A one-call convenience combining :func:`prepare_replay` and
    :func:`launch_replay` -- content not present locally is downloaded
    (with a cancelable dialog) before playback begins, mirroring
    :func:`connect_to_party`'s pre-join content prep. A replay whose
    content is already local (the common case) or which predates
    asset-package tables starts immediately.

    (internal)
    """
    assert babase.in_logic_thread()

    # Latest-wins: a new request cancels any pre-playback prep still in
    # flight.
    global _g_preplay_task  # pylint: disable=global-statement
    if _g_preplay_task is not None and not _g_preplay_task.done():
        _g_preplay_task.cancel()
    _g_preplay_task = None

    babase.app.create_async_task(
        _preplay_and_launch(file_name),
        name=f'new_replay_session {file_name}',
    )


async def _preplay_and_launch(file_name: str) -> None:
    """Content prep + the actual replay launch."""
    global _g_preplay_task  # pylint: disable=global-statement
    task = asyncio.current_task()
    _g_preplay_task = task
    try:
        if await prepare_replay(file_name):
            launch_replay(file_name)
    finally:
        if _g_preplay_task is task:
            _g_preplay_task = None
