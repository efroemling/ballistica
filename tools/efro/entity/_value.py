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
"""Value types for the entity system."""

from __future__ import annotations

import datetime
import inspect
import logging
from collections import abc
from enum import Enum
from typing import TYPE_CHECKING, TypeVar, Generic
# Our Pylint class_generics_filter gives us a false-positive unused-import.
from typing import Tuple, Optional  # pylint: disable=W0611

from efro.entity._base import DataHandler, BaseField
from efro.entity.util import compound_eq

if TYPE_CHECKING:
    from typing import Optional, Set, List, Dict, Any, Type

T = TypeVar('T')
TE = TypeVar('TE', bound=Enum)

_sanity_tested_types: Set[Type] = set()
_type_field_cache: Dict[Type, Dict[str, BaseField]] = {}


class TypedValue(DataHandler, Generic[T]):
    """Base class for all value types dealing with a single data type."""


class SimpleValue(TypedValue[T]):
    """Standard base class for simple single-value types.

    This class provides enough functionality to handle most simple
    types such as int/float/etc without too many subclass overrides.
    """

    def __init__(self,
                 default: T,
                 store_default: bool,
                 target_type: Type = None,
                 convert_source_types: Tuple[Type, ...] = (),
                 allow_none: bool = False) -> None:
        """Init the value field.

        If store_default is False, the field value will not be included
        in final entity data if it is a default value. Be sure to set
        this to True for any fields that will be used for server-side
        queries so they are included in indexing.
        target_type and convert_source_types are used in the default
        filter_input implementation; if passed in data's type is present
        in convert_source_types, a target_type will be instantiated
        using it. (allows for simple conversions to bool, int, etc)
        Data will also be allowed through untouched if it matches target_type.
        (types needing further introspection should override filter_input).
        Lastly, the value of allow_none is also used in filter_input for
        whether values of None should be allowed.
        """
        super().__init__()

        self._store_default = store_default
        self._target_type = target_type
        self._convert_source_types = convert_source_types
        self._allow_none = allow_none

        # We store _default_data in our internal data format so need
        # to run user-facing value through our input filter.
        # Make sure we do this last since filter_input depends on above vals.
        self._default_data: T = self.filter_input(default, error=True)

    def __repr__(self) -> str:
        if self._target_type is not None:
            return f'<Value of type {self._target_type.__name__}>'
        return '<Value of unknown type>'

    def get_default_data(self) -> Any:
        return self._default_data

    def prune_data(self, data: Any) -> bool:
        return not self._store_default and data == self._default_data

    def filter_input(self, data: Any, error: bool) -> Any:

        # Let data pass through untouched if its already our target type
        if self._target_type is not None:
            if isinstance(data, self._target_type):
                return data

        # ...and also if its None and we're into that sort of thing.
        if self._allow_none and data is None:
            return data

        # If its one of our convertible types, convert.
        if (self._convert_source_types
                and isinstance(data, self._convert_source_types)):
            assert self._target_type is not None
            return self._target_type(data)
        if error:
            errmsg = (f'value of type {self._target_type} or None expected'
                      if self._allow_none else
                      f'value of type {self._target_type} expected')
            errmsg += f'; got {type(data)}'
            raise TypeError(errmsg)
        errmsg = f'Ignoring incompatible data for {self};'
        errmsg += (f' expected {self._target_type} or None;'
                   if self._allow_none else f'expected {self._target_type};')
        errmsg += f' got {type(data)}'
        logging.error(errmsg)
        return self.get_default_data()


class StringValue(SimpleValue[str]):
    """Value consisting of a single string."""

    def __init__(self, default: str = '', store_default: bool = True) -> None:
        super().__init__(default, store_default, str)


class OptionalStringValue(SimpleValue[Optional[str]]):
    """Value consisting of a single string or None."""

    def __init__(self,
                 default: Optional[str] = None,
                 store_default: bool = True) -> None:
        super().__init__(default, store_default, str, allow_none=True)


class BoolValue(SimpleValue[bool]):
    """Value consisting of a single bool."""

    def __init__(self,
                 default: bool = False,
                 store_default: bool = True) -> None:
        super().__init__(default, store_default, bool, (int, float))


