# Released under the MIT License. See LICENSE for details.
#
# pylint: disable=missing-module-docstring, invalid-name
from __future__ import annotations

from batools.featureset import FeatureSet

# Grab the FeatureSet we're defining here.
fset = FeatureSet.get_active()

fset.requirements = {'core', 'base'}

fset.soft_requirements = {'classic', 'plus'}

fset.has_python_app_subsystem = True

fset.allow_as_soft_requirement = True
