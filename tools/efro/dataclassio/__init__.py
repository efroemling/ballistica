# Released under the MIT License. See LICENSE for details.
#
"""Functionality for importing, exporting, and validating dataclasses.

This allows complex nested dataclasses to be flattened to json-compatible
data and restored from said data. It also gracefully handles and preserves
unrecognized attribute data, allowing older clients to interact with newer
data formats in a nondestructive manner.
"""

from __future__ import annotations

# from efro.util import set_canonical_module_names
from efro.dataclassio._base import (
    Codec,
    IOAttrs,
    IOExtendedData,
    IOMultiType,
    EXTRA_ATTRS_ATTR,
    parse_annotated,
)
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
    dataclass_hash,
)

__all__ = [
    'Codec',
    'DataclassFieldLookup',
    'EXTRA_ATTRS_ATTR',
    'IOAttrs',
    'IOExtendedData',
    'IOMultiType',
    'JsonStyle',
    'dataclass_from_dict',
    'dataclass_from_json',
    'dataclass_to_dict',
    'dataclass_to_json',
    'dataclass_validate',
    'dataclass_hash',
    'ioprep',
    'ioprepped',
    'is_ioprepped_dataclass',
    'parse_annotated',
    'will_ioprep',
]

# Have these things present themselves cleanly as 'thismodule.SomeClass'
# instead of 'thismodule._internalmodule.SomeClass'
# UPDATE: Trying without this for now. Seems like this might cause more
# harm than good. Can flip it back on if it is missed.
# set_canonical_module_names(globals())
