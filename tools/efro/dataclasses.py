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
"""Custom functionality for dealing with dataclasses."""
from __future__ import annotations

import dataclasses
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Any, Dict, Type, Tuple

# For fields with these string types, we require a passed value's type
# to exactly match one of the tuple values to consider the assignment valid.
_SIMPLE_ASSIGN_TYPES: Dict[str, Tuple[Type, ...]] = {
    'int': (int, ),
    'str': (str, ),
    'bool': (bool, ),
    'float': (float, ),
    'Optional[int]': (int, type(None)),
    'Optional[str]': (str, type(None)),
    'Optional[bool]': (bool, type(None)),
    'Optional[float]': (float, type(None)),
}

_LIST_ASSIGN_TYPES: Dict[str, Tuple[Type, ...]] = {
    'List[int]': (int, ),
    'List[str]': (str, ),
    'List[bool]': (bool, ),
    'List[float]': (float, ),
}


def dataclass_assign(instance: Any, values: Dict[str, Any]) -> None:
    """Safely assign values from a dict to a dataclass instance.

    A TypeError will be raised if types to not match the dataclass fields
    or are unsupported by this function. Note that a limited number of
    types are supported. More can be added as needed.

    Exact types are strictly checked, so a bool cannot be passed for
    an int field, an int can't be passed for a float, etc.
    (can reexamine this strictness if it proves to be a problem)

    An AttributeError will be raised if attributes are passed which are
    not present on the dataclass as fields.

    This function may add significant overhead compared to passing dict
    values to a dataclass' constructor or other more direct methods, but
    the increased safety checks may be worth the speed tradeoff in some
    cases.
    """
    _dataclass_validate(instance, values)
    for key, value in values.items():
        setattr(instance, key, value)


def dataclass_validate(instance: Any) -> None:
    """Ensure values in a dataclass are correct types.

    Note that this will always fail if a dataclass contains field types
    not supported by this module.
    """
    _dataclass_validate(instance, dataclasses.asdict(instance))


def _dataclass_validate(instance: Any, values: Dict[str, Any]) -> None:
    # pylint: disable=too-many-branches
    if not dataclasses.is_dataclass(instance):
        raise TypeError(f'Passed instance {instance} is not a dataclass.')
    if not isinstance(values, dict):
        raise TypeError("Expected a dict for 'values' arg.")
    fields = dataclasses.fields(instance)
    fieldsdict = {f.name: f for f in fields}
    for key, value in values.items():
        if key not in fieldsdict:
            raise AttributeError(
                f"'{type(instance).__name__}' has no '{key}' field.")
        field = fieldsdict[key]

        # We expect to be operating under 'from __future__ import annotations'
        # so field types should always be strings for us; not an actual types.
        # Complain if we come across an actual type.
        fieldtype: str = field.type  # type: ignore
        if not isinstance(fieldtype, str):
            raise RuntimeError(
                f'Dataclass {type(instance).__name__} seems to have'
                f' been created without "from __future__ import annotations";'
                f' those dataclasses are unsupported here.')

        if fieldtype in _SIMPLE_ASSIGN_TYPES:
            reqtypes = _SIMPLE_ASSIGN_TYPES[fieldtype]
            valuetype = type(value)
            if not any(valuetype is t for t in reqtypes):
                if len(reqtypes) == 1:
                    expected = reqtypes[0].__name__
                else:
                    names = ', '.join(t.__name__ for t in reqtypes)
                    expected = f'Union[{names}]'
                raise TypeError(f'Invalid value type for "{key}";'
                                f' expected "{expected}", got'
                                f' "{valuetype.__name__}".')

        elif fieldtype in _LIST_ASSIGN_TYPES:
            reqtypes = _LIST_ASSIGN_TYPES[fieldtype]
            if not isinstance(value, list):
                raise TypeError(
                    f'Invalid value for "{key}";'
                    f' expected a list, got a "{type(value).__name__}"')
            for subvalue in value:
                subvaluetype = type(subvalue)
                if not any(subvaluetype is t for t in reqtypes):
                    if len(reqtypes) == 1:
                        expected = reqtypes[0].__name__
                    else:
                        names = ', '.join(t.__name__ for t in reqtypes)
                        expected = f'Union[{names}]'
                    raise TypeError(f'Invalid value type for "{key}";'
                                    f' expected list of "{expected}", found'
                                    f' "{subvaluetype.__name__}".')

        else:
            raise TypeError(f'Field type "{fieldtype}" is unsupported here.')