class OptionalBoolValue(SimpleValue[Optional[bool]]):
    """Value consisting of a single bool or None."""

    def __init__(self,
                 default: Optional[bool] = None,
                 store_default: bool = True) -> None:
        super().__init__(default,
                         store_default,
                         bool, (int, float),
                         allow_none=True)


def verify_time_input(data: Any, error: bool, allow_none: bool) -> Any:
    """Checks input data for time values."""
    pytz_utc: Any

    # We don't *require* pytz since it must be installed through pip
    # but it is used by firestore client for its date values
    # (in which case it should be installed as a dependency anyway).
    try:
        import pytz
        pytz_utc = pytz.utc
    except ModuleNotFoundError:
        pytz_utc = None

    # Filter unallowed None values.
    if not allow_none and data is None:
        if error:
            raise ValueError('datetime value cannot be None')
        logging.error('ignoring datetime value of None')
        data = (None if allow_none else datetime.datetime.now(
            datetime.timezone.utc))

    # Parent filter_input does what we need, but let's just make
    # sure we *only* accept datetime values that know they're UTC.
    elif (isinstance(data, datetime.datetime)
          and data.tzinfo is not datetime.timezone.utc
          and (pytz_utc is None or data.tzinfo is not pytz_utc)):
        if error:
            raise ValueError(
                'datetime values must have timezone set as timezone.utc')
        logging.error(
            'ignoring datetime value without timezone.utc set: %s %s',
            type(datetime.timezone.utc), type(data.tzinfo))
        data = (None if allow_none else datetime.datetime.now(
            datetime.timezone.utc))
    return data


class DateTimeValue(SimpleValue[datetime.datetime]):
    """Value consisting of a datetime.datetime object.

    The default value for this is always the current time in UTC.
    """

    def __init__(self, store_default: bool = True) -> None:
        # Pass dummy datetime value as default just to satisfy constructor;
        # we override get_default_data though so this doesn't get used.
        dummy_default = datetime.datetime.now(datetime.timezone.utc)
        super().__init__(dummy_default, store_default, datetime.datetime)

    def get_default_data(self) -> Any:
        # For this class we don't use a static default value;
        # default is always now.
        return datetime.datetime.now(datetime.timezone.utc)

    def filter_input(self, data: Any, error: bool) -> Any:
        data = verify_time_input(data, error, allow_none=False)
        return super().filter_input(data, error)


class OptionalDateTimeValue(SimpleValue[Optional[datetime.datetime]]):
    """Value consisting of a datetime.datetime object or None."""

    def __init__(self, store_default: bool = True) -> None:
        super().__init__(None,
                         store_default,
                         datetime.datetime,
                         allow_none=True)

    def filter_input(self, data: Any, error: bool) -> Any:
        data = verify_time_input(data, error, allow_none=True)
        return super().filter_input(data, error)


class IntValue(SimpleValue[int]):
    """Value consisting of a single int."""

    def __init__(self, default: int = 0, store_default: bool = True) -> None:
        super().__init__(default, store_default, int, (bool, float))


class OptionalIntValue(SimpleValue[Optional[int]]):
    """Value consisting of a single int or None"""

    def __init__(self,
                 default: int = None,
                 store_default: bool = True) -> None:
        super().__init__(default,
                         store_default,
                         int, (bool, float),
                         allow_none=True)


class FloatValue(SimpleValue[float]):
    """Value consisting of a single float."""

    def __init__(self,
                 default: float = 0.0,
                 store_default: bool = True) -> None:
        super().__init__(default, store_default, float, (bool, int))


class OptionalFloatValue(SimpleValue[Optional[float]]):
    """Value consisting of a single float or None."""

    def __init__(self,
                 default: float = None,
                 store_default: bool = True) -> None:
        super().__init__(default,
                         store_default,
                         float, (bool, int),
                         allow_none=True)


