# Released under the MIT License. See LICENSE for details.
#
"""Core components of dataclassio."""

from __future__ import annotations

import dataclasses
import typing
import datetime
from enum import Enum
from typing import TYPE_CHECKING, get_args

# noinspection PyProtectedMember
from typing import _AnnotatedAlias  # type: ignore

if TYPE_CHECKING:
    from typing import Any, Callable

# Types which we can pass through as-is.
SIMPLE_TYPES = {int, bool, str, float, type(None)}

# Attr name for dict of extra attributes included on dataclass instances.
# Note that this is only added if extra attributes are present.
EXTRA_ATTRS_ATTR = '_DCIOEXATTRS'


def _raise_type_error(
    fieldpath: str, valuetype: type, expected: tuple[type, ...]
) -> None:
    """Raise an error when a field value's type does not match expected."""
    assert isinstance(expected, tuple)
    assert all(isinstance(e, type) for e in expected)
    if len(expected) == 1:
        expected_str = expected[0].__name__
    else:
        expected_str = ' | '.join(t.__name__ for t in expected)
    raise TypeError(
        f'Invalid value type for "{fieldpath}";'
        f' expected "{expected_str}", got'
        f' "{valuetype.__name__}".'
    )


class Codec(Enum):
    """Specifies expected data format exported to or imported from."""

    # Use only types that will translate cleanly to/from json: lists,
    # dicts with str keys, bools, ints, floats, and None.
    JSON = 'json'

    # Mostly like JSON but passes bytes and datetime objects through
    # as-is instead of converting them to json-friendly types.
    FIRESTORE = 'firestore'


class IOExtendedData:
    """A class that data types can inherit from for extra functionality."""

    def will_output(self) -> None:
        """Called before data is sent to an outputter.

        Can be overridden to validate or filter data before
        sending it on its way.
        """

    @classmethod
    def will_input(cls, data: dict) -> None:
        """Called on raw data before a class instance is created from it.

        Can be overridden to migrate old data formats to new, etc.
        """


def _is_valid_for_codec(obj: Any, codec: Codec) -> bool:
    """Return whether a value consists solely of json-supported types.

    Note that this does not include things like tuples which are
    implicitly translated to lists by python's json module.
    """
    if obj is None:
        return True

    objtype = type(obj)
    if objtype in (int, float, str, bool):
        return True
    if objtype is dict:
        # JSON 'objects' supports only string dict keys, but all value types.
        return all(
            isinstance(k, str) and _is_valid_for_codec(v, codec)
            for k, v in obj.items()
        )
    if objtype is list:
        return all(_is_valid_for_codec(elem, codec) for elem in obj)

    # A few things are valid in firestore but not json.
    if issubclass(objtype, datetime.datetime) or objtype is bytes:
        return codec is Codec.FIRESTORE

    return False


