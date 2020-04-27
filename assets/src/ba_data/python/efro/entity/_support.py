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
"""Various support classes for accessing data and info on fields and values."""

from __future__ import annotations

from typing import TYPE_CHECKING, TypeVar, Generic, overload

from efro.entity._base import BaseField

if TYPE_CHECKING:
    from typing import (Optional, Tuple, Type, Any, Dict, List, Union)
    from efro.entity._value import CompoundValue
    from efro.entity._field import (ListField, DictField, CompoundListField,
                                    CompoundDictField)

T = TypeVar('T')
TKey = TypeVar('TKey')
TCompound = TypeVar('TCompound', bound='CompoundValue')
TBoundList = TypeVar('TBoundList', bound='BoundCompoundListField')


class BoundCompoundValue:
    """Wraps a CompoundValue object and its entity data.

    Allows access to its values through our own equivalent attributes.
    """

    def __init__(self, value: CompoundValue, d_data: Union[List[Any],
                                                           Dict[str, Any]]):
        self.d_value: CompoundValue
        self.d_data: Union[List[Any], Dict[str, Any]]

        # Need to use base setters to avoid triggering our own overrides.
        object.__setattr__(self, 'd_value', value)
        object.__setattr__(self, 'd_data', d_data)

    def __eq__(self, other: Any) -> Any:
        # Allow comparing to compound and bound-compound objects.
        from efro.entity.util import compound_eq
        return compound_eq(self, other)

    def __getattr__(self, name: str, default: Any = None) -> Any:
        # If this attribute corresponds to a field on our compound value's
        # unbound type, ask it to give us a value using our data
        d_value = type(object.__getattribute__(self, 'd_value'))
        field = getattr(d_value, name, None)
        if isinstance(field, BaseField):
            return field.get_with_data(self.d_data)
        raise AttributeError

    def __setattr__(self, name: str, value: Any) -> None:
        # Same deal as __getattr__ basically.
        field = getattr(type(object.__getattribute__(self, 'd_value')), name,
                        None)
        if isinstance(field, BaseField):
            field.set_with_data(self.d_data, value, error=True)
            return
        super().__setattr__(name, value)

    def reset(self) -> None:
        """Reset this field's data to defaults."""
        value = object.__getattribute__(self, 'd_value')
        data = object.__getattribute__(self, 'd_data')
        assert isinstance(data, dict)

        # Need to clear our dict in-place since we have no
        # access to our parent which we'd need to assign an empty one.
        data.clear()

        # Now fill in default data.
        value.apply_fields_to_data(data, error=True)

    def __repr__(self) -> str:
        fstrs: List[str] = []
        for field in self.d_value.get_fields():
            try:
                fstrs.append(str(field) + '=' + repr(getattr(self, field)))
            except Exception:
                fstrs.append('FAIL' + str(field) + ' ' + str(type(self)))
        return type(self.d_value).__name__ + '(' + ', '.join(fstrs) + ')'


class FieldInspector:
    """Used for inspecting fields."""

    def __init__(self, root: Any, obj: Any, path: List[str],
                 dbpath: List[str]) -> None:
        self._root = root
        self._obj = obj
        self._path = path
        self._dbpath = dbpath

    def __repr__(self) -> str:
        path = '.'.join(self._path)
        typename = type(self._root).__name__
        if path == '':
            return f'<FieldInspector: {typename}>'
        return f'<FieldInspector: {typename}: {path}>'

    def __getattr__(self, name: str, default: Any = None) -> Any:
        # pylint: disable=cyclic-import
        from efro.entity._field import CompoundField

        # If this attribute corresponds to a field on our obj's
        # unbound type, return a new inspector for it.
        if isinstance(self._obj, CompoundField):
            target = self._obj.d_value
        else:
            target = self._obj
        field = getattr(type(target), name, None)
        if isinstance(field, BaseField):
            newpath = list(self._path)
            newpath.append(name)
            newdbpath = list(self._dbpath)
            assert field.d_key is not None
            newdbpath.append(field.d_key)
            return FieldInspector(self._root, field, newpath, newdbpath)
        raise AttributeError

    def get_root(self) -> Any:
        """Return the root object this inspector is targeting."""
        return self._root

    def get_path(self) -> List[str]:
        """Return the python path components of this inspector."""
        return self._path

    def get_db_path(self) -> List[str]:
        """Return the database path components of this inspector."""
        return self._dbpath


