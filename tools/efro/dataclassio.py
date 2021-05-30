# Released under the MIT License. See LICENSE for details.
#
"""Functionality for importing, exporting, and validating dataclasses.

This allows complex nested dataclasses to be flattened to json-compatible
data and restored from said data. It also gracefully handles and preserves
unrecognized attribute data, allowing older clients to interact with newer
data formats in a nondestructive manner.
"""

# pylint: disable=too-many-lines

# Note: We do lots of comparing of exact types here which is normally
# frowned upon (stuff like isinstance() is usually encouraged).
# pylint: disable=unidiomatic-typecheck

from __future__ import annotations

import logging
from enum import Enum
import dataclasses
import typing
import datetime
from typing import TYPE_CHECKING, TypeVar, Generic
# Note: can pull this from typing once we update to Python 3.9+
# noinspection PyProtectedMember
from typing_extensions import get_args, get_type_hints, _AnnotatedAlias

from efro.util import enum_by_value

_pytz_utc: Any

# We don't *require* pytz but we want to support it for tzinfos if available.
try:
    import pytz
    _pytz_utc = pytz.utc
except ModuleNotFoundError:
    _pytz_utc = None  # pylint: disable=invalid-name

if TYPE_CHECKING:
    from typing import Any, Dict, Type, Tuple, Optional, List, Set

T = TypeVar('T')

# Types which we can pass through as-is.
SIMPLE_TYPES = {int, bool, str, float, type(None)}

# How deep we go when prepping nested types
# (basically for detecting recursive types)
MAX_RECURSION = 10

# Attr name for data we store on dataclass types as part of prep.
PREP_ATTR = '_DCIOPREP'

# Attr name for dict of extra attributes included on dataclass instances.
# Note that this is only added if extra attributes are present.
EXTRA_ATTRS_ATTR = '_DCIOEXATTRS'


class Codec(Enum):
    """Specifies expected data format exported to or imported from."""

    # Use only types that will translate cleanly to/from json: lists,
    # dicts with str keys, bools, ints, floats, and None.
    JSON = 'json'

    # Mostly like JSON but passes bytes and datetime objects through
    # as-is instead of converting them to json-friendly types.
    FIRESTORE = 'firestore'


class IOAttrs:
    """For specifying io behavior in annotations."""

    storagename: Optional[str] = None
    store_default: bool = True
    whole_days: bool = False
    whole_hours: bool = False

    def __init__(self,
                 storagename: Optional[str] = storagename,
                 store_default: bool = store_default,
                 whole_days: bool = whole_days,
                 whole_hours: bool = whole_hours):

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

    def validate_for_field(self, cls: Type, field: dataclasses.Field) -> None:
        """Ensure the IOAttrs instance is ok to use with the provided field."""

        # Turning off store_default requires the field to have either
        # a default_factory or a default
        if not self.store_default:
            default_factory: Any = field.default_factory  # type: ignore
            if (default_factory is dataclasses.MISSING
                    and field.default is dataclasses.MISSING):
                raise TypeError(f'Field {field.name} of {cls} has'
                                f' neither a default nor a default_factory;'
                                f' store_default=False cannot be set for it.')

    def validate_datetime(self, value: datetime.datetime,
                          fieldpath: str) -> None:
        """Ensure a datetime value meets our value requirements."""
        if self.whole_days:
            if any(x != 0 for x in (value.hour, value.minute, value.second,
                                    value.microsecond)):
                raise ValueError(
                    f'Value {value} at {fieldpath} is not a whole day.')
        if self.whole_hours:
            if any(x != 0
                   for x in (value.minute, value.second, value.microsecond)):
                raise ValueError(f'Value {value} at {fieldpath}'
                                 f' is not a whole hour.')


class FieldStoragePathCapture:
    """Utility for obtaining dataclass storage paths in a type safe way.

    Given dataclass instance foo, FieldStoragePathCapture(foo).bar.eep
    will return 'bar.eep' (or something like 'b.e' if storagenames are
    overridden). This can be combined with type-checking tricks that
    return foo in the type-checker's eyes while returning
    FieldStoragePathCapture(foo) at runtime in order to grant a measure
    of type safety to specifying field paths for things such as db
    queries. Be aware, however, that the type-checker will incorrectly
    think these lookups are returning actual attr values when they
    are actually returning strings.
    """

    def __init__(self, obj: Any, path: List[str] = None):
        if path is None:
            path = []
        if not dataclasses.is_dataclass(obj):
            raise TypeError(f'Expected a dataclass type/instance;'
                            f' got {type(obj)}.')
        self._cls = obj if isinstance(obj, type) else type(obj)
        self._path = path

    def __getattr__(self, name: str) -> Any:
        prep = PrepSession(explicit=False).prep_dataclass(self._cls,
                                                          recursion_level=0)
        try:
            anntype = prep.annotations[name]
        except KeyError as exc:
            raise AttributeError(f'{type(self)} has no {name} field.') from exc
        anntype, ioattrs = _parse_annotated(anntype)
        storagename = (name if (ioattrs is None or ioattrs.storagename is None)
                       else ioattrs.storagename)
        origin = _get_origin(anntype)
        path = self._path + [storagename]

        if dataclasses.is_dataclass(origin):
            return FieldStoragePathCapture(origin, path=path)
        return '.'.join(path)


def dataclass_to_dict(obj: Any,
                      codec: Codec = Codec.JSON,
                      coerce_to_float: bool = True) -> dict:
    """Given a dataclass object, return a json-friendly dict.

    All values will be checked to ensure they match the types specified
    on fields. Note that a limited set of types and data configurations is
    supported.

    Values with type Any will be checked to ensure they match types supported
    directly by json. This does not include types such as tuples which are
    implicitly translated by Python's json module (as this would break
    the ability to do a lossless round-trip with data).

    If coerce_to_float is True, integer values present on float typed fields
    will be converted to floats in the dict output. If False, a TypeError
    will be triggered.
    """

    out = _Outputter(obj,
                     create=True,
                     codec=codec,
                     coerce_to_float=coerce_to_float).run()
    assert isinstance(out, dict)
    return out


