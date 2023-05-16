# Released under the MIT License. See LICENSE for details.
#
"""A system for sanity testing parallel build isolation."""

from __future__ import annotations

from typing import TYPE_CHECKING
import os


if TYPE_CHECKING:
    from typing import Any

LOCK_DIR_PATH = '.cache/buildlocks'


class BuildLock:
    """Tries to ensure a build is not getting stomped on/etc."""

    def __init__(self, name: str) -> None:
        self.name = name
        if '/' in name or '\\' in name:
            raise ValueError(f"Illegal BuildLock name: '{name}'.")
        self.lockpath = os.path.join(LOCK_DIR_PATH, name)

    def __enter__(self) -> None:
        if not os.path.exists(LOCK_DIR_PATH):
            os.makedirs(LOCK_DIR_PATH, exist_ok=True)

        # Note: we aren't doing anything super accurate/atomic here. This
        # is more intended as a gross check to make noise on clearly broken
        # build logic; it isn't important that it catch every corner case
        # perfectly.
        if os.path.exists(self.lockpath):
            raise RuntimeError(
                f"Build-lock: lock '{self.name}' exists."
                ' This probably means multiple builds'
                ' are running at once that should not be.'
            )
        with open(self.lockpath, 'w', encoding='utf-8') as outfile:
            outfile.write('')

    def __exit__(self, exc_type: Any, exc_value: Any, traceback: Any) -> Any:
        if not os.path.exists(self.lockpath):
            raise RuntimeError(
                f"Build-lock: lock '{self.name}' not found at tear-down."
            )
        os.unlink(self.lockpath)
