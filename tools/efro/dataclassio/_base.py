# Released under the MIT License. See LICENSE for details.
#
"""Core components of dataclassio."""

from __future__ import annotations

import dataclasses
import typing
import datetime
from enum import Enum
from typing import TYPE_CHECKING, get_args, override, final

# noinspection PyProtectedMember
from typing import _AnnotatedAlias  # type: ignore

if TYPE_CHECKING:
    from typing import Any, Callable, Literal, ClassVar, Self

# Types which we can pass through as-is.
SIMPLE_TYPES = {int, bool, str, float, type(None)}

# Attr name for dict of extra attributes included on dataclass
# instances. Note that this is only added if extra attributes are
# present.
EXTRA_ATTRS_ATTR = '_DCIOEXATTRS'

# Attr name for a bool attr for flagging data as lossy, which means it
# may have been modified in some way during load and should generally
# not be written back out.
LOSSY_ATTR = '_DCIOLOSSY'


class Codec(Enum):
    """Specifies expected data format exported to or imported from."""

    #: Use only types that will translate cleanly to/from json - lists,
    #: dicts with str keys, bools, ints, floats, and None.
    JSON = 'json'

    #: Mostly like JSON but passes bytes and datetime objects through
    #: as-is instead of converting them to json-friendly types.
    FIRESTORE = 'firestore'


class IOExtendedData:
    """A class types can inherit from for extra functionality."""

    def will_output(self) -> None:
        """Called before data is sent to an outputter.

        Can be overridden to validate or filter data before
        sending it on its way.
        """

    @classmethod
    def will_input(cls, data: dict) -> None:
        """Called on data before a class instance is created from it.

        Can be overridden to migrate old data formats to new, etc.
        """

    def did_input(self) -> None:
        """Called on a class instance after created from data.

        Can be useful to correct values from the db, etc. in the
        type-safe form.
        """

    # pylint: disable=useless-return

    @classmethod
    def handle_input_error(cls, exc: Exception) -> Self | None:
        """Called when an error occurs during input decoding.

        This allows a type to optionally return substitute data
        to be used in place of the failed decode. If it returns
        None, the original exception is re-raised.

        It is generally a bad idea to apply catch-alls such as this,
        as it can lead to silent data loss. This should only be used
        in specific cases such as user settings where an occasional
        reset is harmless and is preferable to keeping all contained
        enums and other values backward compatible indefinitely.
        """
        del exc  # Unused.

        # By default we let things fail.
        return None

    # pylint: enable=useless-return


class IOMultiType[EnumT: Enum]:
    """A base class for types that can map to multiple dataclass types.

    This enables usage of high level base classes (for example a
    'Message' type) in annotations, with dataclassio automatically
    serializing & deserializing dataclass subclasses based on their type
    ('MessagePing', 'MessageChat', etc.)

    Standard usage involves creating a class which inherits from this
    one which acts as a 'registry', and then creating dataclass classes
    inheriting from that registry class. Dataclassio will then do the
    right thing when that registry class is used in type annotations.

    See tests/test_efro/test_dataclassio.py for examples.
    """

    @classmethod
    def get_type(cls, type_id: EnumT) -> type[Self]:
        """Return a specific subclass given a type-id."""
        raise NotImplementedError()

    @final
    @classmethod
    def get_type_cached(cls, type_id: EnumT) -> type[Self]:
        """Version of :meth:`get_type()` with caching.

        Generally end-users of a multi-type class should use this
        instead of calling :meth:`get_type()` directly. It lazily caches
        looked up types so can be significantly more efficient with
        large multitypes and repeat lookups.
        """
        storage: dict[EnumT, type[Self]] | None = getattr(
            cls, '_iomt_tp_cache', None
        )
        if storage is None:
            storage = {}
            setattr(cls, '_iomt_tp_cache', storage)
        tp: type[Self] | None = storage.get(type_id)
        if tp is None:
            tp = storage[type_id] = cls.get_type(type_id)
        return tp

    @classmethod
    def get_type_id(cls) -> EnumT:
        """Return the type-id for this subclass."""
        raise NotImplementedError()

    @classmethod
    def get_type_id_type(cls) -> type[EnumT]:
        """Return the Enum type this class uses as its type-id."""
        out: type[EnumT] = cls.__orig_bases__[0].__args__[0]  # type: ignore
        assert issubclass(out, Enum)
        return out

    @classmethod
    def get_type_id_storage_name(cls) -> str:
        """Return the key used to store type id in serialized data.

        The default is an obscure value so that it does not conflict
        with members of individual type attrs, but in some cases one
        might prefer to serialize it to something simpler like 'type' by
        overriding this call. One just needs to make sure that no
        encompassed types serialize anything to 'type' themself.
        """
        return '_dciotype'

    # NOTE: Currently (Jan 2025) mypy complains if overrides annotate
    # return type of 'Self | None'. Substituting their own explicit type
    # works though (see test_dataclassio).
    @classmethod
    def get_unknown_type_fallback(cls) -> Self | None:
        """Return a fallback object in cases of unrecognized types.

        This can allow newer data to remain readable in older
        environments. Use caution with this option, however, as it
        effectively modifies data.
        """
        return None


