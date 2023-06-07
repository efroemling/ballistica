# Released under the MIT License. See LICENSE for details.
#
"""Functionality for importing, exporting, and validating dataclasses.

This allows complex nested dataclasses to be flattened to json-compatible
data and restored from said data. It also gracefully handles and preserves
unrecognized attribute data, allowing older clients to interact with newer
data formats in a nondestructive manner.
"""

from __future__ import annotations

from efro.util import set_canonical_module_names
from efro.dataclassio._base import Codec, IOAttrs, IOExtendedData
from efro.dataclassio._prep import (
    ioprep,
    ioprepped,
    will_ioprep,
    is_ioprepped_dataclass,
)
from efro.dataclassio._pathcapture import DataclassFieldLookup
from efro.dataclassio._api import (
    JsonStyle,
    dataclass_to_dict,
    dataclass_to_json,
    dataclass_from_dict,
    dataclass_from_json,
    dataclass_validate,
)

__all__ = [
    'JsonStyle',
    'Codec',
    'IOAttrs',
    'IOExtendedData',
    'ioprep',
    'ioprepped',
    'will_ioprep',
    'is_ioprepped_dataclass',
    'DataclassFieldLookup',
    'dataclass_to_dict',
    'dataclass_to_json',
    'dataclass_from_dict',
    'dataclass_from_json',
    'dataclass_validate',
]

# Have these things present themselves cleanly as 'thismodule.SomeClass'
# instead of 'thismodule._internalmodule.SomeClass'
set_canonical_module_names(globals())