def dataclass_to_json(obj: Any, coerce_to_float: bool = True) -> str:
    """Utility function; return a json string from a dataclass instance.

    Basically json.dumps(dataclass_to_dict(...)).
    """
    import json
    return json.dumps(
        dataclass_to_dict(obj=obj,
                          coerce_to_float=coerce_to_float,
                          codec=Codec.JSON),
        separators=(',', ':'),
    )


def dataclass_from_dict(cls: Type[T],
                        values: dict,
                        codec: Codec = Codec.JSON,
                        coerce_to_float: bool = True,
                        allow_unknown_attrs: bool = True,
                        discard_unknown_attrs: bool = False) -> T:
    """Given a dict, return a dataclass of a given type.

    The dict must be formatted to match the specified codec (generally
    json-friendly object types). This means that sequence values such as
    tuples or sets should be passed as lists, enums should be passed as their
    associated values, nested dataclasses should be passed as dicts, etc.

    All values are checked to ensure their types/values are valid.

    Data for attributes of type Any will be checked to ensure they match
    types supported directly by json. This does not include types such
    as tuples which are implicitly translated by Python's json module
    (as this would break the ability to do a lossless round-trip with data).

    If coerce_to_float is True, int values passed for float typed fields
    will be converted to float values. Otherwise a TypeError is raised.

    If allow_unknown_attrs is False, AttributeErrors will be raised for
    attributes present in the dict but not on the data class. Otherwise they
    will be preserved as part of the instance and included if it is
    exported back to a dict, unless discard_unknown_attrs is True, in which
    case they will simply be discarded.
    """
    return _Inputter(cls,
                     codec=codec,
                     coerce_to_float=coerce_to_float,
                     allow_unknown_attrs=allow_unknown_attrs,
                     discard_unknown_attrs=discard_unknown_attrs).run(values)


def dataclass_from_json(cls: Type[T],
                        json_str: str,
                        coerce_to_float: bool = True,
                        allow_unknown_attrs: bool = True,
                        discard_unknown_attrs: bool = False) -> T:
    """Utility function; return a dataclass instance given a json string.

    Basically dataclass_from_dict(json.loads(...))
    """
    import json
    return dataclass_from_dict(cls=cls,
                               values=json.loads(json_str),
                               coerce_to_float=coerce_to_float,
                               allow_unknown_attrs=allow_unknown_attrs,
                               discard_unknown_attrs=discard_unknown_attrs)


def dataclass_validate(obj: Any,
                       coerce_to_float: bool = True,
                       codec: Codec = Codec.JSON) -> None:
    """Ensure that values in a dataclass instance are the correct types."""

    # Simply run an output pass but tell it not to generate data;
    # only run validation.
    _Outputter(obj, create=False, codec=codec,
               coerce_to_float=coerce_to_float).run()


def ioprep(cls: Type) -> None:
    """Prep a dataclass type for use with this module's functionality.

    Prepping ensures that all types contained in a data class as well as
    the usage of said types are supported by this module and pre-builds
    necessary constructs needed for encoding/decoding/etc.

    Prepping will happen on-the-fly as needed, but a warning will be
    emitted in such cases, as it is better to explicitly prep all used types
    early in a process to ensure any invalid types or configuration are caught
    immediately.

    Prepping a dataclass involves evaluating its type annotations, which,
    as of PEP 563, are stored simply as strings. This evaluation is done
    in the module namespace containing the class, so all referenced types
    must be defined at that level.
    """
    PrepSession(explicit=True).prep_dataclass(cls, recursion_level=0)


def ioprepped(cls: Type[T]) -> Type[T]:
    """Class decorator for easily prepping a dataclass at definition time.

    Note that in some cases it may not be possible to prep a dataclass
    immediately (such as when its type annotations refer to forward-declared
    types). In these cases, dataclass_prep() should be explicitly called for
    the class as soon as possible; ideally at module import time to expose any
    errors as early as possible in execution.
    """
    ioprep(cls)
    return cls


@dataclasses.dataclass
class PrepData:
    """Data we prepare and cache for a class during prep.

    This data is used as part of the encoding/decoding/validating process.
    """

    # Resolved annotation data with 'live' classes.
    annotations: Dict[str, Any]

    # Map of storage names to attr names.
    storage_names_to_attr_names: Dict[str, str]


