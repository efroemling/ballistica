# Released under the MIT License. See LICENSE for details.
#
"""Custom functionality for dealing with dataclasses."""
# Note: We do lots of comparing of exact types here which is normally
# frowned upon (stuff like isinstance() is usually encouraged).
# pylint: disable=unidiomatic-typecheck

from __future__ import annotations

import dataclasses
import inspect
from enum import Enum
from typing import TYPE_CHECKING, TypeVar, Generic

from efro.util import enum_by_value

if TYPE_CHECKING:
    from typing import Any, Dict, Type, Tuple, Optional

T = TypeVar('T')

SIMPLE_NAMES_TO_TYPES: Dict[str, Type] = {
    'int': int,
    'bool': bool,
    'str': str,
    'float': float,
}
SIMPLE_TYPES_TO_NAMES = {tp: nm for nm, tp in SIMPLE_NAMES_TO_TYPES.items()}


def dataclass_to_dict(obj: Any, coerce_to_float: bool = True) -> dict:
    """Given a dataclass object, emit a json-friendly dict.

    All values will be checked to ensure they match the types specified
    on fields. Note that only a limited set of types is supported.

    If coerce_to_float is True, integer values present on float typed fields
    will be converted to floats in the dict output. If False, a TypeError
    will be triggered.
    """

    out = _Outputter(obj, create=True, coerce_to_float=coerce_to_float).run()
    assert isinstance(out, dict)
    return out


def dataclass_from_dict(cls: Type[T],
                        values: dict,
                        coerce_to_float: bool = True) -> T:
    """Given a dict, instantiates a dataclass of the given type.

    The dict must be in the json-friendly format as emitted from
    dataclass_to_dict. This means that sequence values such as tuples or
    sets should be passed as lists, enums should be passed as their
    associated values, and nested dataclasses should be passed as dicts.

    If coerce_to_float is True, int values passed for float typed fields
    will be converted to float values. Otherwise a TypeError is raised.
    """
    return _Inputter(cls, coerce_to_float=coerce_to_float).run(values)


def dataclass_validate(obj: Any, coerce_to_float: bool = True) -> None:
    """Ensure that current values in a dataclass are the correct types."""
    _Outputter(obj, create=False, coerce_to_float=coerce_to_float).run()


def _field_type_str(cls: Type, field: dataclasses.Field) -> str:
    # We expect to be operating under 'from __future__ import annotations'
    # so field types should always be strings for us; not actual types.
    # (Can pull this check out once we get to Python 3.10)
    typestr: str = field.type  # type: ignore

    if not isinstance(typestr, str):
        raise RuntimeError(
            f'Dataclass {cls.__name__} seems to have'
            f' been created without "from __future__ import annotations";'
            f' those dataclasses are unsupported here.')
    return typestr


def _raise_type_error(fieldpath: str, valuetype: Type,
                      expected: Tuple[Type, ...]) -> None:
    """Raise an error when a field value's type does not match expected."""
    assert isinstance(expected, tuple)
    assert all(isinstance(e, type) for e in expected)
    if len(expected) == 1:
        expected_str = expected[0].__name__
    else:
        names = ', '.join(t.__name__ for t in expected)
        expected_str = f'Union[{names}]'
    raise TypeError(f'Invalid value type for "{fieldpath}";'
                    f' expected "{expected_str}", got'
                    f' "{valuetype.__name__}".')


class _Outputter:

    def __init__(self, obj: Any, create: bool, coerce_to_float: bool) -> None:
        self._obj = obj
        self._create = create
        self._coerce_to_float = coerce_to_float

    def run(self) -> Any:
        """Do the thing."""
        return self._dataclass_to_output(self._obj, '')

    def _value_to_output(self, fieldpath: str, typestr: str,
                         value: Any) -> Any:
        # pylint: disable=too-many-return-statements
        # pylint: disable=too-many-branches

        # For simple flat types, look for exact matches:
        simpletype = SIMPLE_NAMES_TO_TYPES.get(typestr)
        if simpletype is not None:
            if type(value) is not simpletype:
                # Special case: if they want to coerce ints to floats, do so.
                if (self._coerce_to_float and simpletype is float
                        and type(value) is int):
                    return float(value) if self._create else None
                _raise_type_error(fieldpath, type(value), (simpletype, ))
            return value

        if typestr.startswith('Optional[') and typestr.endswith(']'):
            subtypestr = typestr[9:-1]
            # Handle the 'None' case special and do the default otherwise.
            if value is None:
                return None
            return self._value_to_output(fieldpath, subtypestr, value)

        if typestr.startswith('List[') and typestr.endswith(']'):
            subtypestr = typestr[5:-1]
            if not isinstance(value, list):
                raise TypeError(f'Expected a list for {fieldpath};'
                                f' found a {type(value)}')
            if self._create:
                return [
                    self._value_to_output(fieldpath, subtypestr, x)
                    for x in value
                ]
            for x in value:
                self._value_to_output(fieldpath, subtypestr, x)
            return None

        if typestr.startswith('Set[') and typestr.endswith(']'):
            subtypestr = typestr[4:-1]
            if not isinstance(value, set):
                raise TypeError(f'Expected a set for {fieldpath};'
                                f' found a {type(value)}')
            if self._create:
                # Note: we output json-friendly values so this becomes a list.
                return [
                    self._value_to_output(fieldpath, subtypestr, x)
                    for x in value
                ]
            for x in value:
                self._value_to_output(fieldpath, subtypestr, x)
            return None

        if dataclasses.is_dataclass(value):
            return self._dataclass_to_output(value, fieldpath)

        if isinstance(value, Enum):
            enumvalue = value.value
            if type(enumvalue) not in SIMPLE_TYPES_TO_NAMES:
                raise TypeError(f'Invalid enum value type {type(enumvalue)}'
                                f' for "{fieldpath}".')
            return enumvalue

        raise TypeError(
            f"Field '{fieldpath}' of type '{typestr}' is unsupported here.")

    def _dataclass_to_output(self, obj: Any, fieldpath: str) -> Any:
        if not dataclasses.is_dataclass(obj):
            raise TypeError(f'Passed obj {obj} is not a dataclass.')
        fields = dataclasses.fields(obj)
        out: Optional[Dict[str, Any]] = {} if self._create else None

        for field in fields:
            fieldname = field.name

            if fieldpath:
                subfieldpath = f'{fieldpath}.{fieldname}'
            else:
                subfieldpath = fieldname
            typestr = _field_type_str(type(obj), field)
            value = getattr(obj, fieldname)
            outvalue = self._value_to_output(subfieldpath, typestr, value)
            if self._create:
                assert out is not None
                out[fieldname] = outvalue

        return out


