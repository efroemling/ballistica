# Released under the MIT License. See LICENSE for details.
#
"""Plugin package for tournament screens."""

# ba_meta require api 9

from typing import override

import importlib
import os

from bautils.tools import package_loading_context
import bascenev1 as bs


# ba_meta export babase.Plugin
class RegisterTournamentScreens(bs.Plugin):
    """Register all screens in this module."""

    @override
    def on_app_running(self) -> None:
        with package_loading_context(name="Tournament Screens"):
            self._auto_import_all_modules()

    def _auto_import_all_modules(self) -> None:

        current_dir = os.path.dirname(__file__)
        package = __name__  # 'touny'

        for filename in os.listdir(current_dir):
            if filename.endswith(".py") and filename != "__init__.py":
                module_name = filename[:-3]
                full_module = f"{package}.{module_name}"
                importlib.import_module(full_module)