class Float3Value(SimpleValue[Tuple[float, float, float]]):
    """Value consisting of 3 floats."""

    def __init__(self,
                 default: Tuple[float, float, float] = (0.0, 0.0, 0.0),
                 store_default: bool = True) -> None:
        super().__init__(default, store_default)

    def __repr__(self) -> str:
        return '<Value of type float3>'

    def filter_input(self, data: Any, error: bool) -> Any:
        if (not isinstance(data, abc.Sequence) or len(data) != 3
                or any(not isinstance(i, (int, float)) for i in data)):
            if error:
                raise TypeError('Sequence of 3 float values expected.')
            logging.error('Ignoring non-3-float-sequence data for %s: %s',
                          self, data)
            data = self.get_default_data()

        # Actually store as list.
        return [float(data[0]), float(data[1]), float(data[2])]

    def filter_output(self, data: Any) -> Any:
        """Override."""
        assert len(data) == 3
        return tuple(data)


class BaseEnumValue(TypedValue[T]):
    """Value class for storing Python Enums.

    Internally enums are stored as their corresponding int/str/etc. values.
    """

    def __init__(self,
                 enumtype: Type[T],
                 default: Optional[T] = None,
                 store_default: bool = True,
                 allow_none: bool = False) -> None:
        super().__init__()
        assert issubclass(enumtype, Enum)

        vals: List[T] = list(enumtype)

        # Bit of sanity checking: make sure this enum has at least
        # one value and that its underlying values are all of simple
        # json-friendly types.
        if not vals:
            raise TypeError(f'enum {enumtype} has no values')
        for val in vals:
            assert isinstance(val, Enum)
            if not isinstance(val.value, (int, bool, float, str)):
                raise TypeError(f'enum value {val} has an invalid'
                                f' value type {type(val.value)}')
        self._enumtype: Type[Enum] = enumtype
        self._store_default: bool = store_default
        self._allow_none: bool = allow_none

        # We store default data is internal format so need to run
        # user-provided value through input filter.
        # Make sure to set this last since it could depend on other
        # stuff we set here.
        if default is None and not self._allow_none:
            # Special case: we allow passing None as default even if
            # we don't support None as a value; in that case we sub
            # in the first enum value.
            default = vals[0]
        self._default_data: Enum = self.filter_input(default, error=True)

    def get_default_data(self) -> Any:
        return self._default_data

    def prune_data(self, data: Any) -> bool:
        return not self._store_default and data == self._default_data

    def filter_input(self, data: Any, error: bool) -> Any:

        # Allow passing in enum objects directly of course.
        if isinstance(data, self._enumtype):
            data = data.value
        elif self._allow_none and data is None:
            pass
        else:
            # At this point we assume its an enum value
            try:
                self._enumtype(data)
            except ValueError:
                if error:
                    raise ValueError(
                        f'Invalid value for {self._enumtype}: {data}'
                    ) from None
                logging.error('Ignoring invalid value for %s: %s',
                              self._enumtype, data)
                data = self._default_data
        return data

    def filter_output(self, data: Any) -> Any:
        if self._allow_none and data is None:
            return None
        return self._enumtype(data)


class EnumValue(BaseEnumValue[TE]):
    """Value class for storing Python Enums.

    Internally enums are stored as their corresponding int/str/etc. values.
    """

    def __init__(self,
                 enumtype: Type[TE],
                 default: TE = None,
                 store_default: bool = True) -> None:
        super().__init__(enumtype, default, store_default, allow_none=False)


class OptionalEnumValue(BaseEnumValue[Optional[TE]]):
    """Value class for storing Python Enums (or None).

    Internally enums are stored as their corresponding int/str/etc. values.
    """

    def __init__(self,
                 enumtype: Type[TE],
                 default: TE = None,
                 store_default: bool = True) -> None:
        super().__init__(enumtype, default, store_default, allow_none=True)


