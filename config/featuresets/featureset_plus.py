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

fset.requirements = {'core', 'base'}

# We use classic but can live without it.
fset.soft_requirements = {'classic'}

fset.internal = True

# We provide 'ba*.app.plus'.
fset.has_python_app_subsystem = True

# We want things to work without us. Note that this will cause our
# subsystem's type annotation to be PlusAppSubsystem | None instead of
# the default PlusAppSubsystem.
fset.allow_as_soft_requirement = True
