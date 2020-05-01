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
"""Misc utility functionality related to the entity system."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Any, Union, Tuple, List
    from efro.entity._value import CompoundValue
    from efro.entity._support import BoundCompoundValue


def diff_compound_values(
        obj1: Union[BoundCompoundValue, CompoundValue],
        obj2: Union[BoundCompoundValue, CompoundValue]) -> str:
    """Generate a string showing differences between two compound values.

    Both must be associated with data and have the same set of fields.
    """

    # Ensure fields match and both are attached to data...
    value1, data1 = get_compound_value_and_data(obj1)
    if data1 is None:
        raise ValueError(f'Invalid unbound compound value: {obj1}')
    value2, data2 = get_compound_value_and_data(obj2)
    if data2 is None:
        raise ValueError(f'Invalid unbound compound value: {obj2}')
    if not have_matching_fields(value1, value2):
        raise ValueError(
            f"Can't diff objs with non-matching fields: {value1} and {value2}")

    # Ok; let 'er rip...
    diff = _diff(obj1, obj2, 2)
    return '  <no differences>' if diff == '' else diff


class CompoundValueDiff:
    """Wraps diff_compound_values() in an object for efficiency.

    It is preferable to pass this to logging calls instead of the
    final diff string since the diff will never be generated if
    the associated logging level is not being emitted.
    """

    def __init__(self, obj1: Union[BoundCompoundValue, CompoundValue],
                 obj2: Union[BoundCompoundValue, CompoundValue]):
        self._obj1 = obj1
        self._obj2 = obj2

    def __repr__(self) -> str:
        return diff_compound_values(self._obj1, self._obj2)


def _diff(obj1: Union[BoundCompoundValue, CompoundValue],
          obj2: Union[BoundCompoundValue, CompoundValue], indent: int) -> str:
    from efro.entity._support import BoundCompoundValue
    bits: List[str] = []
    indentstr = ' ' * indent
    vobj1, _data1 = get_compound_value_and_data(obj1)
    fields = sorted(vobj1.get_fields().keys())
    for field in fields:
        val1 = getattr(obj1, field)
        val2 = getattr(obj2, field)
        # for nested compounds, dive in and do nice piecewise compares
        if isinstance(val1, BoundCompoundValue):
            assert isinstance(val2, BoundCompoundValue)
            diff = _diff(val1, val2, indent + 2)
            if diff != '':
                bits.append(f'{indentstr}{field}:')
                bits.append(diff)
        # for all else just do a single line
        # (perhaps we could improve on this for other complex types)
        else:
            if val1 != val2:
                bits.append(f'{indentstr}{field}: {val1} -> {val2}')
    return '\n'.join(bits)


def have_matching_fields(val1: CompoundValue, val2: CompoundValue) -> bool:
    """Return whether two compound-values have matching sets of fields.

    Note this just refers to the field configuration; not data.
    """
    # quick-out: matching types will always have identical fields
    if type(val1) is type(val2):
        return True
    # otherwise do a full comparision
    return val1.get_fields() == val2.get_fields()


def get_compound_value_and_data(
    obj: Union[BoundCompoundValue,
               CompoundValue]) -> Tuple[CompoundValue, Any]:
    """Return value and data for bound or unbound compound values."""
    # pylint: disable=cyclic-import
    from efro.entity._support import BoundCompoundValue
    from efro.entity._value import CompoundValue
    if isinstance(obj, BoundCompoundValue):
        value = obj.d_value
        data = obj.d_data
    elif isinstance(obj, CompoundValue):
        value = obj
        data = getattr(obj, 'd_data', None)  # may not exist
    else:
        raise TypeError(
            f'Expected a BoundCompoundValue or CompoundValue; got {type(obj)}')
    return value, data


def compound_eq(obj1: Union[BoundCompoundValue, CompoundValue],
                obj2: Union[BoundCompoundValue, CompoundValue]) -> Any:
    """Compare two compound value/bound-value objects for equality."""

    # Criteria for comparison: both need to be a compound value
    # and both must have data (which implies they are either a entity
    # or bound to a subfield in a entity).
    value1, data1 = get_compound_value_and_data(obj1)
    if data1 is None:
        return NotImplemented
    value2, data2 = get_compound_value_and_data(obj2)
    if data2 is None:
        return NotImplemented

    # Ok we can compare them. To consider them equal we look for
    # matching sets of fields and matching data.  Note that there
    # could be unbound data causing inequality despite their field
    # values all matching; not sure if that's what we want.
    return have_matching_fields(value1, value2) and data1 == data2