class _Inputter(Generic[T]):

    def __init__(self, cls: Type[T], coerce_to_float: bool):
        self._cls = cls
        self._coerce_to_float = coerce_to_float

    def run(self, values: dict) -> T:
        """Do the thing."""
        return self._dataclass_from_input(  # type: ignore
            self._cls, '', values)

    def _value_from_input(self, cls: Type, fieldpath: str, typestr: str,
                          value: Any) -> Any:
        """Convert an assigned value to what a dataclass field expects."""
        # pylint: disable=too-many-return-statements

        simpletype = SIMPLE_NAMES_TO_TYPES.get(typestr)
        if simpletype is not None:
            if type(value) is not simpletype:
                # Special case: if they want to coerce ints to floats, do so.
                if (self._coerce_to_float and simpletype is float
                        and type(value) is int):
                    return float(value)
                _raise_type_error(fieldpath, type(value), (simpletype, ))
            return value
        if typestr.startswith('List[') and typestr.endswith(']'):
            return self._sequence_from_input(cls, fieldpath, typestr, value,
                                             'List', list)
        if typestr.startswith('Set[') and typestr.endswith(']'):
            return self._sequence_from_input(cls, fieldpath, typestr, value,
                                             'Set', set)
        if typestr.startswith('Optional[') and typestr.endswith(']'):
            subtypestr = typestr[9:-1]
            # Handle the 'None' case special and do the default
            # thing otherwise.
            if value is None:
                return None
            return self._value_from_input(cls, fieldpath, subtypestr, value)

        # Ok, its not a builtin type. It might be an enum or nested dataclass.
        cls2 = getattr(inspect.getmodule(cls), typestr, None)
        if cls2 is None:
            raise RuntimeError(f"Unable to resolve '{typestr}'"
                               f" used by class '{cls.__name__}';"
                               f' make sure all nested types are declared'
                               f' in the global namespace of the module where'
                               f" '{cls.__name__} is defined.")

        if dataclasses.is_dataclass(cls2):
            return self._dataclass_from_input(cls2, fieldpath, value)

        if issubclass(cls2, Enum):
            return enum_by_value(cls2, value)

        raise TypeError(
            f"Field '{fieldpath}' of type '{typestr}' is unsupported here.")

    def _dataclass_from_input(self, cls: Type, fieldpath: str,
                              values: dict) -> Any:
        """Given a dict, instantiates a dataclass of the given type.

        The dict must be in the json-friendly format as emitted from
        dataclass_to_dict. This means that sequence values such as tuples or
        sets should be passed as lists, enums should be passed as their
        associated values, and nested dataclasses should be passed as dicts.
        """
        if not dataclasses.is_dataclass(cls):
            raise TypeError(f'Passed class {cls} is not a dataclass.')
        if not isinstance(values, dict):
            raise TypeError("Expected a dict for 'values' arg.")

        # noinspection PyDataclass
        fields = dataclasses.fields(cls)
        fields_by_name = {f.name: f for f in fields}
        args: Dict[str, Any] = {}
        for key, value in values.items():
            field = fields_by_name.get(key)
            if field is None:
                raise AttributeError(f"'{cls.__name__}' has no '{key}' field.")

            typestr = _field_type_str(cls, field)

            subfieldpath = (f'{fieldpath}.{field.name}'
                            if fieldpath else field.name)
            args[key] = self._value_from_input(cls, subfieldpath, typestr,
                                               value)

        return cls(**args)

    def _sequence_from_input(self, cls: Type, fieldpath: str, typestr: str,
                             value: Any, seqtypestr: str,
                             seqtype: Type) -> Any:
        # Because we are json-centric, we expect a list for all sequences.
        if type(value) is not list:
            raise TypeError(f'Invalid input value for "{fieldpath}";'
                            f' expected a list, got a {type(value).__name__}')
        subtypestr = typestr[len(seqtypestr) + 1:-1]
        return seqtype(
            self._value_from_input(cls, fieldpath, subtypestr, i)
            for i in value)
