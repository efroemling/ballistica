# Released under the MIT License. See LICENSE for details.
#
"""Various utility calls for interacting with baenv."""

# This code runs in the logic thread to bootstrap ballistica.

from __future__ import annotations

from typing import TYPE_CHECKING
import sys

if TYPE_CHECKING:
    import baenv


def prepend_sys_path(path: str) -> None:
    """Simply add a path to sys paths at the beginning."""
    sys.path.insert(0, path)


def import_baenv_and_run_configure(
    config_dir: str | None,
    data_dir: str | None,
    user_python_dir: str | None,
    contains_python_dist: bool,
) -> None:
    """Import baenv and run its configure method."""
    import baenv

    baenv.configure(
        config_dir=config_dir,
        data_dir=data_dir,
        user_python_dir=user_python_dir,
        contains_python_dist=contains_python_dist,
    )


def get_env_config() -> baenv.EnvConfig:
    """Import baenv and get the config."""
    import baenv

    return baenv.get_config()
