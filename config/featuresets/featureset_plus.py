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
fset.requirements = {'core', 'base'}

# Stuff we use but don't *need* (and only access via app-subsystems).
fset.soft_requirements = {'classic'}

fset.internal = True

# We provide 'ba*.app.plus'.
fset.has_python_app_subsystem = True

# Allow things to soft-require us so they can work when we're not
# present. Note that this will cause our app-subsystem's type annotation
# to be `PlusAppSubsystem | None` instead of the default
# `PlusAppSubsystem`.
fset.allow_as_soft_requirement = True