class PrepSession:
    """Context for a prep."""

    def __init__(self, explicit: bool):
        self.explicit = explicit

    def prep_dataclass(self, cls: Type, recursion_level: int) -> PrepData:
        """Run prep on a dataclass if necessary and return its prep data."""

        # We should only need to do this once per dataclass.
        existing_data = getattr(cls, PREP_ATTR, None)
        if existing_data is not None:
            assert isinstance(existing_data, PrepData)
            return existing_data

        # If we run into classes containing themselves, we may have
        # to do something smarter to handle it.
        if recursion_level > MAX_RECURSION:
            raise RuntimeError('Max recursion exceeded.')

        # We should only be passed classes which are dataclasses.
        if not isinstance(cls, type) or not dataclasses.is_dataclass(cls):
            raise TypeError(f'Passed arg {cls} is not a dataclass type.')

        # Generate a warning on non-explicit preps; we prefer prep to
        # happen explicitly at runtime so errors can be detected early on.
        if not self.explicit:
            logging.warning(
                'efro.dataclassio: implicitly prepping dataclass: %s.'
                ' It is highly recommended to explicitly prep dataclasses'
                ' as soon as possible after definition (via'
                ' efro.dataclassio.ioprep() or the'
                ' @efro.dataclassio.ioprepped decorator).', cls)

        try:
            # NOTE: perhaps we want to expose the globalns/localns args
            # to this?
            # pylint: disable=unexpected-keyword-arg
            resolved_annotations = get_type_hints(cls, include_extras=True)
            # pylint: enable=unexpected-keyword-arg
        except Exception as exc:
            raise RuntimeError(
                f'dataclassio prep for {cls} failed with error: {exc}.'
                f' Make sure all types used in annotations are defined'
                f' at the module level or add them as part of an explicit'
                f' prep call.') from exc

        # noinspection PyDataclass
        fields = dataclasses.fields(cls)
        fields_by_name = {f.name: f for f in fields}

        all_storage_names: Set[str] = set()
        storage_names_to_attr_names: Dict[str, str] = {}

        # Ok; we've resolved actual types for this dataclass.
        # now recurse through them, verifying that we support all contained
        # types and prepping any contained dataclass types.
        for attrname, anntype in resolved_annotations.items():

            anntype, ioattrs = _parse_annotated(anntype)

            # If we found attached IOAttrs data, make sure it contains
            # valid values for the field it is attached to.
            if ioattrs is not None:
                ioattrs.validate_for_field(cls, fields_by_name[attrname])
                if ioattrs.storagename is not None:
                    storagename = ioattrs.storagename
                    storage_names_to_attr_names[ioattrs.storagename] = attrname
                else:
                    storagename = attrname
            else:
                storagename = attrname

            # Make sure we don't have any clashes in our storage names.
            if storagename in all_storage_names:
                raise TypeError(f'Multiple attrs on {cls} are using'
                                f' storage-name \'{storagename}\'')
            all_storage_names.add(storagename)

            self.prep_type(cls,
                           attrname,
                           anntype,
                           recursion_level=recursion_level + 1)

        # Success! Store our resolved stuff with the class and we're done.
        prepdata = PrepData(
            annotations=resolved_annotations,
            storage_names_to_attr_names=storage_names_to_attr_names)
        setattr(cls, PREP_ATTR, prepdata)
        return prepdata

    def prep_type(self, cls: Type, attrname: str, anntype: Any,
                  recursion_level: int) -> None:
        """Run prep on a dataclass."""
        # pylint: disable=too-many-return-statements
        # pylint: disable=too-many-branches

        # If we run into classes containing themselves, we may have
        # to do something smarter to handle it.
        if recursion_level > MAX_RECURSION:
            raise RuntimeError('Max recursion exceeded.')

        origin = _get_origin(anntype)

        if origin is typing.Union:
            self.prep_union(cls,
                            attrname,
                            anntype,
                            recursion_level=recursion_level + 1)
            return

        if anntype is typing.Any:
            return

        # Everything below this point assumes the annotation type resolves
        # to a concrete type.
        if not isinstance(origin, type):
            raise TypeError(
                f'Unsupported type found for \'{attrname}\' on {cls}:'
                f' {anntype}')

        if origin in SIMPLE_TYPES:
            return

        # For sets and lists, check out their single contained type (if any).
        if origin in (list, set):
            childtypes = typing.get_args(anntype)
            if len(childtypes) == 0:
                # This is equivalent to Any; nothing else needs checking.
                return
            if len(childtypes) > 1:
                raise TypeError(
                    f'Unrecognized typing arg count {len(childtypes)}'
                    f" for {anntype} attr '{attrname}' on {cls}")
            self.prep_type(cls,
                           attrname,
                           childtypes[0],
                           recursion_level=recursion_level + 1)
            return

        if origin is dict:
            childtypes = typing.get_args(anntype)
            assert len(childtypes) in (0, 2)

            # For key types we support Any, str, int,
            # and Enums with uniform str/int values.
            if not childtypes or childtypes[0] is typing.Any:
                # 'Any' needs no further checks (just checked per-instance).
                pass
            elif childtypes[0] in (str, int):
                # str and int are all good as keys.
                pass
            elif issubclass(childtypes[0], Enum):
                # Allow our usual str or int enum types as keys.
                self.prep_enum(childtypes[0])
            else:
                raise TypeError(
                    f'Dict key type {childtypes[0]} for \'{attrname}\''
                    f' on {cls.__name__} is not supported by dataclassio.')

            # For value types we support any of our normal types.
            if not childtypes or _get_origin(childtypes[1]) is typing.Any:
                # 'Any' needs no further checks (just checked per-instance).
                pass
            else:
                self.prep_type(cls,
                               attrname,
                               childtypes[1],
                               recursion_level=recursion_level + 1)
            return

        # For Tuples, simply check individual member types.
        # (and, for now, explicitly disallow zero member types or usage
        # of ellipsis)
        if origin is tuple:
            childtypes = typing.get_args(anntype)
            if not childtypes:
                raise TypeError(
                    f'Tuple at \'{attrname}\''
                    f' has no type args; dataclassio requires type args.')
            if childtypes[-1] is ...:
                raise TypeError(f'Found ellipsis as part of type for'
                                f' \'{attrname}\' on {cls.__name__};'
                                f' these are not'
                                f' supported by dataclassio.')
            for childtype in childtypes:
                self.prep_type(cls,
                               attrname,
                               childtype,
                               recursion_level=recursion_level + 1)
            return

        if issubclass(origin, Enum):
            self.prep_enum(origin)
            return

        # We allow datetime objects (and google's extended subclass of them
        # used in firestore, which is why we don't look for exact type here).
        if issubclass(origin, datetime.datetime):
            return

        if dataclasses.is_dataclass(origin):
            self.prep_dataclass(origin, recursion_level=recursion_level + 1)
            return

        if origin is bytes:
            return

        raise TypeError(f"Attr '{attrname}' on {cls.__name__} contains"
                        f" type '{anntype}'"
                        f' which is not supported by dataclassio.')

    def prep_union(self, cls: Type, attrname: str, anntype: Any,
                   recursion_level: int) -> None:
        """Run prep on a Union type."""
        typeargs = typing.get_args(anntype)
        if (len(typeargs) != 2
                or len([c for c in typeargs if c is type(None)]) != 1):
            raise TypeError(f'Union {anntype} for attr \'{attrname}\' on'
                            f' {cls.__name__} is not supported by dataclassio;'
                            f' only 2 member Unions with one type being None'
                            f' are supported.')
        for childtype in typeargs:
            self.prep_type(cls,
                           attrname,
                           childtype,
                           recursion_level=recursion_level + 1)

    def prep_enum(self, enumtype: Type[Enum]) -> None:
        """Run prep on an enum type."""

        valtype: Any = None

        # We currently support enums with str or int values; fail if we
        # find any others.
        for enumval in enumtype:
            if not isinstance(enumval.value, (str, int)):
                raise TypeError(f'Enum value {enumval} has value type'
                                f' {type(enumval.value)}; only str and int is'
                                f' supported by dataclassio.')
            if valtype is None:
                valtype = type(enumval.value)
            else:
                if type(enumval.value) is not valtype:
                    raise TypeError(f'Enum type {enumtype} has multiple'
                                    f' value types; dataclassio requires'
                                    f' them to be uniform.')


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
            type(k) is str and _is_valid_for_codec(v, codec)
            for k, v in obj.items())
    if objtype is list:
        return all(_is_valid_for_codec(elem, codec) for elem in obj)

    # A few things are valid in firestore but not json.
    if issubclass(objtype, datetime.datetime) or objtype is bytes:
        return codec is Codec.FIRESTORE

    return False


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


