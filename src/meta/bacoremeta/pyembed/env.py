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


# The following warm_start calls are used by MonolithicMainIncremental
# to pull in Python stdlib stuff that we always use. This allows us to
# break importing into roughly equal (time-wise) pieces that we can run
# spaced out in the main thread without triggering app-not-responding
# reports. This is especially important now that we generate our own
# .pyc files on the fly; importing all this stuff at once on a slow
# mobile device can take a bit of time.


_g_warm_start_1_completed = False


def warm_start_1() -> None:
    """Early import python bits we'll be using later."""
    import threading

    threading.Thread(target=_warm_start_imports).start()


def _warm_start_imports() -> None:
    # pylint: disable=unused-import
    # pylint: disable=global-statement
    # pylint: disable=too-many-locals
    import os
    import ssl
    import zlib
    import json
    import time
    import copy
    import stat
    import fcntl
    import email
    import socket
    import locale
    import random
    import shutil
    import string
    import zipfile
    import inspect
    import logging
    import weakref
    import hashlib
    import pathlib
    import warnings
    import textwrap
    import tempfile
    import datetime
    import traceback
    import functools
    import encodings
    import importlib
    import contextlib
    import dataclasses
    import urllib.parse
    import collections.abc
    import concurrent.futures
    import asyncio

    global _g_warm_start_1_completed
    _g_warm_start_1_completed = True


def warm_start_1_completed() -> bool:
    """Is warm-start-1 done?"""
    return _g_warm_start_1_completed
