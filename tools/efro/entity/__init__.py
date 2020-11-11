# Released under the MIT License. See LICENSE for details.
#
"""Entity functionality.

A system for defining complex data-containing types, supporting both static
and run-time type safety, serialization, efficient/sparse storage, per-field
value limits, etc. These are heavy-weight in comparison to things such as
dataclasses, but the increased features can make the overhead worth it for
certain use cases.
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