class BoundListField(Generic[T]):
    """ListField bound to data; used for accessing field values."""

    def __init__(self, field: ListField[T], d_data: List[Any]):
        self.d_field = field
        assert isinstance(d_data, list)
        self.d_data = d_data
        self._i = 0

    def __eq__(self, other: Any) -> Any:
        # Just convert us into a regular list and run a compare with that.
        flattened = [
            self.d_field.d_value.filter_output(value) for value in self.d_data
        ]
        return flattened == other

    def __repr__(self) -> str:
        return '[' + ', '.join(
            repr(self.d_field.d_value.filter_output(i))
            for i in self.d_data) + ']'

    def __len__(self) -> int:
        return len(self.d_data)

    def __iter__(self) -> Any:
        self._i = 0
        return self

    def append(self, val: T) -> None:
        """Append the provided value to the list."""
        self.d_data.append(self.d_field.d_value.filter_input(val, error=True))

    def __next__(self) -> T:
        if self._i < len(self.d_data):
            self._i += 1
            val: T = self.d_field.d_value.filter_output(self.d_data[self._i -
                                                                    1])
            return val
        raise StopIteration

    @overload
    def __getitem__(self, key: int) -> T:
        ...

    @overload
    def __getitem__(self, key: slice) -> List[T]:
        ...

    def __getitem__(self, key: Any) -> Any:
        if isinstance(key, slice):
            dofilter = self.d_field.d_value.filter_output
            return [
                dofilter(self.d_data[i])
                for i in range(*key.indices(len(self)))
            ]
        assert isinstance(key, int)
        return self.d_field.d_value.filter_output(self.d_data[key])

    def __setitem__(self, key: int, value: T) -> None:
        if not isinstance(key, int):
            raise TypeError('Expected int index.')
        self.d_data[key] = self.d_field.d_value.filter_input(value, error=True)


class BoundDictField(Generic[TKey, T]):
    """DictField bound to its data; used for accessing its values."""

    def __init__(self, keytype: Type[TKey], field: DictField[TKey, T],
                 d_data: Dict[TKey, T]):
        self._keytype = keytype
        self.d_field = field
        assert isinstance(d_data, dict)
        self.d_data = d_data

    def __eq__(self, other: Any) -> Any:
        # Just convert us into a regular dict and run a compare with that.
        flattened = {
            key: self.d_field.d_value.filter_output(value)
            for key, value in self.d_data.items()
        }
        return flattened == other

    def __repr__(self) -> str:
        return '{' + ', '.join(
            repr(key) + ': ' + repr(self.d_field.d_value.filter_output(val))
            for key, val in self.d_data.items()) + '}'

    def __len__(self) -> int:
        return len(self.d_data)

    def __getitem__(self, key: TKey) -> T:
        if not isinstance(key, self._keytype):
            raise TypeError(
                f'Invalid key type {type(key)}; expected {self._keytype}')
        assert isinstance(key, self._keytype)
        typedval: T = self.d_field.d_value.filter_output(self.d_data[key])
        return typedval

    def get(self, key: TKey, default: Optional[T] = None) -> Optional[T]:
        """Get a value if present, or a default otherwise."""
        if not isinstance(key, self._keytype):
            raise TypeError(
                f'Invalid key type {type(key)}; expected {self._keytype}')
        assert isinstance(key, self._keytype)
        if key not in self.d_data:
            return default
        typedval: T = self.d_field.d_value.filter_output(self.d_data[key])
        return typedval

    def __setitem__(self, key: TKey, value: T) -> None:
        if not isinstance(key, self._keytype):
            raise TypeError('Expected str index.')
        self.d_data[key] = self.d_field.d_value.filter_input(value, error=True)

    def __contains__(self, key: TKey) -> bool:
        return key in self.d_data

    def __delitem__(self, key: TKey) -> None:
        del self.d_data[key]

    def keys(self) -> List[TKey]:
        """Return a list of our keys."""
        return list(self.d_data.keys())

    def values(self) -> List[T]:
        """Return a list of our values."""
        return [
            self.d_field.d_value.filter_output(value)
            for value in self.d_data.values()
        ]

    def items(self) -> List[Tuple[TKey, T]]:
        """Return a list of item/value pairs."""
        return [(key, self.d_field.d_value.filter_output(value))
                for key, value in self.d_data.items()]


