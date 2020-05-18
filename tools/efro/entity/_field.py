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
"""Field types for the entity system."""

from __future__ import annotations

import copy
import logging
from typing import TYPE_CHECKING, Generic, TypeVar, overload

from efro.entity._base import BaseField
from efro.entity._support import (BoundCompoundValue, BoundListField,
                                  BoundDictField, BoundCompoundListField,
                                  BoundCompoundDictField)
from efro.entity.util import have_matching_fields

if TYPE_CHECKING:
    from typing import Dict, Type, List, Any
    from efro.entity._value import TypedValue, CompoundValue

T = TypeVar('T')
TK = TypeVar('TK')
TC = TypeVar('TC', bound='CompoundValue')


class Field(BaseField, Generic[T]):
    """Field consisting of a single value."""

    def __init__(self,
                 d_key: str,
                 value: TypedValue[T],
                 store_default: bool = True) -> None:
        super().__init__(d_key)
        self.d_value = value
        self._store_default = store_default

    def __repr__(self) -> str:
        return f'<Field "{self.d_key}" with {self.d_value}>'

    def get_default_data(self) -> Any:
        return self.d_value.get_default_data()

    def filter_input(self, data: Any, error: bool) -> Any:
        return self.d_value.filter_input(data, error)

    def filter_output(self, data: Any) -> Any:
        return self.d_value.filter_output(data)

    def prune_data(self, data: Any) -> bool:
        return self.d_value.prune_data(data)

    if TYPE_CHECKING:
        # Use default runtime get/set but let type-checker know our types.
        # Note: we actually return a bound-field when accessed on
        # a type instead of an instance, but we don't reflect that here yet
        # (would need to write a mypy plugin so sub-field access works first)

        @overload
        def __get__(self, obj: None, cls: Any = None) -> Field[T]:
            ...

        @overload
        def __get__(self, obj: Any, cls: Any = None) -> T:
            ...

        def __get__(self, obj: Any, cls: Any = None) -> Any:
            ...

        def __set__(self, obj: Any, value: T) -> None:
            ...


class CompoundField(BaseField, Generic[TC]):
    """Field consisting of a single compound value."""

    def __init__(self,
                 d_key: str,
                 value: TC,
                 store_default: bool = True) -> None:
        super().__init__(d_key)
        if __debug__:
            from efro.entity._value import CompoundValue
            assert isinstance(value, CompoundValue)
            assert not hasattr(value, 'd_data')
        self.d_value = value
        self._store_default = store_default

    def get_default_data(self) -> dict:
        return self.d_value.get_default_data()

    def filter_input(self, data: Any, error: bool) -> dict:
        return self.d_value.filter_input(data, error)

    def prune_data(self, data: Any) -> bool:
        return self.d_value.prune_data(data)

    # Note:
    # Currently, to the type-checker we just return a simple instance
    # of our CompoundValue so it can properly type-check access to its
    # attrs. However at runtime we return a FieldInspector or
    # BoundCompoundField which both use magic to provide the same attrs
    # dynamically (but which the type-checker doesn't understand).
    # Perhaps at some point we can write a mypy plugin to correct this.
    if TYPE_CHECKING:

        def __get__(self, obj: Any, cls: Any = None) -> TC:
            ...

        # Theoretically this type-checking may be too tight;
        # we can support assigning a parent class to a child class if
        # their fields match.  Not sure if that'll ever come up though;
        # gonna leave this for now as I prefer to have *some* checking.
        # Also once we get BoundCompoundValues working with mypy we'll
        # need to accept those too.
        def __set__(self: CompoundField[TC], obj: Any, value: TC) -> None:
            ...

    def get_with_data(self, data: Any) -> Any:
        assert self.d_key in data
        return BoundCompoundValue(self.d_value, data[self.d_key])

    def set_with_data(self, data: Any, value: Any, error: bool) -> Any:
        from efro.entity._value import CompoundValue

        # Ok here's the deal: our type checking above allows any subtype
        # of our CompoundValue in here, but we want to be more picky than
        # that. Let's check fields for equality. This way we'll allow
        # assigning something like a Carentity to a Car field
        # (where the data is the same), but won't allow assigning a Car
        # to a Vehicle field (as Car probably adds more fields).
        value1: CompoundValue
        if isinstance(value, BoundCompoundValue):
            value1 = value.d_value
        elif isinstance(value, CompoundValue):
            value1 = value
        else:
            raise ValueError(f"Can't assign from object type {type(value)}")
        dataval = getattr(value, 'd_data', None)
        if dataval is None:
            raise ValueError(f"Can't assign from unbound object {value}")
        if self.d_value.get_fields() != value1.get_fields():
            raise ValueError(f"Can't assign to {self.d_value} from"
                             f' incompatible type {value.d_value}; '
                             f'sub-fields do not match.')

        # If we're allowing this to go through, we can simply copy the
        # data from the passed in value. The fields match so it should
        # be in a valid state already.
        data[self.d_key] = copy.deepcopy(dataval)


