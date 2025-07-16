# Released under the MIT License. See LICENSE for details.
#
"""All Server commands are defined in this directory."""

# ba_meta require api 9

import os
import importlib
import time

from typing import Generator, Any, override
from contextlib import contextmanager

import bascenev1 as bs


@contextmanager
def command_loading_context(
    name: str = "Command system",
) -> Generator[None, Any, None]:
    """A context manager securing to load all commands in this package."""

    print(f"🚀 Initializing {name}...")
    start = time.time()
    try:
        yield
        elapsed = time.time() - start
        print(f"✅ All command modules loaded in {elapsed:.2f}s.\n")
    except Exception as e:
        print(f"❌ Failed to load module {name}: {e}")
        raise


# ba_meta export babase.Plugin
class RegisterCommands(bs.Plugin):
    """Register all commands in this module."""

    @override
    def on_app_running(self) -> None:
        with command_loading_context():
            self._auto_import_all_modules()

    def _auto_import_all_modules(self) -> None:

        current_dir = os.path.dirname(__file__)
        package = __name__  # 'commands'

        for filename in os.listdir(current_dir):
            if filename.endswith(".py") and filename != "__init__.py":
                module_name = filename[:-3]
                full_module = f"{package}.{module_name}"
                importlib.import_module(full_module)
