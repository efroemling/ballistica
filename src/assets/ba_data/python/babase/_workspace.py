# Released under the MIT License. See LICENSE for details.
#
"""Workspace related functionality."""

from __future__ import annotations

import os
import sys
import logging
from pathlib import Path
from threading import Thread
from functools import partial
from typing import TYPE_CHECKING

from efro.error import CleanError
import _babase
import bacommon.cloud
from bacommon.transfer import DirectoryManifest

if TYPE_CHECKING:
    from typing import Callable

    import babase


class WorkspaceSubsystem:
    """Subsystem for workspace handling in the app.

    Category: **App Classes**

    Access the single shared instance of this class at `ba.app.workspaces`.
    """

    def __init__(self) -> None:
        pass

    def set_active_workspace(
        self,
        account: babase.AccountV2Handle,
        workspaceid: str,
        workspacename: str,
        on_completed: Callable[[], None],
    ) -> None:
        """(internal)"""

        # Do our work in a background thread so we don't destroy
        # interactivity.
        Thread(
            target=lambda: self._set_active_workspace_bg(
                account=account,
                workspaceid=workspaceid,
                workspacename=workspacename,
                on_completed=on_completed,
            ),
            daemon=True,
        ).start()

    def _errmsg(self, msg: babase.Lstr) -> None:
        _babase.screenmessage(msg, color=(1, 0, 0))
        _babase.getsimplesound('error').play()

    def _successmsg(self, msg: babase.Lstr) -> None:
        _babase.screenmessage(msg, color=(0, 1, 0))
        _babase.getsimplesound('gunCocking').play()

    def _set_active_workspace_bg(
        self,
        account: babase.AccountV2Handle,
        workspaceid: str,
        workspacename: str,
        on_completed: Callable[[], None],
    ) -> None:
        from babase._language import Lstr

        class _SkipSyncError(RuntimeError):
            pass

        plus = _babase.app.plus
        assert plus is not None

        set_path = True
        wspath = Path(
            _babase.get_volatile_data_directory(), 'workspaces', workspaceid
        )
        try:
            # If it seems we're offline, don't even attempt a sync,
            # but allow using the previous synced state.
            # (is this a good idea?)
            if not plus.cloud.is_connected():
                raise _SkipSyncError()

            manifest = DirectoryManifest.create_from_disk(wspath)

            # FIXME: Should implement a way to pass account credentials in
            # from the logic thread.
            state = bacommon.cloud.WorkspaceFetchState(manifest=manifest)

            while True:
                with account:
                    response = plus.cloud.send_message(
                        bacommon.cloud.WorkspaceFetchMessage(
                            workspaceid=workspaceid, state=state
                        )
                    )
                state = response.state
                self._handle_deletes(
                    workspace_dir=wspath, deletes=response.deletes
                )
                self._handle_downloads_inline(
                    workspace_dir=wspath,
                    downloads_inline=response.downloads_inline,
                )
                if response.done:
                    # Server only deals in files; let's clean up any
                    # leftover empty dirs after the dust has cleared.
                    self._handle_dir_prune_empty(str(wspath))
                    break
                state.iteration += 1

            _babase.pushcall(
                partial(
                    self._successmsg,
                    Lstr(
                        resource='activatedText',
                        subs=[('${THING}', workspacename)],
                    ),
                ),
                from_other_thread=True,
            )

        except _SkipSyncError:
            _babase.pushcall(
                partial(
                    self._errmsg,
                    Lstr(
                        resource='workspaceSyncReuseText',
                        subs=[('${WORKSPACE}', workspacename)],
                    ),
                ),
                from_other_thread=True,
            )

        except CleanError as exc:
            # Avoid reusing existing if we fail in the middle; could
            # be in wonky state.
            set_path = False
            _babase.pushcall(
                partial(self._errmsg, Lstr(value=str(exc))),
                from_other_thread=True,
            )
        except Exception:
            # Ditto.
            set_path = False
            logging.exception("Error syncing workspace '%s'.", workspacename)
            _babase.pushcall(
                partial(
                    self._errmsg,
                    Lstr(
                        resource='workspaceSyncErrorText',
                        subs=[('${WORKSPACE}', workspacename)],
                    ),
                ),
                from_other_thread=True,
            )

        if set_path and wspath.is_dir():
            # Add to Python paths and also to list of stuff to be scanned
            # for meta tags.
            sys.path.insert(0, str(wspath))
            _babase.app.meta.extra_scan_dirs.append(str(wspath))

        # Job's done!
        _babase.pushcall(on_completed, from_other_thread=True)

    def _handle_deletes(self, workspace_dir: Path, deletes: list[str]) -> None:
        """Handle file deletes."""
        for fname in deletes:
            fname = os.path.join(workspace_dir, fname)
            # Server shouldn't be sending us dir paths here.
            assert not os.path.isdir(fname)
            os.unlink(fname)

    def _handle_downloads_inline(
        self,
        workspace_dir: Path,
        downloads_inline: dict[str, bytes],
    ) -> None:
        """Handle inline file data to be saved to the client."""
        for fname, fdata in downloads_inline.items():
            fname = os.path.join(workspace_dir, fname)
            # If there's a directory where we want our file to go, clear it
            # out first. File deletes should have run before this so
            # everything under it should be empty and thus killable via rmdir.
            if os.path.isdir(fname):
                for basename, dirnames, _fn in os.walk(fname, topdown=False):
                    for dirname in dirnames:
                        os.rmdir(os.path.join(basename, dirname))
                os.rmdir(fname)

            dirname = os.path.dirname(fname)
            if dirname:
                os.makedirs(dirname, exist_ok=True)
            with open(fname, 'wb') as outfile:
                outfile.write(fdata)

    def _handle_dir_prune_empty(self, prunedir: str) -> None:
        """Handle pruning empty directories."""
        # Walk the tree bottom-up so we can properly kill recursive empty dirs.
        for basename, dirnames, filenames in os.walk(prunedir, topdown=False):
            # It seems that child dirs we kill during the walk are still
            # listed when the parent dir is visited, so lets make sure
            # to only acknowledge still-existing ones.
            dirnames = [
                d for d in dirnames if os.path.exists(os.path.join(basename, d))
            ]
            if not dirnames and not filenames and basename != prunedir:
                os.rmdir(basename)
