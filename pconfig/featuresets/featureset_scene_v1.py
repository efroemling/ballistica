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
#
# Ideally we shouldn't need scene_v1_lib, but things are tangled for
# historical reasons.
fset.requirements = {'core', 'base', 'classic', 'scene_v1_lib'}