class IOAttrs:
    """For specifying io behavior in annotations.

    'storagename', if passed, is the name used when storing to json/etc.
    'store_default' can be set to False to avoid writing values when equal
        to the default value. Note that this requires the dataclass field
        to define a default or default_factory or for its IOAttrs to
        define a soft_default value.
    'whole_days', if True, requires datetime values to be exactly on day
        boundaries (see efro.util.utc_today()).
    'whole_hours', if True, requires datetime values to lie exactly on hour
        boundaries (see efro.util.utc_this_hour()).
    'whole_minutes', if True, requires datetime values to lie exactly on minute
        boundaries (see efro.util.utc_this_minute()).
    'soft_default', if passed, injects a default value into dataclass
        instantiation when the field is not present in the input data.
        This allows dataclasses to add new non-optional fields while
        gracefully 'upgrading' old data. Note that when a soft_default is
        present it will take precedence over field defaults when determining
        whether to store a value for a field with store_default=False
        (since the soft_default value is what we'll get when reading that
        same data back in when the field is omitted).
    'soft_default_factory' is similar to 'default_factory' in dataclass
        fields; it should be used instead of 'soft_default' for mutable types
        such as lists to prevent a single default object from unintentionally
        changing over time.
    """

    # A sentinel object to detect if a parameter is supplied or not.  Use
    # a class to give it a better repr.
    class _MissingType:
        pass

    MISSING = _MissingType()

    storagename: str | None = None
    store_default: bool = True
    whole_days: bool = False
    whole_hours: bool = False
    whole_minutes: bool = False
    soft_default: Any = MISSING
    soft_default_factory: Callable[[], Any] | _MissingType = MISSING

    def __init__(
        self,
        storagename: str | None = storagename,
        store_default: bool = store_default,
        whole_days: bool = whole_days,
        whole_hours: bool = whole_hours,
        whole_minutes: bool = whole_minutes,
        soft_default: Any = MISSING,
        soft_default_factory: Callable[[], Any] | _MissingType = MISSING,
    ):
        # Only store values that differ from class defaults to keep
        # our instances nice and lean.
        cls = type(self)
        if storagename != cls.storagename:
            self.storagename = storagename
        if store_default != cls.store_default:
            self.store_default = store_default
        if whole_days != cls.whole_days:
            self.whole_days = whole_days
        if whole_hours != cls.whole_hours:
            self.whole_hours = whole_hours
        if whole_minutes != cls.whole_minutes:
            self.whole_minutes = whole_minutes
        if soft_default is not cls.soft_default:
            # Do what dataclasses does with its default types and
            # tell the user to use factory for mutable ones.
            if isinstance(soft_default, (list, dict, set)):
                raise ValueError(
                    f'mutable {type(soft_default)} is not allowed'
                    f' for soft_default; use soft_default_factory.'
                )
            self.soft_default = soft_default
        if soft_default_factory is not cls.soft_default_factory:
            self.soft_default_factory = soft_default_factory
            if self.soft_default is not cls.soft_default:
                raise ValueError(
                    'Cannot set both soft_default and soft_default_factory'
                )

    def validate_for_field(self, cls: type, field: dataclasses.Field) -> None:
        """Ensure the IOAttrs instance is ok to use with the provided field."""

        # Turning off store_default requires the field to have either
        # a default or a a default_factory or for us to have soft equivalents.

        if not self.store_default:
            field_default_factory: Any = field.default_factory
            if (
                field_default_factory is dataclasses.MISSING
                and field.default is dataclasses.MISSING
                and self.soft_default is self.MISSING
                and self.soft_default_factory is self.MISSING
            ):
                raise TypeError(
                    f'Field {field.name} of {cls} has'
                    f' neither a default nor a default_factory'
                    f' and IOAttrs contains neither a soft_default'
                    f' nor a soft_default_factory;'
                    f' store_default=False cannot be set for it.'
                )

    def validate_datetime(
        self, value: datetime.datetime, fieldpath: str
    ) -> None:
        """Ensure a datetime value meets our value requirements."""
        if self.whole_days:
            if any(
                x != 0
                for x in (
                    value.hour,
                    value.minute,
                    value.second,
                    value.microsecond,
                )
            ):
                raise ValueError(
                    f'Value {value} at {fieldpath} is not a whole day.'
                )
        elif self.whole_hours:
            if any(
                x != 0 for x in (value.minute, value.second, value.microsecond)
            ):
                raise ValueError(
                    f'Value {value} at {fieldpath}' f' is not a whole hour.'
                )
        elif self.whole_minutes:
            if any(x != 0 for x in (value.second, value.microsecond)):
                raise ValueError(
                    f'Value {value} at {fieldpath}' f' is not a whole minute.'
                )


def _get_origin(anntype: Any) -> Any:
    """Given a type annotation, return its origin or itself if there is none.

    This differs from typing.get_origin in that it will never return None.
    This lets us use the same code path for handling typing.List
    that we do for handling list, which is good since they can be used
    interchangeably in annotations.
    """
    origin = typing.get_origin(anntype)
    return anntype if origin is None else origin


def _parse_annotated(anntype: Any) -> tuple[Any, IOAttrs | None]:
    """Parse Annotated() constructs, returning annotated type & IOAttrs."""
    # If we get an Annotated[foo, bar, eep] we take
    # foo as the actual type, and we look for IOAttrs instances in
    # bar/eep to affect our behavior.
    ioattrs: IOAttrs | None = None
    if isinstance(anntype, _AnnotatedAlias):
        annargs = get_args(anntype)
        for annarg in annargs[1:]:
            if isinstance(annarg, IOAttrs):
                if ioattrs is not None:
                    raise RuntimeError(
                        'Multiple IOAttrs instances found for a'
                        ' single annotation; this is not supported.'
                    )
                ioattrs = annarg

            # I occasionally just throw a 'x' down when I mean IOAttrs('x');
            # catch these mistakes.
            elif isinstance(annarg, (str, int, float, bool)):
                raise RuntimeError(
                    f'Raw {type(annarg)} found in Annotated[] entry:'
                    f' {anntype}; this is probably not what you intended.'
                )
        anntype = annargs[0]
    return anntype, ioattrs
