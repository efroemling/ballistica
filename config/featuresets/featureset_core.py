# Released under the MIT License. See LICENSE for details.
#
# pylint: disable=missing-module-docstring, invalid-name
from __future__ import annotations

# This file is exec'ed by the spinoff system, allowing us to define
# values and behavior for this feature-set here in a programmatic way
# that can also be type-checked alongside other project Python code.

from batools.featureset import FeatureSet

# Grab the FeatureSet we're defining here.
fset = FeatureSet.get_active()

# Stuff we need.
fset.requirements = set()

# We're a special case in that there is no 'bacore' module in Python;
# all of our functionality is exposed to Python through the 'babase'
# feature-set.
fset.has_python_binary_module = False

# Bits of code we're using that don't conform to our feature-set based
# namespace scheme.
fset.cpp_namespace_check_disable_files = {
    'src/ballistica/core/platform/android/utf8/checked.h',
    'src/ballistica/core/platform/android/utf8/unchecked.h',
    'src/ballistica/core/platform/android/utf8/core.h',
}