class ListField(BaseField, Generic[T]):
    """Field consisting of repeated values."""

    def __init__(self,
                 d_key: str,
                 value: TypedValue[T],
                 store_default: bool = True) -> None:
        super().__init__(d_key)
        self.d_value = value
        self._store_default = store_default

    def get_default_data(self) -> list:
        return []

    def filter_input(self, data: Any, error: bool) -> Any:

        # If we were passed a BoundListField, operate on its raw values
        if isinstance(data, BoundListField):
            data = data.d_data

        if not isinstance(data, list):
            if error:
                raise TypeError(f'list value expected; got {type(data)}')
            logging.error('Ignoring non-list data for %s: %s', self, data)
            data = []
        for i, entry in enumerate(data):
            data[i] = self.d_value.filter_input(entry, error=error)
        return data

    def prune_data(self, data: Any) -> bool:
        # We never prune individual values since that would fundamentally
        # change the list, but we can prune completely if empty (and allowed).
        return not data and not self._store_default

    # When accessed on a FieldInspector we return a sub-field FieldInspector.
    # When accessed on an instance we return a BoundListField.

    # noinspection DuplicatedCode
    if TYPE_CHECKING:

        # Access via type gives our field; via an instance gives a bound field.
        @overload
        def __get__(self, obj: None, cls: Any = None) -> ListField[T]:
            ...

        @overload
        def __get__(self, obj: Any, cls: Any = None) -> BoundListField[T]:
            ...

        def __get__(self, obj: Any, cls: Any = None) -> Any:
            ...

        # Allow setting via a raw value list or a bound list field
        @overload
        def __set__(self, obj: Any, value: List[T]) -> None:
            ...

        @overload
        def __set__(self, obj: Any, value: BoundListField[T]) -> None:
            ...

        def __set__(self, obj: Any, value: Any) -> None:
            ...

    def get_with_data(self, data: Any) -> Any:
        return BoundListField(self, data[self.d_key])


class DictField(BaseField, Generic[TK, T]):
    """A field of values in a dict with a specified index type."""

    def __init__(self,
                 d_key: str,
                 keytype: Type[TK],
                 field: TypedValue[T],
                 store_default: bool = True) -> None:
        super().__init__(d_key)
        self.d_value = field
        self._store_default = store_default
        self._keytype = keytype

    def get_default_data(self) -> dict:
        return {}

    # noinspection DuplicatedCode
    def filter_input(self, data: Any, error: bool) -> Any:

        # If we were passed a BoundDictField, operate on its raw values
        if isinstance(data, BoundDictField):
            data = data.d_data

        if not isinstance(data, dict):
            if error:
                raise TypeError('dict value expected')
            logging.error('Ignoring non-dict data for %s: %s', self, data)
            data = {}
        data_out = {}
        for key, val in data.items():
            if not isinstance(key, self._keytype):
                if error:
                    raise TypeError('invalid key type')
                logging.error('Ignoring invalid key type for %s: %s', self,
                              data)
                continue
            data_out[key] = self.d_value.filter_input(val, error=error)
        return data_out

    def prune_data(self, data: Any) -> bool:
        # We never prune individual values since that would fundamentally
        # change the dict, but we can prune completely if empty (and allowed)
        return not data and not self._store_default

    # noinspection DuplicatedCode
    if TYPE_CHECKING:

        # Return our field if accessed via type and bound-dict-field
        # if via instance.
        @overload
        def __get__(self, obj: None, cls: Any = None) -> DictField[TK, T]:
            ...

        @overload
        def __get__(self, obj: Any, cls: Any = None) -> BoundDictField[TK, T]:
            ...

        def __get__(self, obj: Any, cls: Any = None) -> Any:
            ...

        # Allow setting via matching dict values or BoundDictFields
        @overload
        def __set__(self, obj: Any, value: Dict[TK, T]) -> None:
            ...

        @overload
        def __set__(self, obj: Any, value: BoundDictField[TK, T]) -> None:
            ...

        def __set__(self, obj: Any, value: Any) -> None:
            ...

    def get_with_data(self, data: Any) -> Any:
        return BoundDictField(self._keytype, self, data[self.d_key])


