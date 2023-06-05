# Released under the MIT License. See LICENSE for details.
# Where most of our python-c++ binding happens.
# Python objects should be added here along with their associated c++ enum.
# Run make update to update the project after editing this..
# pylint: disable=missing-module-docstring, line-too-long
from __future__ import annotations
import babase


# The C++ layer looks for this variable:
values = [
    babase.app,  # kApp
    babase.app.handle_deep_link,  # kDeepLinkCall
    babase.app.lang.get_resource,  # kGetResourceCall
    babase.app.lang.translate,  # kTranslateCall
]
