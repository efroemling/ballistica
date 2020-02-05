# Copyright (c) 2011-2020 Eric Froemling
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
# -----------------------------------------------------------------------------
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