class CompoundListField(BaseField, Generic[TC]):
    """A field consisting of repeated instances of a compound-value.

    Element access returns the sub-field, allowing nested field access.
    ie: mylist[10].fieldattr = 'foo'
    """

    def __init__(self,
                 d_key: str,
                 valuetype: TC,
                 store_default: bool = True) -> None:
        super().__init__(d_key)
        self.d_value = valuetype

        # This doesnt actually exist for us, but want the type-checker
        # to think it does (see TYPE_CHECKING note below).
        self.d_data: Any
        self._store_default = store_default

    def filter_input(self, data: Any, error: bool) -> list:

        if not isinstance(data, list):
            if error:
                raise TypeError('list value expected')
            logging.error('Ignoring non-list data for %s: %s', self, data)
            data = []
        assert isinstance(data, list)

        # Ok we've got a list; now run everything in it through validation.
        for i, subdata in enumerate(data):
            data[i] = self.d_value.filter_input(subdata, error=error)
        return data

    def get_default_data(self) -> list:
        return []

    def prune_data(self, data: Any) -> bool:
        # Run pruning on all individual entries' data through out child field.
        # However we don't *completely* prune values from the list since that
        # would change it.
        for subdata in data:
            self.d_value.prune_fields_data(subdata)

        # We can also optionally prune the whole list if empty and allowed.
        return not data and not self._store_default

    # noinspection DuplicatedCode
    if TYPE_CHECKING:

        @overload
        def __get__(self, obj: None, cls: Any = None) -> CompoundListField[TC]:
            ...

        @overload
        def __get__(self,
                    obj: Any,
                    cls: Any = None) -> BoundCompoundListField[TC]:
            ...

        def __get__(self, obj: Any, cls: Any = None) -> Any:
            ...

        # Note:
        # When setting the list, we tell the type-checker that we also accept
        # a raw list of CompoundValue objects, but at runtime we actually
        # always deal with BoundCompoundValue objects (see note in
        # BoundCompoundListField for why we accept CompoundValue objs)
        @overload
        def __set__(self, obj: Any, value: List[TC]) -> None:
            ...

        @overload
        def __set__(self, obj: Any, value: BoundCompoundListField[TC]) -> None:
            ...

        def __set__(self, obj: Any, value: Any) -> None:
            ...

    def get_with_data(self, data: Any) -> Any:
        assert self.d_key in data
        return BoundCompoundListField(self, data[self.d_key])

    def set_with_data(self, data: Any, value: Any, error: bool) -> Any:

        # If we were passed a BoundCompoundListField,
        # simply convert it to a flat list of BoundCompoundValue objects which
        # is what we work with natively here.
        if isinstance(value, BoundCompoundListField):
            value = list(value)

        if not isinstance(value, list):
            raise TypeError(f'CompoundListField expected list value on set;'
                            f' got {type(value)}.')

        # Allow assigning only from a sequence of our existing children.
        # (could look into expanding this to other children if we can
        # be sure the underlying data will line up; for example two
        # CompoundListFields with different child_field values should not
        # be inter-assignable.
        if not all(isinstance(i, BoundCompoundValue) for i in value):
            raise ValueError('CompoundListField assignment must be a '
                             'list containing only BoundCompoundValue objs.')

        # Make sure the data all has the same CompoundValue type and
        # compare that type against ours once to make sure its fields match.
        # (this will not allow passing CompoundValues from multiple sources
        # but I don't know if that would ever come up..)
        for i, val in enumerate(value):
            if i == 0:
                # Do the full field comparison on the first value only..
                if not have_matching_fields(val.d_value, self.d_value):
                    raise ValueError(
                        'CompoundListField assignment must be a '
                        'list containing matching CompoundValues.')
            else:
                # For all remaining values, just ensure they match the first.
                if val.d_value is not value[0].d_value:
                    raise ValueError(
                        'CompoundListField assignment cannot contain '
                        'multiple CompoundValue types as sources.')

        data[self.d_key] = self.filter_input([i.d_data for i in value],
                                             error=error)


