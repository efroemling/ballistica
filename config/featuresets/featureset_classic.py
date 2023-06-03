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

fset.requirements = {'base', 'scene_v1', 'ui_v1'}

# We provide 'babase.app.classic'.
fset.has_python_app_subsystem = True

# We want things to work without us.
fset.allow_as_soft_requirement = True