def _get_origin(anntype: Any) -> Any:
    """Given a type annotation, return its origin or itself if there is none.

    This differs from typing.get_origin in that it will never return None.
    This lets us use the same code path for handling typing.List
    that we do for handling list, which is good since they can be used
    interchangeably in annotations.
    """
    origin = typing.get_origin(anntype)
    return anntype if origin is None else origin


class _Outputter:
    """Validates or exports data contained in a dataclass instance."""

    def __init__(self, obj: Any, create: bool, codec: Codec,
                 coerce_to_float: bool) -> None:
        self._obj = obj
        self._create = create
        self._codec = codec
        self._coerce_to_float = coerce_to_float

    def run(self) -> Any:
        """Do the thing."""
        return self._process_dataclass(type(self._obj), self._obj, '')

    def _process_dataclass(self, cls: Type, obj: Any, fieldpath: str) -> Any:
        # pylint: disable=too-many-locals
        # pylint: disable=too-many-branches
        prep = PrepSession(explicit=False).prep_dataclass(type(obj),
                                                          recursion_level=0)
        fields = dataclasses.fields(obj)
        out: Optional[Dict[str, Any]] = {} if self._create else None
        for field in fields:
            fieldname = field.name
            if fieldpath:
                subfieldpath = f'{fieldpath}.{fieldname}'
            else:
                subfieldpath = fieldname
            anntype = prep.annotations[fieldname]
            value = getattr(obj, fieldname)

            anntype, ioattrs = _parse_annotated(anntype)

            # If we're not storing default values for this fella,
            # we can skip all output processing if we've got a default value.
            if ioattrs is not None and not ioattrs.store_default:
                default_factory: Any = field.default_factory  # type: ignore
                if default_factory is not dataclasses.MISSING:
                    if default_factory() == value:
                        continue
                elif field.default is not dataclasses.MISSING:
                    if field.default == value:
                        continue
                else:
                    raise RuntimeError(
                        f'Field {fieldname} of {cls.__name__} has'
                        f' neither a default nor a default_factory;'
                        f' store_default=False cannot be set for it.'
                        f' (AND THIS SHOULD HAVE BEEN CAUGHT IN PREP!)')

            outvalue = self._process_value(cls, subfieldpath, anntype, value,
                                           ioattrs)
            if self._create:
                assert out is not None
                storagename = (fieldname if
                               (ioattrs is None or ioattrs.storagename is None)
                               else ioattrs.storagename)
                out[storagename] = outvalue

        # If there's extra-attrs stored on us, check/include them.
        extra_attrs = getattr(obj, EXTRA_ATTRS_ATTR, None)
        if isinstance(extra_attrs, dict):
            if not _is_valid_for_codec(extra_attrs, self._codec):
                raise TypeError(
                    f'Extra attrs on {fieldpath} contains data type(s)'
                    f' not supported by json.')
            if self._create:
                assert out is not None
                out.update(extra_attrs)
        return out

    def _process_value(self, cls: Type, fieldpath: str, anntype: Any,
                       value: Any, ioattrs: Optional[IOAttrs]) -> Any:
        # pylint: disable=too-many-return-statements
        # pylint: disable=too-many-branches
        # pylint: disable=too-many-statements

        origin = _get_origin(anntype)

        if origin is typing.Any:
            if not _is_valid_for_codec(value, self._codec):
                raise TypeError(
                    f'Invalid value type for \'{fieldpath}\';'
                    f" 'Any' typed values must contain types directly"
                    f' supported by the specified codec ({self._codec.name});'
                    f' found \'{type(value).__name__}\' which is not.')
            return value if self._create else None

        if origin is typing.Union:
            # Currently the only unions we support are None/Value
            # (translated from Optional), which we verified on prep.
            # So let's treat this as a simple optional case.
            if value is None:
                return None
            childanntypes_l = [
                c for c in typing.get_args(anntype) if c is not type(None)
            ]
            assert len(childanntypes_l) == 1
            return self._process_value(cls, fieldpath, childanntypes_l[0],
                                       value, ioattrs)

        # Everything below this point assumes the annotation type resolves
        # to a concrete type. (This should have been verified at prep time).
        assert isinstance(origin, type)

        # For simple flat types, look for exact matches:
        if origin in SIMPLE_TYPES:
            if type(value) is not origin:
                # Special case: if they want to coerce ints to floats, do so.
                if (self._coerce_to_float and origin is float
                        and type(value) is int):
                    return float(value) if self._create else None
                _raise_type_error(fieldpath, type(value), (origin, ))
            return value if self._create else None

        if origin is tuple:
            if not isinstance(value, tuple):
                raise TypeError(f'Expected a tuple for {fieldpath};'
                                f' found a {type(value)}')
            childanntypes = typing.get_args(anntype)

            # We should have verified this was non-zero at prep-time
            assert childanntypes
            if len(value) != len(childanntypes):
                raise TypeError(f'Tuple at {fieldpath} contains'
                                f' {len(value)} values; type specifies'
                                f' {len(childanntypes)}.')
            if self._create:
                return [
                    self._process_value(cls, fieldpath, childanntypes[i], x,
                                        ioattrs) for i, x in enumerate(value)
                ]
            for i, x in enumerate(value):
                self._process_value(cls, fieldpath, childanntypes[i], x,
                                    ioattrs)
            return None

        if origin is list:
            if not isinstance(value, list):
                raise TypeError(f'Expected a list for {fieldpath};'
                                f' found a {type(value)}')
            childanntypes = typing.get_args(anntype)

            # 'Any' type children; make sure they are valid values for
            # the specified codec.
            if len(childanntypes) == 0 or childanntypes[0] is typing.Any:
                for i, child in enumerate(value):
                    if not _is_valid_for_codec(child, self._codec):
                        raise TypeError(
                            f'Item {i} of {fieldpath} contains'
                            f' data type(s) not supported by the specified'
                            f' codec ({self._codec.name}).')
                # Hmm; should we do a copy here?
                return value if self._create else None

            # We contain elements of some specified type.
            assert len(childanntypes) == 1
            if self._create:
                return [
                    self._process_value(cls, fieldpath, childanntypes[0], x,
                                        ioattrs) for x in value
                ]
            for x in value:
                self._process_value(cls, fieldpath, childanntypes[0], x,
                                    ioattrs)
            return None

        if origin is set:
            if not isinstance(value, set):
                raise TypeError(f'Expected a set for {fieldpath};'
                                f' found a {type(value)}')
            childanntypes = typing.get_args(anntype)

            # 'Any' type children; make sure they are valid Any values.
            if len(childanntypes) == 0 or childanntypes[0] is typing.Any:
                for child in value:
                    if not _is_valid_for_codec(child, self._codec):
                        raise TypeError(
                            f'Set at {fieldpath} contains'
                            f' data type(s) not supported by the'
                            f' specified codec ({self._codec.name}).')
                return list(value) if self._create else None

            # We contain elements of some specified type.
            assert len(childanntypes) == 1
            if self._create:
                # Note: we output json-friendly values so this becomes
                # a list.
                return [
                    self._process_value(cls, fieldpath, childanntypes[0], x,
                                        ioattrs) for x in value
                ]
            for x in value:
                self._process_value(cls, fieldpath, childanntypes[0], x,
                                    ioattrs)
            return None

        if origin is dict:
            return self._process_dict(cls, fieldpath, anntype, value, ioattrs)

        if dataclasses.is_dataclass(origin):
            if not isinstance(value, origin):
                raise TypeError(f'Expected a {origin} for {fieldpath};'
                                f' found a {type(value)}.')
            return self._process_dataclass(cls, value, fieldpath)

        if issubclass(origin, Enum):
            if not isinstance(value, origin):
                raise TypeError(f'Expected a {origin} for {fieldpath};'
                                f' found a {type(value)}.')
            # At prep-time we verified that these enums had valid value
            # types, so we can blindly return it here.
            return value.value if self._create else None

        if issubclass(origin, datetime.datetime):
            if not isinstance(value, origin):
                raise TypeError(f'Expected a {origin} for {fieldpath};'
                                f' found a {type(value)}.')
            _ensure_datetime_is_timezone_aware(value)
            if ioattrs is not None:
                ioattrs.validate_datetime(value, fieldpath)
            if self._codec is Codec.FIRESTORE:
                return value
            assert self._codec is Codec.JSON
            return [
                value.year, value.month, value.day, value.hour, value.minute,
                value.second, value.microsecond
            ] if self._create else None

        if origin is bytes:
            return self._process_bytes(cls, fieldpath, value)

        raise TypeError(
            f"Field '{fieldpath}' of type '{anntype}' is unsupported here.")

    def _process_bytes(self, cls: Type, fieldpath: str, value: bytes) -> Any:
        import base64
        if not isinstance(value, bytes):
            raise TypeError(
                f'Expected bytes for {fieldpath} on {cls.__name__};'
                f' found a {type(value)}.')

        if not self._create:
            return None

        # In JSON we convert to base64, but firestore directly supports bytes.
        if self._codec is Codec.JSON:
            return base64.b64encode(value).decode()

        assert self._codec is Codec.FIRESTORE
        return value

    def _process_dict(self, cls: Type, fieldpath: str, anntype: Any,
                      value: dict, ioattrs: Optional[IOAttrs]) -> Any:
        # pylint: disable=too-many-branches
        if not isinstance(value, dict):
            raise TypeError(f'Expected a dict for {fieldpath};'
                            f' found a {type(value)}.')
        childtypes = typing.get_args(anntype)
        assert len(childtypes) in (0, 2)

        # We treat 'Any' dicts simply as json; we don't do any translating.
        if not childtypes or childtypes[0] is typing.Any:
            if not isinstance(value, dict) or not _is_valid_for_codec(
                    value, self._codec):
                raise TypeError(
                    f'Invalid value for Dict[Any, Any]'
                    f' at \'{fieldpath}\' on {cls.__name__};'
                    f' all keys and values must be directly compatible'
                    f' with the specified codec ({self._codec.name})'
                    f' when dict type is Any.')
            return value if self._create else None

        # Ok; we've got a definite key type (which we verified as valid
        # during prep). Make sure all keys match it.
        out: Optional[Dict] = {} if self._create else None
        keyanntype, valanntype = childtypes

        # str keys we just export directly since that's supported by json.
        if keyanntype is str:
            for key, val in value.items():
                if not isinstance(key, str):
                    raise TypeError(
                        f'Got invalid key type {type(key)} for'
                        f' dict key at \'{fieldpath}\' on {cls.__name__};'
                        f' expected {keyanntype}.')
                outval = self._process_value(cls, fieldpath, valanntype, val,
                                             ioattrs)
                if self._create:
                    assert out is not None
                    out[key] = outval

        # int keys are stored as str versions of themselves.
        elif keyanntype is int:
            for key, val in value.items():
                if not isinstance(key, int):
                    raise TypeError(
                        f'Got invalid key type {type(key)} for'
                        f' dict key at \'{fieldpath}\' on {cls.__name__};'
                        f' expected an int.')
                outval = self._process_value(cls, fieldpath, valanntype, val,
                                             ioattrs)
                if self._create:
                    assert out is not None
                    out[str(key)] = outval

        elif issubclass(keyanntype, Enum):
            for key, val in value.items():
                if not isinstance(key, keyanntype):
                    raise TypeError(
                        f'Got invalid key type {type(key)} for'
                        f' dict key at \'{fieldpath}\' on {cls.__name__};'
                        f' expected a {keyanntype}.')
                outval = self._process_value(cls, fieldpath, valanntype, val,
                                             ioattrs)
                if self._create:
                    assert out is not None
                    out[str(key.value)] = outval
        else:
            raise RuntimeError(f'Unhandled dict out-key-type {keyanntype}')

        return out


