# Released under the MIT License. See LICENSE for details.
#
"""Extra rarely-needed functionality related to dataclasses."""

from __future__ import annotations

import dataclasses
from typing import TYPE_CHECKING, override

if TYPE_CHECKING:
    from typing import Any


def dataclass_diff(obj1: Any, obj2: Any) -> str:
    """Generate a string showing differences between two dataclass instances.

    Both must be of the exact same type.
    """
    diff = _diff(obj1, obj2, 2)
    return '  <no differences>' if diff == '' else diff


class DataclassDiff:
    """Wraps dataclass_diff() in an object for efficiency.

    It is preferable to pass this to logging calls instead of the
    final diff string since the diff will never be generated if
    the associated logging level is not being emitted.
    """

    def __init__(self, obj1: Any, obj2: Any):
        self._obj1 = obj1
        self._obj2 = obj2

    @override
    def __repr__(self) -> str:
        return dataclass_diff(self._obj1, self._obj2)


def _diff(obj1: Any, obj2: Any, indent: int) -> str:
    assert dataclasses.is_dataclass(obj1)
    assert dataclasses.is_dataclass(obj2)
    if type(obj1) is not type(obj2):
        raise TypeError(
            f'Passed objects are not of the same'
            f' type ({type(obj1)} and {type(obj2)}).'
        )
    bits: list[str] = []
    indentstr = ' ' * indent
    fields = dataclasses.fields(obj1)
    for field in fields:
        fieldname = field.name
        val1 = getattr(obj1, fieldname)
        val2 = getattr(obj2, fieldname)

        # For nested dataclasses, dive in and do nice piecewise compares.
        if (
            dataclasses.is_dataclass(val1)
            and dataclasses.is_dataclass(val2)
            and type(val1) is type(val2)
        ):
            diff = _diff(val1, val2, indent + 2)
            if diff != '':
                bits.append(f'{indentstr}{fieldname}:')
                bits.append(diff)

        # For all else just do a single line
        # (perhaps we could improve on this for other complex types)
        else:
            if val1 != val2:
                bits.append(f'{indentstr}{fieldname}: {val1} -> {val2}')
    return '\n'.join(bits)
