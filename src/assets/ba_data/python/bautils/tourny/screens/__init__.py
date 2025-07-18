# Released under the MIT License. See LICENSE for details.
#
"""Package that handles tournament mode."""

# ba_meta require api 9

from typing import override
import os
import importlib
import bascenev1 as bs


# ba_meta export babase.Plugin
class RegisterTournamentScreens(bs.Plugin):
    """Register all screens in this module."""

    @override
    def on_app_running(self) -> None:
        self._auto_import_all_modules()
        print("imported tourny screens.")

    def _auto_import_all_modules(self) -> None:

        current_dir = os.path.dirname(__file__)
        package = __name__

        for filename in os.listdir(current_dir):
            if filename.endswith(".py") and filename != "__init__.py":
                module_name = filename[:-3]
                full_module = f"{package}.{module_name}"
                importlib.import_module(full_module)
