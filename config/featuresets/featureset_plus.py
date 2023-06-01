# Released under the MIT License. See LICENSE for details.
#
# pylint: disable=missing-docstring, invalid-name
from __future__ import annotations

# This file is exec'ed by the spinoff system, allowing us to define
# values and behavior for this feature-set here in a programmatic way
# that can also be type-checked alongside other project Python code.

from batools.featureset import FeatureSet

# Grab the FeatureSet we should apply to.
fset = FeatureSet.get_active()

fset.requirements = {'base'}
fset.internal = True