class BoundCompoundListField(Generic[TCompound]):
    """A CompoundListField bound to its entity sub-data."""

    def __init__(self, field: CompoundListField[TCompound], d_data: List[Any]):
        self.d_field = field
        self.d_data = d_data
        self._i = 0

    def __eq__(self, other: Any) -> Any:
        from efro.entity.util import have_matching_fields

        # We can only be compared to other bound-compound-fields
        if not isinstance(other, BoundCompoundListField):
            return NotImplemented

        # If our compound values have differing fields, we're unequal.
        if not have_matching_fields(self.d_field.d_value,
                                    other.d_field.d_value):
            return False

        # Ok our data schemas match; now just compare our data..
        return self.d_data == other.d_data

    def __len__(self) -> int:
        return len(self.d_data)

    def __repr__(self) -> str:
        return '[' + ', '.join(
            repr(BoundCompoundValue(self.d_field.d_value, i))
            for i in self.d_data) + ']'

    # Note: to the type checker our gets/sets simply deal with CompoundValue
    # objects so the type-checker can cleanly handle their sub-fields.
    # However at runtime we deal in BoundCompoundValue objects which use magic
    # to tie the CompoundValue object to its data but which the type checker
    # can't understand.
    if TYPE_CHECKING:

        @overload
        def __getitem__(self, key: int) -> TCompound:
            ...

        @overload
        def __getitem__(self, key: slice) -> List[TCompound]:
            ...

        def __getitem__(self, key: Any) -> Any:
            ...

        def __next__(self) -> TCompound:
            ...

        def append(self) -> TCompound:
            """Append and return a new field entry to the array."""
            ...
    else:

        def __getitem__(self, key: Any) -> Any:
            if isinstance(key, slice):
                return [
                    BoundCompoundValue(self.d_field.d_value, self.d_data[i])
                    for i in range(*key.indices(len(self)))
                ]
            assert isinstance(key, int)
            return BoundCompoundValue(self.d_field.d_value, self.d_data[key])

        def __next__(self):
            if self._i < len(self.d_data):
                self._i += 1
                return BoundCompoundValue(self.d_field.d_value,
                                          self.d_data[self._i - 1])
            raise StopIteration

        def append(self) -> Any:
            """Append and return a new field entry to the array."""
            # push the entity default into data and then let it fill in
            # any children/etc.
            self.d_data.append(
                self.d_field.d_value.filter_input(
                    self.d_field.d_value.get_default_data(), error=True))
            return BoundCompoundValue(self.d_field.d_value, self.d_data[-1])

    def __iter__(self: TBoundList) -> TBoundList:
        self._i = 0
        return self


class BoundCompoundDictField(Generic[TKey, TCompound]):
    """A CompoundDictField bound to its entity sub-data."""

    def __init__(self, field: CompoundDictField[TKey, TCompound],
                 d_data: Dict[Any, Any]):
        self.d_field = field
        self.d_data = d_data

    def __eq__(self, other: Any) -> Any:
        from efro.entity.util import have_matching_fields

        # We can only be compared to other bound-compound-fields
        if not isinstance(other, BoundCompoundDictField):
            return NotImplemented

        # If our compound values have differing fields, we're unequal.
        if not have_matching_fields(self.d_field.d_value,
                                    other.d_field.d_value):
            return False

        # Ok our data schemas match; now just compare our data..
        return self.d_data == other.d_data

    def __repr__(self) -> str:
        return '{' + ', '.join(
            repr(key) + ': ' +
            repr(BoundCompoundValue(self.d_field.d_value, value))
            for key, value in self.d_data.items()) + '}'

    # In the typechecker's eyes, gets/sets on us simply deal in
    # CompoundValue object. This allows type-checking to work nicely
    # for its sub-fields.
    # However in real-life we return BoundCompoundValues which use magic
    # to tie the CompoundValue to its data (but which the typechecker
    # would not be able to make sense of)
    if TYPE_CHECKING:

        def __getitem__(self, key: TKey) -> TCompound:
            pass

        def values(self) -> List[TCompound]:
            """Return a list of our values."""

        def items(self) -> List[Tuple[TKey, TCompound]]:
            """Return key/value pairs for all dict entries."""

        def add(self, key: TKey) -> TCompound:
            """Add an entry into the dict, returning it.

            Any existing value is replaced."""

    else:

        def __getitem__(self, key):
            return BoundCompoundValue(self.d_field.d_value, self.d_data[key])

        def values(self):
            """Return a list of our values."""
            return list(
                BoundCompoundValue(self.d_field.d_value, i)
                for i in self.d_data.values())

        def items(self):
            """Return key/value pairs for all dict entries."""
            return [(key, BoundCompoundValue(self.d_field.d_value, value))
                    for key, value in self.d_data.items()]

        def add(self, key: TKey) -> TCompound:
            """Add an entry into the dict, returning it.

            Any existing value is replaced."""
            if not isinstance(key, self.d_field.d_keytype):
                raise TypeError(f'expected key type {self.d_field.d_keytype};'
                                f' got {type(key)}')
            # Push the entity default into data and then let it fill in
            # any children/etc.
            self.d_data[key] = (self.d_field.d_value.filter_input(
                self.d_field.d_value.get_default_data(), error=True))
            return BoundCompoundValue(self.d_field.d_value, self.d_data[key])

    def __len__(self) -> int:
        return len(self.d_data)

    def __contains__(self, key: TKey) -> bool:
        return key in self.d_data

    def __delitem__(self, key: TKey) -> None:
        del self.d_data[key]

    def keys(self) -> List[TKey]:
        """Return a list of our keys."""
        return list(self.d_data.keys())