class IOAttrs:
    """Used to customize dataclassio behavior for particular fields.

    Example: specify that 'value2' will be stored as 'v2'::

        @ioprepped
        @dataclass
        class MyData:
            value1: int = 1
            value2: Annotated[int, IOAttrs('v2')] = 2

        >>> print(dataclass_to_dict(MyData()))

        # Output: {'value1': 1, 'v2': 2}

    Providing fixed storagenames for all fields can allow the freedom to
    rename fields later without worrying about breaking existing data.
    """

    # A sentinel object to detect if a parameter is supplied or not. Use
    # a class to give it a better repr.
    class _MissingType:

        @override
        def __repr__(self) -> str:
            return '<MISSING>'

    #: :meta private:
    MISSING = _MissingType()

    #: If passed, is the name used when storing to json/etc.
    storagename: str | None = None

    #: Can be set to ``False`` to avoid writing values when equal to the
    #: default value. Note that this requires the dataclass field to
    #: define a ``default`` or ``default_factory`` or for its ``IOAttrs``
    #: to define a ``soft_default`` value.
    store_default: bool = True

    #: If True, requires datetime values to be exactly on day boundaries
    #: (see :meth:`efro.util.utc_today()`).
    whole_days: bool = False

    #: If ``True``, requires datetime values to lie exactly on hour
    #: boundaries (see :meth:`efro.util.utc_this_hour()`).
    whole_hours: bool = False

    #: If ``True``, requires ``datetime.datetime`` values to lie exactly on
    #: minute boundaries (see :meth:`efro.util.utc_this_minute()`).
    whole_minutes: bool = False

    #: If ``True``, values of type ``datetime.datetime`` (in json codec)
    #: and ``datetime.timedelta`` (in all codecs) will be stored as single
    #: float timestamp/seconds values instead of the default list of
    #: ints. This is more concise but introduces the possibility of
    #: restored values varying slightly from originals due to
    #: floating-point precision limitations.
    float_times: bool = False

    #: If passed, injects a default value into dataclass instantiation
    #: when the field is not present in the input data. This allows
    #: dataclasses to add new non-optional fields while gracefully
    #: 'upgrading' old data. Note that when a soft-default is present it
    #: will take precedence over field defaults when determining whether
    #: to store a value for a field with ``store_default=False`` (since
    #: the soft_default value is what we'll get when reading that same
    #: data back in when the field is omitted).
    soft_default: Any = MISSING

    #: Is similar to 'default_factory' in dataclass fields; it should be
    #: used instead of 'soft_default' for mutable types such as lists to
    #: prevent a single default object from unintentionally changing over
    #: time.
    soft_default_factory: Callable[[], Any] | _MissingType = MISSING

    #: If provided, specifies an enum value that can be substituted in
    #: the case of unrecognized input values. This can allow newer data
    #: to remain loadable in older environments. Note that 'lossy' must
    #: be enabled in the top level load call for this to apply, since it
    #: can fundamentally modify data.
    enum_fallback: Enum | None = None

    #: If provided for a string, hints as to whether multi line values
    #: are allowed/expected. Can be referenced when creating UI for
    #: editing the value. Does not actually affect value input/output.
    multiline: bool | None = None

    def __init__(
        self,
        storagename: str | None = storagename,
        *,
        store_default: bool = store_default,
        whole_days: bool = whole_days,
        whole_hours: bool = whole_hours,
        whole_minutes: bool = whole_minutes,
        float_times: bool = float_times,
        soft_default: Any = MISSING,
        soft_default_factory: Callable[[], Any] | _MissingType = MISSING,
        enum_fallback: Enum | None = None,
        multiline: bool | None = None,
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
        if float_times != cls.float_times:
            self.float_times = float_times
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
        if enum_fallback is not cls.enum_fallback:
            self.enum_fallback = enum_fallback
        if multiline is not cls.multiline:
            self.multiline = multiline

    def validate_for_field(self, cls: type, field: dataclasses.Field) -> None:
        """Ensure the IOAttrs is ok to use with provided field."""

        # Turning off store_default requires the field to have either a
        # default or a default_factory or for us to have soft
        # equivalents.

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
        # JSON 'objects' supports only string dict keys, but all value
        # types.
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


def _get_origin(anntype: Any) -> Any:
    """Given a type annotation, return its origin or itself if there is none.

    This differs from typing.get_origin in that it will never return
    None. This lets us use the same code path for handling typing.List
    that we do for handling list, which is good since they can be used
    interchangeably in annotations.
    """
    origin = typing.get_origin(anntype)
    return anntype if origin is None else origin


def parse_annotated(anntype: Any) -> tuple[Any, IOAttrs | None]:
    """Parse Annotated() constructs, returning annotated type & IOAttrs."""

    # If we get an Annotated[foo, bar, eep] we take foo as the actual
    # type, and we look for IOAttrs instances in bar/eep to affect our
    # behavior.
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

            # I occasionally just throw a 'x' down when I mean
            # IOAttrs('x'); catch these mistakes.
            elif isinstance(annarg, (str, int, float, bool)):
                raise RuntimeError(
                    f'Raw {type(annarg)} found in Annotated[] entry:'
                    f' {anntype}; this is probably not what you intended.'
                )
        anntype = annargs[0]
    return anntype, ioattrs


def _get_multitype_type(
    cls: type[IOMultiType], fieldpath: str, val: Any
) -> type[Any]:
    if not isinstance(val, dict):
        raise ValueError(
            f"Found a {type(val)} at '{fieldpath}'; expected a dict."
        )
    storename = cls.get_type_id_storage_name()
    id_val = val.get(storename)
    if id_val is None:
        raise ValueError(
            f"Expected a '{storename}'" f" value for object at '{fieldpath}'."
        )
    id_enum_type = cls.get_type_id_type()
    id_enum = id_enum_type(id_val)
    return cls.get_type_cached(id_enum)
