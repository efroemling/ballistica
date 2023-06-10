# Released under the MIT License. See LICENSE for details.

# Where most of our python-c++ binding happens.
# Python objects should be added here along with their associated c++ enum.
# pylint: disable=useless-suppression, missing-module-docstring, line-too-long
from __future__ import annotations

from batemplatefs import _hooks

# The C++ layer looks for this variable:
values = [
    _hooks.hello_world,  # kHelloWorldCall
]