class CompoundDictField(BaseField, Generic[TK, TC]):
    """A field consisting of key-indexed instances of a compound-value.

    Element access returns the sub-field, allowing nested field access.
    ie: mylist[10].fieldattr = 'foo'
    """

    def __init__(self,
                 d_key: str,
                 keytype: Type[TK],
                 valuetype: TC,
                 store_default: bool = True) -> None:
        super().__init__(d_key)
        self.d_value = valuetype

        # This doesnt actually exist for us, but want the type-checker
        # to think it does (see TYPE_CHECKING note below).
        self.d_data: Any
        self.d_keytype = keytype
        self._store_default = store_default

    # noinspection DuplicatedCode
    def filter_input(self, data: Any, error: bool) -> dict:
        if not isinstance(data, dict):
            if error:
                raise TypeError('dict value expected')
            logging.error('Ignoring non-dict data for %s: %s', self, data)
            data = {}
        data_out = {}
        for key, val in data.items():
            if not isinstance(key, self.d_keytype):
                if error:
                    raise TypeError('invalid key type')
                logging.error('Ignoring invalid key type for %s: %s', self,
                              data)
                continue
            data_out[key] = self.d_value.filter_input(val, error=error)
        return data_out

    def get_default_data(self) -> dict:
        return {}

    def prune_data(self, data: Any) -> bool:
        # Run pruning on all individual entries' data through our child field.
        # However we don't *completely* prune values from the list since that
        # would change it.
        for subdata in data.values():
            self.d_value.prune_fields_data(subdata)

        # We can also optionally prune the whole list if empty and allowed.
        return not data and not self._store_default

    # ONLY overriding these in type-checker land to clarify types.
    # (see note in BaseField)
    # noinspection DuplicatedCode
    if TYPE_CHECKING:

        @overload
        def __get__(self,
                    obj: None,
                    cls: Any = None) -> CompoundDictField[TK, TC]:
            ...

        @overload
        def __get__(self,
                    obj: Any,
                    cls: Any = None) -> BoundCompoundDictField[TK, TC]:
            ...

        def __get__(self, obj: Any, cls: Any = None) -> Any:
            ...

        # Note:
        # When setting the dict, we tell the type-checker that we also accept
        # a raw dict of CompoundValue objects, but at runtime we actually
        # always deal with BoundCompoundValue objects (see note in
        # BoundCompoundDictField for why we accept CompoundValue objs)
        @overload
        def __set__(self, obj: Any, value: Dict[TK, TC]) -> None:
            ...

        @overload
        def __set__(self, obj: Any, value: BoundCompoundDictField[TK,
                                                                  TC]) -> None:
            ...

        def __set__(self, obj: Any, value: Any) -> None:
            ...

    def get_with_data(self, data: Any) -> Any:
        assert self.d_key in data
        return BoundCompoundDictField(self, data[self.d_key])

    def set_with_data(self, data: Any, value: Any, error: bool) -> Any:

        # If we were passed a BoundCompoundDictField,
        # simply convert it to a flat dict of BoundCompoundValue objects which
        # is what we work with natively here.
        if isinstance(value, BoundCompoundDictField):
            value = dict(value.items())

        if not isinstance(value, dict):
            raise TypeError('CompoundDictField expected dict value on set.')

        # Allow assigning only from a sequence of our existing children.
        # (could look into expanding this to other children if we can
        # be sure the underlying data will line up; for example two
        # CompoundListFields with different child_field values should not
        # be inter-assignable.
        if (not all(isinstance(i, BoundCompoundValue)
                    for i in value.values())):
            raise ValueError('CompoundDictField assignment must be a '
                             'dict containing only BoundCompoundValues.')

        # Make sure the data all has the same CompoundValue type and
        # compare that type against ours once to make sure its fields match.
        # (this will not allow passing CompoundValues from multiple sources
        # but I don't know if that would ever come up..)
        first_value: Any = None
        for i, val in enumerate(value.values()):
            if i == 0:
                first_value = val.d_value
                # Do the full field comparison on the first value only..
                if not have_matching_fields(val.d_value, self.d_value):
                    raise ValueError(
                        'CompoundListField assignment must be a '
                        'list containing matching CompoundValues.')
            else:
                # For all remaining values, just ensure they match the first.
                if val.d_value is not first_value:
                    raise ValueError(
                        'CompoundListField assignment cannot contain '
                        'multiple CompoundValue types as sources.')

        data[self.d_key] = self.filter_input(
            {key: val.d_data
             for key, val in value.items()}, error=error)
