# Released under the MIT License. See LICENSE for details.

# Where most of our python-c++ binding happens.
# Python objects should be added here along with their associated c++ enum.
# pylint: disable=useless-suppression, missing-module-docstring, line-too-long

from typing import Any

# The C++ layer looks for this variable. (Any: entries are arbitrary
# Python objects -- classes, callables, values -- handed to C++.)
values = list[Any]()