class CompoundValue(DataHandler):
    """A value containing one or more named child fields of its own.

    Custom classes can be defined that inherit from this and include
    any number of Field instances within themself.
    """

    def __init__(self, store_default: bool = True) -> None:
        super().__init__()
        self._store_default = store_default

        # Run sanity checks on this type if we haven't.
        self.run_type_sanity_checks()

    def __eq__(self, other: Any) -> Any:
        # Allow comparing to compound and bound-compound objects.
        return compound_eq(self, other)

    def get_default_data(self) -> dict:
        return {}

    # NOTE: once we've got bound-compound-fields working in mypy
    # we should get rid of this here.
    # For now it needs to be here though since bound-compound fields
    # come across as these in type-land.
    def reset(self) -> None:
        """Resets data to default."""
        raise ValueError('Unbound CompoundValue cannot be reset.')

    def filter_input(self, data: Any, error: bool) -> dict:
        if not isinstance(data, dict):
            if error:
                raise TypeError('dict value expected')
            logging.error('Ignoring non-dict data for %s: %s', self, data)
            data = {}
        assert isinstance(data, dict)
        self.apply_fields_to_data(data, error=error)
        return data

    def prune_data(self, data: Any) -> bool:
        # Let all of our sub-fields prune themselves..
        self.prune_fields_data(data)

        # Now we can optionally prune ourself completely if there's
        # nothing left in our data dict...
        return not data and not self._store_default

    def prune_fields_data(self, d_data: Dict[str, Any]) -> None:
        """Given a CompoundValue and data, prune any unnecessary data.
        will include those set to default values with store_default False.
        """

        # Allow all fields to take a pruning pass.
        assert isinstance(d_data, dict)
        for field in self.get_fields().values():
            assert isinstance(field.d_key, str)

            # This is supposed to be valid data so there should be *something*
            # there for all fields.
            if field.d_key not in d_data:
                raise RuntimeError(f'expected to find {field.d_key} in data'
                                   f' for {self}; got data {d_data}')

            # Now ask the field if this data is necessary.  If not, prune it.
            if field.prune_data(d_data[field.d_key]):
                del d_data[field.d_key]

    def apply_fields_to_data(self, d_data: Dict[str, Any],
                             error: bool) -> None:
        """Apply all of our fields to target data.

        If error is True, exceptions will be raised for invalid data;
        otherwise it will be overwritten (with logging notices emitted).
        """
        assert isinstance(d_data, dict)
        for field in self.get_fields().values():
            assert isinstance(field.d_key, str)

            # First off, make sure *something* is there for this field.
            if field.d_key not in d_data:
                d_data[field.d_key] = field.get_default_data()

            # Now let the field tweak the data as needed so its valid.
            d_data[field.d_key] = field.filter_input(d_data[field.d_key],
                                                     error=error)

    def __repr__(self) -> str:
        if not hasattr(self, 'd_data'):
            return f'<unbound {type(self).__name__} at {hex(id(self))}>'
        fstrs: List[str] = []
        assert isinstance(self, CompoundValue)
        for field in self.get_fields():
            fstrs.append(str(field) + '=' + repr(getattr(self, field)))
        return type(self).__name__ + '(' + ', '.join(fstrs) + ')'

    @classmethod
    def get_fields(cls) -> Dict[str, BaseField]:
        """Return all field instances for this type."""
        assert issubclass(cls, CompoundValue)

        # If we haven't yet, calculate and cache a complete list of fields
        # for this exact type.
        if cls not in _type_field_cache:
            fields: Dict[str, BaseField] = {}
            for icls in inspect.getmro(cls):
                for name, field in icls.__dict__.items():
                    if isinstance(field, BaseField):
                        fields[name] = field
            _type_field_cache[cls] = fields
        retval: Dict[str, BaseField] = _type_field_cache[cls]
        assert isinstance(retval, dict)
        return retval

    @classmethod
    def run_type_sanity_checks(cls) -> None:
        """Given a type, run one-time sanity checks on it.

        These tests ensure child fields are using valid
        non-repeating names/etc.
        """
        if cls not in _sanity_tested_types:
            _sanity_tested_types.add(cls)

            # Make sure all embedded fields have a key set and there are no
            # duplicates.
            field_keys: Set[str] = set()
            for field in cls.get_fields().values():
                assert isinstance(field.d_key, str)
                if field.d_key is None:
                    raise RuntimeError(f'Child field {field} under {cls}'
                                       'has d_key None')
                if field.d_key == '':
                    raise RuntimeError(f'Child field {field} under {cls}'
                                       'has empty d_key')

                # Allow alphanumeric and underscore only.
                if not field.d_key.replace('_', '').isalnum():
                    raise RuntimeError(
                        f'Child field "{field.d_key}" under {cls}'
                        f' contains invalid characters; only alphanumeric'
                        f' and underscore allowed.')
                if field.d_key in field_keys:
                    raise RuntimeError('Multiple child fields with key'
                                       f' "{field.d_key}" found in {cls}')
                field_keys.add(field.d_key)
