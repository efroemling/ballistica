# Released under the MIT License. See LICENSE for details.
#
"""Operate on large sets of files efficiently."""

from __future__ import annotations

import logging
from collections import deque
from typing import TYPE_CHECKING
from threading import Condition, Thread
import os

if TYPE_CHECKING:
    from typing import Iterable, Callable


class _FileBatchesRun:
    def __init__(
        self,
        paths: list[str],
        batch_size: int,
        file_filter: Callable[[str], bool] | None,
        include_mac_packages: bool = False,
    ) -> None:
        self.condition = Condition()
        self.paths = paths
        self.batches = deque[list[str]]()
        self.batch_size = batch_size
        self.done = False
        self.errored = False
        self.file_filter = file_filter
        self.batch_buffer_size = 5
        self._pending_batch: list[str] = []
        self._include_mac_packages = include_mac_packages

        if self._include_mac_packages:
            # pylint: disable=useless-suppression
            # pylint: disable=no-name-in-module, import-error
            # noinspection PyUnresolvedReferences
            from Cocoa import NSWorkspace  # pyright: ignore

            self._shared_nsworkspace = NSWorkspace.sharedWorkspace()
            # pylint: enable=useless-suppression
        else:
            self._shared_nsworkspace = None

    def _submit_pending_batch(self) -> None:
        assert self._pending_batch

        # Wait until there's room on the list (or we've been marked done),
        # stuff our new results in, and inform any listeners that it has
        # changed.
        with self.condition:
            self.condition.wait_for(
                lambda: len(self.batches) < self.batch_buffer_size or self.done
            )
            self.batches.append(self._pending_batch)
            self._pending_batch = []
            self.condition.notify()

    def _possibly_add_to_pending_batch(self, path: str) -> None:
        try:
            if self.file_filter is None or self.file_filter(path):
                self._pending_batch.append(path)
                if len(self._pending_batch) >= self.batch_size:
                    self._submit_pending_batch()
        except Exception:
            # FIXME: we should translate this into failing overall...
            logging.exception('Error in file_filter')

    def bg_thread(self) -> None:
        """Add batches in the bg thread."""
        # pylint: disable=too-many-nested-blocks

        # Build batches and push them when they're big enough.
        for path in self.paths:
            if os.path.isfile(path):
                self._possibly_add_to_pending_batch(path)
            elif os.path.isdir(path):
                # From os.walk docs: we can prune dirs in-place when
                # running in top-down mode. We can use this to skip
                # diving into mac packages.
                for root, dirs, fnames in os.walk(path, topdown=True):
                    # If we find dirs that are actually mac packages, pull
                    # them out of the dir list we'll dive into and pass
                    # them directly to our batch for processing.
                    if self._include_mac_packages:
                        assert self._shared_nsworkspace is not None
                        for dirname in list(dirs):
                            fullpath = os.path.join(root, dirname)
                            if self._shared_nsworkspace.isFilePackageAtPath_(
                                fullpath
                            ):
                                dirs.remove(dirname)
                                self._possibly_add_to_pending_batch(fullpath)

                    for fname in fnames:
                        fullpath = os.path.join(root, fname)
                        self._possibly_add_to_pending_batch(fullpath)

        if self._pending_batch:
            self._submit_pending_batch()

        # Tell the world we're done.
        with self.condition:
            self.done = True
            self.condition.notify()


def file_batches(
    paths: list[str],
    batch_size: int = 1,
    file_filter: Callable[[str], bool] | None = None,
    include_mac_packages: bool = False,
) -> Iterable[list[str]]:
    """Efficiently yield batches of files to operate on.

    Accepts a list of paths which can be files or directories to be recursed.
    The batch lists are buffered in a background thread so time-consuming
    synchronous operations on the returned batches will not slow the gather.
    """

    run = _FileBatchesRun(
        paths=paths,
        batch_size=batch_size,
        file_filter=file_filter,
        include_mac_packages=include_mac_packages,
    )

    # Spin up a bg thread to feed us batches.
    thread = Thread(target=run.bg_thread)
    thread.start()

    # Now spin waiting for new batches to come in or completion/errors.
    while True:
        with run.condition:
            run.condition.wait_for(
                lambda: run.done or run.errored or run.batches
            )
            try:
                if run.errored:
                    raise RuntimeError('BG batch run errored.')
                while run.batches:
                    yield run.batches.popleft()
                if run.done:
                    break
            except GeneratorExit:
                # Lets the bg thread know to abort.
                run.done = True
                raise
            finally:
                run.condition.notify()