class _Inputter(Generic[T]):

    def __init__(self,
                 cls: Type[T],
                 codec: Codec,
                 coerce_to_float: bool,
                 allow_unknown_attrs: bool = True,
                 discard_unknown_attrs: bool = False):
        self._cls = cls
        self._codec = codec
        self._coerce_to_float = coerce_to_float
        self._allow_unknown_attrs = allow_unknown_attrs
        self._discard_unknown_attrs = discard_unknown_attrs

        if not allow_unknown_attrs and discard_unknown_attrs:
            raise ValueError('discard_unknown_attrs cannot be True'
                             ' when allow_unknown_attrs is False.')

    def run(self, values: dict) -> T:
        """Do the thing."""
        out = self._dataclass_from_input(self._cls, '', values)
        assert isinstance(out, self._cls)
        return out

    def _value_from_input(self, cls: Type, fieldpath: str, anntype: Any,
                          value: Any, ioattrs: Optional[IOAttrs]) -> Any:
        """Convert an assigned value to what a dataclass field expects."""
        # pylint: disable=too-many-return-statements
        # pylint: disable=too-many-branches

        origin = _get_origin(anntype)

        if origin is typing.Any:
            if not _is_valid_for_codec(value, self._codec):
                raise TypeError(f'Invalid value type for \'{fieldpath}\';'
                                f' \'Any\' typed values must contain only'
                                f' types directly supported by the specified'
                                f' codec ({self._codec.name}); found'
                                f' \'{type(value).__name__}\' which is not.')
            return value

        if origin is typing.Union:
            # Currently the only unions we support are None/Value
            # (translated from Optional), which we verified on prep.
            # So let's treat this as a simple optional case.
            if value is None:
                return None
            childanntypes_l = [
                c for c in typing.get_args(anntype) if c is not type(None)
            ]
            assert len(childanntypes_l) == 1
            return self._value_from_input(cls, fieldpath, childanntypes_l[0],
                                          value, ioattrs)

        # Everything below this point assumes the annotation type resolves
        # to a concrete type. (This should have been verified at prep time).
        assert isinstance(origin, type)

        if origin in SIMPLE_TYPES:
            if type(value) is not origin:
                # Special case: if they want to coerce ints to floats, do so.
                if (self._coerce_to_float and origin is float
                        and type(value) is int):
                    return float(value)
                _raise_type_error(fieldpath, type(value), (origin, ))
            return value

        if origin in {list, set}:
            return self._sequence_from_input(cls, fieldpath, anntype, value,
                                             origin, ioattrs)

        if origin is tuple:
            return self._tuple_from_input(cls, fieldpath, anntype, value,
                                          ioattrs)

        if origin is dict:
            return self._dict_from_input(cls, fieldpath, anntype, value,
                                         ioattrs)

        if dataclasses.is_dataclass(origin):
            return self._dataclass_from_input(origin, fieldpath, value)

        if issubclass(origin, Enum):
            return enum_by_value(origin, value)

        if issubclass(origin, datetime.datetime):
            return self._datetime_from_input(cls, fieldpath, value, ioattrs)

        if origin is bytes:
            return self._bytes_from_input(origin, fieldpath, value)

        raise TypeError(
            f"Field '{fieldpath}' of type '{anntype}' is unsupported here.")

    def _bytes_from_input(self, cls: Type, fieldpath: str,
                          value: Any) -> bytes:
        """Given input data, returns bytes."""
        import base64

        # For firestore, bytes are passed as-is. Otherwise they're encoded
        # as base64.
        if self._codec is Codec.FIRESTORE:
            if not isinstance(value, bytes):
                raise TypeError(f'Expected a bytes object for {fieldpath}'
                                f' on {cls.__name__}; got a {type(value)}.')

            return value

        assert self._codec is Codec.JSON
        if not isinstance(value, str):
            raise TypeError(f'Expected a string object for {fieldpath}'
                            f' on {cls.__name__}; got a {type(value)}.')
        return base64.b64decode(value)

    def _dataclass_from_input(self, cls: Type, fieldpath: str,
                              values: dict) -> Any:
        """Given a dict, instantiates a dataclass of the given type.

        The dict must be in the json-friendly format as emitted from
        dataclass_to_dict. This means that sequence values such as tuples or
        sets should be passed as lists, enums should be passed as their
        associated values, and nested dataclasses should be passed as dicts.
        """
        # pylint: disable=too-many-locals
        if not isinstance(values, dict):
            raise TypeError(
                f'Expected a dict for {fieldpath} on {cls.__name__};'
                f' got a {type(values)}.')

        prep = PrepSession(explicit=False).prep_dataclass(cls,
                                                          recursion_level=0)

        extra_attrs = {}

        # noinspection PyDataclass
        fields = dataclasses.fields(cls)
        fields_by_name = {f.name: f for f in fields}
        args: Dict[str, Any] = {}
        for rawkey, value in values.items():
            key = prep.storage_names_to_attr_names.get(rawkey, rawkey)
            field = fields_by_name.get(key)

            # Store unknown attrs off to the side (or error if desired).
            if field is None:
                if self._allow_unknown_attrs:
                    if self._discard_unknown_attrs:
                        continue

                    # Treat this like 'Any' data; ensure that it is valid
                    # raw json.
                    if not _is_valid_for_codec(value, self._codec):
                        raise TypeError(
                            f'Unknown attr \'{key}\''
                            f' on {fieldpath} contains data type(s)'
                            f' not supported by the specified codec'
                            f' ({self._codec.name}).')
                    extra_attrs[key] = value
                else:
                    raise AttributeError(
                        f"'{cls.__name__}' has no '{key}' field.")
            else:
                fieldname = field.name
                anntype = prep.annotations[fieldname]
                anntype, ioattrs = _parse_annotated(anntype)

                subfieldpath = (f'{fieldpath}.{fieldname}'
                                if fieldpath else fieldname)
                args[key] = self._value_from_input(cls, subfieldpath, anntype,
                                                   value, ioattrs)
        try:
            out = cls(**args)
        except Exception as exc:
            raise RuntimeError(f'Error instantiating class {cls.__name__}'
                               f' at {fieldpath}: {exc}') from exc
        if extra_attrs:
            setattr(out, EXTRA_ATTRS_ATTR, extra_attrs)
        return out

    def _dict_from_input(self, cls: Type, fieldpath: str, anntype: Any,
                         value: Any, ioattrs: Optional[IOAttrs]) -> Any:
        # pylint: disable=too-many-branches
        # pylint: disable=too-many-locals

        if not isinstance(value, dict):
            raise TypeError(
                f'Expected a dict for \'{fieldpath}\' on {cls.__name__};'
                f' got a {type(value)}.')

        childtypes = typing.get_args(anntype)
        assert len(childtypes) in (0, 2)

        out: Dict

        # We treat 'Any' dicts simply as json; we don't do any translating.
        if not childtypes or childtypes[0] is typing.Any:
            if not isinstance(value, dict) or not _is_valid_for_codec(
                    value, self._codec):
                raise TypeError(f'Got invalid value for Dict[Any, Any]'
                                f' at \'{fieldpath}\' on {cls.__name__};'
                                f' all keys and values must be'
                                f' compatible with the specified codec'
                                f' ({self._codec.name}).')
            out = value
        else:
            out = {}
            keyanntype, valanntype = childtypes

            # Ok; we've got definite key/value types (which we verified as
            # valid during prep). Run all keys/values through it.

            # str keys we just take directly since that's supported by json.
            if keyanntype is str:
                for key, val in value.items():
                    if not isinstance(key, str):
                        raise TypeError(
                            f'Got invalid key type {type(key)} for'
                            f' dict key at \'{fieldpath}\' on {cls.__name__};'
                            f' expected a str.')
                    out[key] = self._value_from_input(cls, fieldpath,
                                                      valanntype, val, ioattrs)

            # int keys are stored in json as str versions of themselves.
            elif keyanntype is int:
                for key, val in value.items():
                    if not isinstance(key, str):
                        raise TypeError(
                            f'Got invalid key type {type(key)} for'
                            f' dict key at \'{fieldpath}\' on {cls.__name__};'
                            f' expected a str.')
                    try:
                        keyint = int(key)
                    except ValueError as exc:
                        raise TypeError(
                            f'Got invalid key value {key} for'
                            f' dict key at \'{fieldpath}\' on {cls.__name__};'
                            f' expected an int in string form.') from exc
                    out[keyint] = self._value_from_input(
                        cls, fieldpath, valanntype, val, ioattrs)

            elif issubclass(keyanntype, Enum):
                # In prep we verified that all these enums' values have
                # the same type, so we can just look at the first to see if
                # this is a string enum or an int enum.
                enumvaltype = type(next(iter(keyanntype)).value)
                assert enumvaltype in (int, str)
                if enumvaltype is str:
                    for key, val in value.items():
                        try:
                            enumval = enum_by_value(keyanntype, key)
                        except ValueError as exc:
                            raise ValueError(
                                f'Got invalid key value {key} for'
                                f' dict key at \'{fieldpath}\''
                                f' on {cls.__name__};'
                                f' expected a value corresponding to'
                                f' a {keyanntype}.') from exc
                        out[enumval] = self._value_from_input(
                            cls, fieldpath, valanntype, val, ioattrs)
                else:
                    for key, val in value.items():
                        try:
                            enumval = enum_by_value(keyanntype, int(key))
                        except (ValueError, TypeError) as exc:
                            raise ValueError(
                                f'Got invalid key value {key} for'
                                f' dict key at \'{fieldpath}\''
                                f' on {cls.__name__};'
                                f' expected {keyanntype} value (though'
                                f' in string form).') from exc
                        out[enumval] = self._value_from_input(
                            cls, fieldpath, valanntype, val, ioattrs)

            else:
                raise RuntimeError(f'Unhandled dict in-key-type {keyanntype}')

        return out

    def _sequence_from_input(self, cls: Type, fieldpath: str, anntype: Any,
                             value: Any, seqtype: Type,
                             ioattrs: Optional[IOAttrs]) -> Any:

        # Because we are json-centric, we expect a list for all sequences.
        if type(value) is not list:
            raise TypeError(f'Invalid input value for "{fieldpath}";'
                            f' expected a list, got a {type(value).__name__}')

        childanntypes = typing.get_args(anntype)

        # 'Any' type children; make sure they are valid json values
        # and then just grab them.
        if len(childanntypes) == 0 or childanntypes[0] is typing.Any:
            for i, child in enumerate(value):
                if not _is_valid_for_codec(child, self._codec):
                    raise TypeError(f'Item {i} of {fieldpath} contains'
                                    f' data type(s) not supported by json.')
            return value if type(value) is seqtype else seqtype(value)

        # We contain elements of some specified type.
        assert len(childanntypes) == 1
        childanntype = childanntypes[0]
        return seqtype(
            self._value_from_input(cls, fieldpath, childanntype, i, ioattrs)
            for i in value)

    def _datetime_from_input(self, cls: Type, fieldpath: str, value: Any,
                             ioattrs: Optional[IOAttrs]) -> Any:

        # For firestore we expect a datetime object.
        if self._codec is Codec.FIRESTORE:
            # Don't compare exact type here, as firestore can give us
            # a subclass with extended precision.
            if not isinstance(value, datetime.datetime):
                raise TypeError(
                    f'Invalid input value for "{fieldpath}" on'
                    f' "{cls.__name__}";'
                    f' expected a datetime, got a {type(value).__name__}')
            _ensure_datetime_is_timezone_aware(value)
            return value

        assert self._codec is Codec.JSON

        # We expect a list of 7 ints.
        if type(value) is not list:
            raise TypeError(
                f'Invalid input value for "{fieldpath}" on "{cls.__name__}";'
                f' expected a list, got a {type(value).__name__}')
        if len(value) != 7 or not all(isinstance(x, int) for x in value):
            raise TypeError(
                f'Invalid input value for "{fieldpath}" on "{cls.__name__}";'
                f' expected a list of 7 ints.')
        out = datetime.datetime(  # type: ignore
            *value, tzinfo=datetime.timezone.utc)
        if ioattrs is not None:
            ioattrs.validate_datetime(out, fieldpath)
        return out

    def _tuple_from_input(self, cls: Type, fieldpath: str, anntype: Any,
                          value: Any, ioattrs: Optional[IOAttrs]) -> Any:

        out: List = []

        # Because we are json-centric, we expect a list for all sequences.
        if type(value) is not list:
            raise TypeError(f'Invalid input value for "{fieldpath}";'
                            f' expected a list, got a {type(value).__name__}')

        childanntypes = typing.get_args(anntype)

        # We should have verified this to be non-zero at prep-time.
        assert childanntypes

        if len(value) != len(childanntypes):
            raise TypeError(f'Invalid tuple input for "{fieldpath}";'
                            f' expected {len(childanntypes)} values,'
                            f' found {len(value)}.')

        for i, childanntype in enumerate(childanntypes):
            childval = value[i]

            # 'Any' type children; make sure they are valid json values
            # and then just grab them.
            if childanntype is typing.Any:
                if not _is_valid_for_codec(childval, self._codec):
                    raise TypeError(f'Item {i} of {fieldpath} contains'
                                    f' data type(s) not supported by json.')
                out.append(childval)
            else:
                out.append(
                    self._value_from_input(cls, fieldpath, childanntype,
                                           childval, ioattrs))

        assert len(out) == len(childanntypes)
        return tuple(out)


