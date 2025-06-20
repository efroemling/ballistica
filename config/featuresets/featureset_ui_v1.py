# Released under the MIT License. See LICENSE for details.
#
# pylint: disable=useless-suppression, missing-docstring, invalid-name
from __future__ import annotations

# This file is exec'ed by the spinoff system, allowing us to define
# values and behavior for this feature-set here in a programmatic way
# that can also be type-checked alongside other project Python code.

from batools.featureset import FeatureSet
from batools.dummymodule import DummyModuleDef

# Grab the FeatureSet we're defining here.
fset = FeatureSet.get_active()

# Stuff we need.
fset.requirements = {'core', 'base'}

# We provide 'ba*.app.ui_v1'.
fset.has_python_app_subsystem = True

# We'd prefer our name's title form to be 'UI V1', not the default 'Ui V1'.
fset.name_title = 'UI V1'


# Customize how our dummy module is generated (work in progress).
class OurDummyModuleDef(DummyModuleDef):
    pass


fset.dummy_module_def = OurDummyModuleDef()
