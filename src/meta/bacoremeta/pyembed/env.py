# Released under the MIT License. See LICENSE for details.
#
"""Various utility calls for interacting with baenv."""

# This code runs in the logic thread to bootstrap ballistica.

from __future__ import annotations

from typing import TYPE_CHECKING
import sys

if TYPE_CHECKING:
    from typing import Callable

    import baenv

_atexits: list[Callable[[], None]] = []


def prepend_sys_path(path: str) -> None:
    """Simply add a path to sys paths at the beginning."""
    sys.path.insert(0, path)


def import_baenv_and_run_configure(
    config_dir: str | None,
    data_dir: str,
    cache_dir: str | None,
    user_python_dir: str | None,
    contains_python_dist: bool,
    strict_threads_atexit: Callable[[Callable[[], None]], None],
    setup_pycache_prefix: bool,
) -> None | str:
    """Import baenv and run its configure method.

    On success, returns None. On Failure, attempts to return an error
    traceback as a string (logging may not yet be functional at this point
    so we need to be direct).
    """
    # pylint: disable=too-many-positional-arguments
    try:
        import baenv

        baenv.configure(
            config_dir=config_dir,
            data_dir=data_dir,
            cache_dir=cache_dir,
            user_python_dir=user_python_dir,
            contains_python_dist=contains_python_dist,
            strict_threads_atexit=strict_threads_atexit,
            setup_pycache_prefix=setup_pycache_prefix,
        )
        return None
    except Exception:
        import traceback

        return traceback.format_exc()


def get_env_config() -> baenv.EnvConfig:
    """Import baenv and get the config."""
    import baenv

    return baenv.get_env_config()


def atexit(call: Callable[[], None]) -> None:
    """Register a call to run just before shutting down Python."""

    _atexits.append(call)


def pre_finalize() -> None:
    """Called on our monolithic builds just before Py_FinalizeEx().

    We use this to run our registered atexit() callbacks.
    """
    import logging

    # Like regular atexit, run our calls in reverse order.
    for call in reversed(_atexits):
        try:
            call()
        except Exception:
            logging.exception('Error in pre_finalize_call.')