def _ensure_datetime_is_timezone_aware(value: datetime.datetime) -> None:
    # We only support timezone-aware utc times.
    if (value.tzinfo is not datetime.timezone.utc
            and (_pytz_utc is None or value.tzinfo is not _pytz_utc)):
        raise ValueError(
            'datetime values must have timezone set as timezone.utc')


def _parse_annotated(anntype: Any) -> Tuple[Any, Optional[IOAttrs]]:
    """Parse Annotated() constructs, returning annotated type & IOAttrs."""
    # If we get an Annotated[foo, bar, eep] we take
    # foo as the actual type and we look for IOAttrs instances in
    # bar/eep to affect our behavior.
    ioattrs: Optional[IOAttrs] = None
    if isinstance(anntype, _AnnotatedAlias):
        annargs = get_args(anntype)
        for annarg in annargs[1:]:
            if isinstance(annarg, IOAttrs):
                if ioattrs is not None:
                    raise RuntimeError(
                        'Multiple IOAttrs instances found for a'
                        ' single annotation; this is not supported.')
                ioattrs = annarg

            # I occasionally just throw a 'x' down when I mean IOAttrs('x');
            # catch these mistakes.
            elif isinstance(annarg, (str, int, float, bool)):
                raise RuntimeError(
                    f'Raw {type(annarg)} found in Annotated[] entry:'
                    f' {anntype}; this is probably not what you intended.')
        anntype = annargs[0]
    return anntype, ioattrs
