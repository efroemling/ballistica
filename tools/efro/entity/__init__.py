# Released under the MIT License. See LICENSE for details.
#
"""Entity functionality.

A system for defining structured data, supporting both static and runtime
type safety, serialization, efficient/sparse storage, per-field value
limits, etc. This is a heavyweight option in comparison to things such as
dataclasses, but the increased features can make the overhead worth it for
certain use cases.

Advantages compared to nested dataclasses:
- Field names separated from their data representation so can get more
  concise json data, change variable names while preserving back-compat, etc.
- Can wrap and preserve unmapped data (so fields can be added to new versions
  of something without breaking old versions' ability to read the data)
- Incorrectly typed data is caught at runtime (for dataclasses we rely on
  type-checking and explicit validation calls)

Disadvantages compared to nested dataclasses:
- More complex to use
- Significantly more heavyweight (roughly 10 times slower in quick tests)
- Can't currently be initialized in constructors (this would probably require
  a Mypy plugin to do in a type-safe way)
"""
# pylint: disable=unused-import

from efro.entity._entity import EntityMixin, Entity
from efro.entity._field import (Field, CompoundField, ListField, DictField,
                                CompoundListField, CompoundDictField)
from efro.entity._value import (
    EnumValue, OptionalEnumValue, IntValue, OptionalIntValue, StringValue,
    OptionalStringValue, BoolValue, OptionalBoolValue, FloatValue,
    OptionalFloatValue, DateTimeValue, OptionalDateTimeValue, Float3Value,
    CompoundValue)

from efro.entity._support import FieldInspector
