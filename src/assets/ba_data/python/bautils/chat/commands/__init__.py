# Released under the MIT License. See LICENSE for details.
#
"""All Server commands are defined in this directory."""

# ba_meta require api 9

import os
import importlib

from typing import override

import bascenev1 as bs
from bautils.tools import package_loading_context


# ba_meta export babase.Plugin
class RegisterCommands(bs.Plugin):
    """Register all commands in this module."""

    @override
    def on_app_running(self) -> None:
        with package_loading_context(name="Command System"):
            self._auto_import_all_modules()

    def _auto_import_all_modules(self) -> None:

        current_dir = os.path.dirname(__file__)
        package = __name__  # 'commands'

        for filename in os.listdir(current_dir):
            if filename.endswith(".py") and filename != "__init__.py":
                module_name = filename[:-3]
                full_module = f"{package}.{module_name}"
                importlib.import_module(full_module)
